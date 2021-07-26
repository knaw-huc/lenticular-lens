import io
import csv
import itertools

from datetime import datetime
from collections import OrderedDict

from rdflib import Literal, URIRef, XSD, Graph
from rdflib.namespace import NamespaceManager
from anytree import Node, RenderTree, DoubleStyle, PostOrderIter

from ll.job.validation import Validation

from ll.namespaces.void_plus import VoidPlus
from ll.namespaces.shared_ontologies import Namespaces as NS

from ll.util.hasher import hash_string_min
from ll.util.stopwords import get_stopwords, get_iso_639_1_code
from ll.util.n3_helpers import TAB, pred_val, multiple_val, blank_node
from ll.util.helpers import flatten, get_json_from_file, get_publisher, get_from_buffer


class CsvExport:
    def __init__(self, job, type, id):
        self._job = job
        self._type = type
        self._id = id

    def create_generator(self, validation_filter=Validation.ALL):
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(['Source URI', 'Target URI', 'Strength', 'Valid', 'Cluster ID', 'Motivation'])

        i = 0
        for link in self._job.get_links(self._id, self._type, validation_filter=validation_filter):
            similarity = round(link['similarity'], 5) if link['similarity'] else 1
            cluster_id = link['cluster_id'] if link['cluster_id'] else ''
            motivation = link['motivation'] if link['motivation'] else ''

            source_uri = link['source'] if link['link_order'] != 'target_source' else link['target']
            target_uri = link['target'] if link['link_order'] != 'target_source' else link['source']

            writer.writerow([source_uri, target_uri, similarity, link['valid'], cluster_id, motivation])

            i += 1
            if i > 1000:
                i = 0
                yield get_from_buffer(buffer)

        yield buffer.getvalue()


class RdfExport:
    _logic_ops_info = get_json_from_file('logic_ops.json')
    _matching_methods_info = get_json_from_file('matching_methods.json')
    _lens_operators_info = get_json_from_file('lens_operators.json')
    _validation_states_info = get_json_from_file('validation_states.json')

    _predefined_metadata_prefix_mappings = {
        NS.RDF.prefix: str(NS.RDF.rdf),
        NS.RDFS.prefix: str(NS.RDFS.rdfs),
        NS.VoID.prefix: str(NS.VoID.void),
        NS.DCterms.prefix: str(NS.DCterms.dcterms),
        NS.Formats.prefix: str(NS.Formats.formats),
        NS.CC.prefix: str(NS.CC.cc),
        NS.XSD.prefix: str(NS.XSD.xsd),
        VoidPlus.ontology_prefix: VoidPlus.ontology,
        VoidPlus.resource_prefix: VoidPlus.resource,
        VoidPlus.linkset_prefix: VoidPlus.linkset
    }
    _predefined_export_only_prefix_mappings = {
        NS.RDF.prefix: str(NS.RDF.rdf),
        VoidPlus.ontology_prefix_ttl: VoidPlus.ontology
    }
    _predefined_export_only_reification_prefix_mappigs = {
        NS.XSD.prefix: str(NS.XSD.xsd),
        VoidPlus.resource_prefix: VoidPlus.resource
    }

    def __init__(self, job, type, id):
        self._job = job
        self._type = type
        self._id = id

        self._spec = self._job.get_spec_by_id(self._id, self._type)
        self._linkset_specs = {self._spec} if self._type == 'linkset' else {linkset for linkset in self._spec.linksets}

        self._entity_type_selections = self._spec.all_entity_type_selections
        self._matching_methods = self._spec.matching_methods

        self._filter_props = {property for ets in self._entity_type_selections for property in ets.filter_properties}

        self._matching_methods_source_props = {(ets, prop)
                                               for matching_method in self._matching_methods
                                               for ets, props_ets in matching_method.sources.items()
                                               for prop in props_ets}

        self._matching_methods_target_props = {(ets, prop)
                                               for matching_method in self._matching_methods
                                               for ets, props_ets in matching_method.targets.items()
                                               for prop in props_ets}

        self._matching_methods_intermediate_source_props = \
            {(ets, prop)
             for matching_method in self._matching_methods
             for ets, props_ets in matching_method.intermediates.items()
             for prop in props_ets['source']
             if matching_method.is_intermediate}

        self._matching_methods_intermediate_target_props = \
            {(ets, prop)
             for matching_method in self._matching_methods
             for ets, props_ets in matching_method.intermediates.items()
             for prop in props_ets['target']
             if matching_method.is_intermediate}

        self._matching_methods_props = self._matching_methods_source_props \
            .union(self._matching_methods_target_props) \
            .union(self._matching_methods_intermediate_source_props) \
            .union(self._matching_methods_intermediate_target_props)

        self._all_props = self._filter_props.union({prop.prop_original for ets, prop in self._matching_methods_props})

        self._all_transformers = flatten(
            [mm.transformers('sources') + mm.transformers('targets') for mm in self._matching_methods] +
            [prop.property_transformers for ets_id, prop in self._matching_methods_props])

    def create_generator(self, link_pred_namespace, link_pred_shortname,
                         export_linkset=True, export_metadata=True, export_validation_set=True, export_cluster_set=True,
                         reification='none', creator=None, validation_filter=Validation.ALL):
        link_pred = link_pred_shortname.split(':')
        prefix_mappings = self._determine_prefix_mappings(
            link_pred[0], link_pred_namespace, export_linkset, export_metadata,
            export_validation_set, export_cluster_set, reification != 'none')

        ns_manager = NamespaceManager(Graph())
        for prefix, uri in prefix_mappings.items():
            ns_manager.bind(prefix, uri)

        generators = [self._namespaces_metadata_generator(prefix_mappings)]

        if export_metadata:
            generators.append(self._metadata_export_generator(ns_manager, link_pred_shortname, creator))

        if export_linkset:
            links_iter = self._job.get_links(self._id, self._type, validation_filter=validation_filter)
            generators.append(self._linkset_export_generator(
                links_iter, link_pred_namespace + link_pred[1], ns_manager, reification,
                (not export_metadata and not export_validation_set and not export_cluster_set)))

        if export_validation_set:
            links_iter = self._job.get_links(self._id, self._type, validation_filter=validation_filter)
            generators.append(self._validations_export_generator(links_iter, ns_manager))

        if export_cluster_set:
            clusters_iter = self._job.get_clusters(self._id, self._type,
                                                   validation_filter=validation_filter, include_nodes=True)
            generators.append(self._clusters_export_generator(clusters_iter, ns_manager))

        return itertools.chain(*generators)

    def _get_predefined_prefix_mappings(self, export_metadata):
        return self._predefined_metadata_prefix_mappings.copy() \
            if export_metadata else self._predefined_export_only_prefix_mappings.copy()

    def _determine_prefix_mappings(self, link_pred_prefix, link_pred_uri, export_linkset, export_metadata,
                                   export_validation_set, export_cluster_set, export_link_metadata):
        predefined_prefix_mappings = self._get_predefined_prefix_mappings(export_metadata)

        if export_metadata:
            for property in self._all_props:
                predefined_prefix_mappings = {**predefined_prefix_mappings, **property.prefix_mappings}

            method_info_and_configs = [[mm.method_info, mm.method_config] for mm in self._matching_methods] + \
                                      [[mm.method_sim_info, mm.method_sim_config] for mm in self._matching_methods]
            for [method_info, method_config] in method_info_and_configs:
                for prop_key in method_info.get('items', {}).keys():
                    predicate_rdf_info = method_info['items'][prop_key].get('rdf')
                    if predicate_rdf_info:
                        predefined_prefix_mappings[predicate_rdf_info['prefix']] = predicate_rdf_info['uri']
                        if method_config[prop_key] in predicate_rdf_info.get('values', {}):
                            for value_rdf_info in predicate_rdf_info['values'][method_config[prop_key]]:
                                predefined_prefix_mappings[value_rdf_info['prefix']] = value_rdf_info['uri']

            for transformer in self._all_transformers:
                if transformer['name'] == 'STOPWORDS':
                    if NS.DC.prefix not in predefined_prefix_mappings:
                        predefined_prefix_mappings[NS.DC.prefix] = NS.DC.dc
                    if NS.ISO.prefix not in predefined_prefix_mappings:
                        predefined_prefix_mappings[NS.ISO.prefix] = NS.ISO.iso

        if export_linkset:
            if link_pred_prefix not in predefined_prefix_mappings:
                predefined_prefix_mappings[link_pred_prefix] = link_pred_uri

            if export_link_metadata:
                predefined_prefix_mappings = {**predefined_prefix_mappings,
                                              **self._predefined_export_only_reification_prefix_mappigs}

            for ets in self._entity_type_selections:
                predefined_prefix_mappings = {**predefined_prefix_mappings, **ets.collection.uri_prefix_mappings}

        return predefined_prefix_mappings

    def _namespaces_metadata_generator(self, prefix_mappings):
        buffer = io.StringIO()
        buffer.write(self._main_header('NAMESPACES'))

        for prefix, uri in prefix_mappings.items():
            buffer.write(F"@prefix {prefix:>{20}}: {URIRef(uri).n3()} .\n")

        yield buffer.getvalue()

    def _metadata_export_generator(self, ns_manager, link_pred_shortname, creator=None):
        def lens_metadata():
            buffer.write(self._header('LENS METADATA'))

            buffer.write('### LENS OPERATOR\n')
            for lens_operator in self._spec.operators:
                lens_operator_info = self._lens_operators_info[lens_operator]

                buffer.write(F"operator:{lens_operator}\n")
                buffer.write(pred_val('a', VoidPlus.LensOperator_ttl))
                buffer.write(pred_val(NS.RDFS.label_ttl, Literal(lens_operator_info['label']).n3()))
                buffer.write(pred_val(NS.DCterms.description_ttl,
                                      Literal(lens_operator_info['description'], lang='en').n3(), end=True))
                buffer.write("\n")

            buffer.write('### LENS RESOURCE DESCRIPTION\n')
            buffer.write(F"lens:{self._job.job_id}-{self._spec.id}\n")
            buffer.write(pred_val('a', VoidPlus.Lens_ttl))

            buffer.write(pred_val(NS.VoID.feature_ttl, F"{NS.Formats.turtle_ttl}, {NS.Formats.triG_ttl}"))
            buffer.write(pred_val(NS.CC.attributionName_ttl, Literal('Lenticular Lens', 'en').n3(ns_manager)))
            buffer.write(pred_val(NS.CC.license_ttl,
                                  URIRef('http://purl.org/NET/rdflicense/W3C1.0').n3(ns_manager)))
            buffer.write(pred_val(NS.DCterms.created_ttl,
                                  Literal(datetime.utcnow(), datatype=XSD.dateTime).n3(ns_manager)))

            if creator and len(creator.strip()) > 0:
                buffer.write(pred_val(NS.DCterms.creator_ttl, Literal(creator.strip()).n3(ns_manager)))

            buffer.write(pred_val(NS.DCterms.publisher_ttl, Literal(get_publisher().strip()).n3(ns_manager)))
            buffer.write(pred_val(NS.VoID.linkPredicate_tt, link_pred_shortname))

            buffer.write(pred_val(NS.RDFS.label_ttl, Literal(self._spec.label).n3(ns_manager)))
            if self._spec.description and len(self._spec.description) > 0:
                buffer.write(pred_val(NS.DCterms.description_ttl, Literal(self._spec.description).n3(ns_manager)))
            buffer.write("\n")

            buffer.write(pred_val(VoidPlus.hasOperator_ttl, multiple_val([
                F"lens:{lens_operator}" for lens_operator in self._spec.operators])))
            buffer.write("\n")

            buffer.write(pred_val(VoidPlus.hasOperand_ttl, multiple_val(
                [F"linkset:{self._job.job_id}-{linkset.id}" for linkset in self._spec.linksets] + \
                [F"lens:{self._job.job_id}-{lens.id}" for lens in self._spec.lenses], tabs=1
            )))
            buffer.write("\n")

            if self._spec.threshold:
                buffer.write(pred_val(VoidPlus.combiThreshold_ttl, self._spec.threshold))
                buffer.write("\n")

            lens = self._job.lens(self._id)
            if lens['links_count'] > 0:
                buffer.write(pred_val(NS.VoID.triples_ttl, Literal(lens['links_count']).n3(ns_manager)))

            if lens['lens_entities_count'] and lens['lens_entities_count'] > 0:
                buffer.write(pred_val(NS.VoID.entities_ttl, Literal(lens['lens_entities_count']).n3(ns_manager)))

            if lens['lens_sources_count'] and lens['lens_sources_count'] > 0:
                buffer.write(pred_val(NS.VoID.distinctSubjects_ttl, Literal(lens['lens_sources_count']).n3(ns_manager)))

            if lens['lens_targets_count'] and lens['lens_targets_count'] > 0:
                buffer.write(pred_val(NS.VoID.distinctObjects_ttl, Literal(lens['lens_targets_count']).n3(ns_manager)))

            clustering = self._job.clustering(self._id, 'lens')
            if clustering and clustering['clusters_count'] > 0:
                buffer.write("\n")
                buffer.write(pred_val(VoidPlus.clusters_ttl, Literal(clustering['clusters_count']).n3(ns_manager)))
                buffer.write(pred_val(VoidPlus.clusterset_ttl, F"clusterset:{self._job.job_id}-lens-{self._id}"))

            link_totals = self._job.get_links_totals(self._id, 'lens')
            if link_totals and link_totals['not_validated'] < lens['links_count']:
                buffer.write("\n")

                if link_totals['mixed'] > 0:
                    buffer.write(pred_val(VoidPlus.contradictions_ttl, Literal(link_totals['mixed']).n3(ns_manager)))

                buffer.write(pred_val(VoidPlus.has_validationset_ttl,
                                      F"validationset:{self._job.job_id}-lens-{self._id}"))

            buffer.write("\n")
            buffer.write(pred_val(VoidPlus.formulation_ttl,
                                  F"resource:LensFormulation-{self._job.job_id}-{self._spec.id}", end=True))

        def lens_logic_expression():
            def write_node(left, right, type, t_conorm, threshold, only_left, lens_id=None):
                id = F'(lens.{lens_id})' if lens_id else ''
                if lens_id:
                    legend[lens_id] = F'{id}: created as lens:{self._job.job_id}-{lens_id}'

                if only_left:
                    return Node(F"{type.upper()}{id}".strip(), children=[left, right])

                logic_ops_info = self._logic_ops_info[t_conorm]
                label_txt = F"{type.upper()} {id}".strip()
                fuzzy_txt = F"{logic_ops_info['label']} ({logic_ops_info['short']})"
                threshold_txt = F"[with sim ≥ {threshold}]" if 0 < threshold < 1 else ''

                return Node(F"{label_txt} using OR [{fuzzy_txt}] {threshold_txt}".strip(), children=[left, right])

            def write_spec(spec, id, type):
                if type == 'linkset':
                    return Node(F"linkset:{self._job.job_id}-{id}")

                return spec.with_lenses_recursive(lambda *args: write_node(*args, lens_id=id), write_spec)

            buffer.write(self._header("LENS LOGIC EXPRESSION"))

            legend = OrderedDict()
            root = self._spec.with_lenses_recursive(write_node, write_spec)
            legend_txt = f'\n\n{TAB}{TAB}Legend:\n{TAB}{TAB}{TAB}' + \
                         f'\n{TAB}{TAB}{TAB}'.join(line for line in legend.values()) if legend else ''

            buffer.write(F"resource:LensFormulation-{self._job.job_id}-{self._spec.id}\n")
            buffer.write(pred_val('a', VoidPlus.LensFormulation_ttl))

            buffer.write(pred_val(VoidPlus.part_ttl, multiple_val([F"linkset:{self._job.job_id}-{linkset.id}"
                                                                   for linkset in self._spec.linksets], tabs=1)))

            buffer.write(pred_val(VoidPlus.formulaDescription_ttl,
                                  Literal(self._expression(root) + legend_txt).n3(ns_manager)))
            buffer.write("\n")

            buffer.write(pred_val(VoidPlus.formulaTree_ttl,
                                  Literal(F"\n{TAB}{self._tree(root) + legend_txt}\n{TAB}").n3(ns_manager), end=True))

            buffer.write("\n")

        def linkset_generic_metadata():
            buffer.write(self._header('LINKSET GENERIC METADATA'))

            linksets = self._job.linksets
            clusterings = self._job.clusterings

            for idx, spec in enumerate(self._linkset_specs):
                linkset = next(linkset for linkset in linksets if linkset['spec_id'] == spec.id)
                clustering = next(clustering for clustering in clusterings
                                  if clustering['spec_id'] == spec.id and clustering['spec_type'] == 'linkset')

                buffer.write(F"### JOB ID       : {self._job.job_id}\n")
                buffer.write(F"### LINKSET ID   : {spec.id}\n")

                buffer.write(F"linkset:{self._job.job_id}-{spec.id}\n")
                buffer.write(pred_val('a', VoidPlus.Linkset_ttl))

                buffer.write(pred_val(NS.VoID.feature_ttl, F"{NS.Formats.turtle_ttl}, {NS.Formats.triG_ttl}"))
                buffer.write(pred_val(NS.CC.attributionName_ttl, Literal('Lenticular Lens', 'en').n3(ns_manager)))
                buffer.write(pred_val(NS.CC.license_ttl,
                                      URIRef('http://purl.org/NET/rdflicense/W3C1.0').n3(ns_manager)))
                buffer.write(pred_val(NS.DCterms.created_ttl,
                                      Literal(datetime.utcnow(), datatype=XSD.dateTime).n3(ns_manager)))

                if creator and len(creator.strip()) > 0:
                    buffer.write(pred_val(NS.DCterms.creator_ttl, Literal(creator.strip()).n3(ns_manager)))

                buffer.write(pred_val(NS.DCterms.publisher_ttl, Literal(get_publisher().strip()).n3(ns_manager)))
                buffer.write(pred_val(NS.VoID.linkPredicate_tt, link_pred_shortname))

                buffer.write(pred_val(NS.RDFS.label_ttl, Literal(spec.label).n3(ns_manager)))
                if spec.description and len(spec.description) > 0:
                    buffer.write(pred_val(NS.DCterms.description_ttl, Literal(spec.description).n3(ns_manager)))

                buffer.write(F"\n{TAB}### VOID LINKSET STATS\n")

                if linkset['links_count'] > 0:
                    buffer.write(pred_val(NS.VoID.triples_ttl, linkset['links_count']))

                if linkset['linkset_entities_count'] > 0:
                    buffer.write(pred_val(NS.VoID.entities_ttl, linkset['linkset_entities_count']))

                if linkset['linkset_sources_count'] > 0:
                    buffer.write(pred_val(NS.VoID.distinctSubjects_ttl, linkset['linkset_sources_count']))

                if linkset['linkset_targets_count'] > 0:
                    buffer.write(pred_val(NS.VoID.distinctObjects_ttl, linkset['linkset_targets_count']))

                buffer.write(F"\n{TAB}### SOURCE AND TARGET DATASETS STATS\n")

                if linkset['entities_count'] > 0:
                    buffer.write(pred_val(VoidPlus.srcTrgEntities_ttl, linkset['entities_count']))

                if linkset['sources_count'] > 0:
                    buffer.write(pred_val(VoidPlus.sourceEntities_ttl, linkset['sources_count']))

                if linkset['targets_count'] > 0:
                    buffer.write(pred_val(VoidPlus.targetEntities_ttl, linkset['targets_count']))

                buffer.write(F"\n{TAB}### ABOUT CLUSTERS\n")

                if clustering and clustering['clusters_count'] > 0:
                    buffer.write(pred_val(VoidPlus.clusters_ttl, clustering['clusters_count']))
                    buffer.write(pred_val(VoidPlus.clusterset_ttl,
                                          F"clusterset:{self._job.job_id}-linkset-{spec.id}"))

                buffer.write(F"\n{TAB}### SOURCE ENTITY TYPE SELECTION(S)\n")
                buffer.write(pred_val(VoidPlus.subTarget_ttl,
                                      multiple_val([F"resource:ResourceSelection-{self._job.job_id}-{selection.id}"
                                                    for selection in spec.sources])))

                buffer.write(F"\n{TAB}### TARGET ENTITY TYPE SELECTION(S)\n")
                buffer.write(pred_val(VoidPlus.objTarget_ttl,
                                      multiple_val([F"resource:ResourceSelection-{self._job.job_id}-{selection.id}"
                                                    for selection in spec.targets])))

                buffer.write(F"\n{TAB}### THE LOGIC FORMULA\n")
                buffer.write(pred_val(VoidPlus.formulation_ttl,
                                      F"resource:LinksetFormulation-{self._job.job_id}-{spec.id}", end=True))

                if idx + 1 < len(self._linkset_specs):
                    buffer.write("\n")

        def linkset_logic():
            def write_node(children_nodes, operator, fuzzy, threshold):
                logic_ops_info = self._logic_ops_info[fuzzy]
                fuzzy_txt = F"{logic_ops_info['label']} ({logic_ops_info['short']})"
                threshold_txt = F"[with sim ≥ {threshold}]" if 0 < threshold < 1 else ''

                return Node(F"{operator} [{fuzzy_txt}] {threshold_txt}".strip(), children=children_nodes)

            buffer.write(self._header("LINKSET LOGIC EXPRESSION"))

            for idx, linkset in enumerate(self._linkset_specs):
                root = linkset.with_matching_methods_recursive(
                    write_node,
                    lambda mm: Node(F"resource:{mm.method_name}-{mm.config_hash}")
                )

                buffer.write(F"resource:LinksetFormulation-{self._job.job_id}-{linkset.id}\n")
                buffer.write(pred_val('a', VoidPlus.LinksetLogicFormulation_ttl))

                buffer.write(pred_val(VoidPlus.part_ttl, multiple_val(
                    [F"resource:{matching_method.method_name}-{matching_method.config_hash}"
                     for matching_method in linkset.matching_methods])))
                buffer.write("\n")

                buffer.write(pred_val(VoidPlus.formulaDescription_ttl, Literal(self._expression(root)).n3(ns_manager)))
                buffer.write("\n")

                buffer.write(pred_val(VoidPlus.formulaTree_ttl,
                                      Literal(F"\n{TAB}{self._tree(root)}\n{TAB}").n3(ns_manager), end=True))

                if idx + 1 < len(self._linkset_specs):
                    buffer.write("\n")

        def resource_selections():
            def get_selection_root(selection):
                return selection.with_filters_recursive(
                    lambda children_nodes, type: Node(type, children=children_nodes),
                    lambda filter_func: Node(F"resource:PropertyPartition-{filter_func.hash}")
                )

            class_partitions = dict()
            selection_formulations = dict()
            filters = dict()

            buffer.write(F"{self._header('LINKSET RESOURCE SELECTIONS')}")
            for selection in sorted(self._entity_type_selections, key=lambda ets: ets.id):
                root = get_selection_root(selection)
                class_partition_key = hash_string_min(hash(selection.collection))
                selection_formulation_key = hash_string_min(root)

                class_partitions[class_partition_key] = selection.collection.table_data['collection_uri']
                selection_formulations[selection_formulation_key] = (class_partition_key, selection)
                for filter in selection.filters:
                    filters[filter.hash] = filter

                buffer.write(F"### RESOURCE {selection.id}\n")
                buffer.write(F"resource:ResourceSelection-{self._job.job_id}-{selection.id}\n")
                buffer.write(pred_val('a', F"{NS.VoID.dataset_ttl}, {VoidPlus.EntitySelection_ttl}"))

                buffer.write(pred_val(NS.RDFS.label_ttl, Literal(selection.label).n3(ns_manager)))
                if selection.description:
                    buffer.write(pred_val(NS.DCterms.description_ttl, Literal(selection.description).n3(ns_manager)))

                buffer.write(pred_val(VoidPlus.subset_of_ttl, F"resource:{selection.dataset_id}"))
                buffer.write(pred_val(NS.DCterms.identifier_ttl,
                                      Literal(selection.collection.table_data['dataset_name']).n3(ns_manager)))
                buffer.write(pred_val(VoidPlus.hasFormulation_ttl,
                                      F"resource:SelectionFormulation-{selection_formulation_key}", end=True))
                buffer.write("\n")

            for key, uri in class_partitions.items():
                buffer.write(F"\nresource:ClassPartition-{key}\n")
                buffer.write(pred_val('a', F"{VoidPlus.ClassPartition_ttl}"))
                buffer.write(pred_val(NS.VoID.voidClass_ttl, URIRef(uri).n3(ns_manager), end=True))

            for key, (class_partition_key, selection) in selection_formulations.items():
                root = get_selection_root(selection)

                buffer.write(F"\nresource:SelectionFormulation-{key}\n")
                buffer.write(pred_val('a', F"{VoidPlus.PartitionFormulation_ttl}"))

                items = [F"resource:ClassPartition-{class_partition_key}"]
                items += list(set(F"resource:PropertyPartition-{filter.hash}" for filter in selection.filters))
                buffer.write(pred_val(VoidPlus.hasItem_ttl, multiple_val(items), end=(not root)))

                if root:
                    root.parent = Node("AND")
                    Node(F"resource:ClassPartition-{class_partition_key}", parent=root.parent)

                    buffer.write("\n")
                    buffer.write(pred_val(VoidPlus.formulaDescription_ttl,
                                          Literal(self._expression(root.parent)).n3(ns_manager)))

                    buffer.write("\n")
                    buffer.write(pred_val(VoidPlus.formulaTree_ttl,
                                          Literal(F"\n{TAB}{self._tree(root.parent)}\n{TAB}").n3(ns_manager), end=True))

            for key, filter in filters.items():
                buffer.write(F"\nresource:PropertyPartition-{key}\n")
                buffer.write(pred_val('a', F"{VoidPlus.PropertyPartition_ttl}"))
                buffer.write(filter.property_field.n3(ns_manager))

                buffer.write(pred_val(VoidPlus.filterFunction_ttl, Literal(filter.function_name).n3(ns_manager),
                                      end=(not filter.value)))
                if filter.value:
                    buffer.write("\n")
                    buffer.write(pred_val(
                        VoidPlus.filterValue_ttl, Literal(filter.value).n3(ns_manager),
                        end=('format' not in filter.parameters)))

                if 'format' in filter.parameters:
                    buffer.write(pred_val(VoidPlus.filterFormat_ttl,
                                          Literal(filter.parameters['format']).n3(ns_manager), end=True))

        def methods_signatures():
            def write_algorithm(method_config, method_info):
                pred_vals = [(VoidPlus.thresholdRange_ttl, Literal(method_info['threshold_range']).n3(ns_manager))]

                for prop_key in method_info.get('items', {}).keys():
                    if 'rdf' in method_info['items'][prop_key]:
                        predicate_rdf_info = method_info['items'][prop_key]['rdf']

                        values = method_config[prop_key]
                        if values in predicate_rdf_info.get('values', {}):
                            values = predicate_rdf_info['values'][values]

                        if not isinstance(values, list):
                            values = [values]

                        is_uri_ref = isinstance(values[0], dict)

                        pred_vals.append((
                            URIRef(predicate_rdf_info['predicate']).n3(ns_manager),
                            multiple_val([URIRef(v['predicate']).n3(ns_manager)
                                          if is_uri_ref else Literal(v).n3(ns_manager) for v in values])
                        ))

                return pred_vals

            buffer.write(self._header('METHOD SIGNATURES'))

            has_list_matching_absolute, has_list_matching_relative = False, False
            matching_methods_hashed = {matching_method.config_hash: matching_method
                                       for matching_method in self._matching_methods}

            for idx, (key, matching_method) in enumerate(matching_methods_hashed.items()):
                buffer.write(F"resource:{matching_method.method_name}-{key}\n")
                buffer.write(pred_val('a', VoidPlus.MatchingMethod_ttl))

                if matching_method.method_sim_name:
                    buffer.write(pred_val(VoidPlus.methodSequence_ttl,
                                          F"resource:AlgorithmSequence-{matching_method.field_name}"))
                else:
                    buffer.write(pred_val(VoidPlus.method_ttl, F"resource:{matching_method.method_name}"))

                if matching_method.threshold:
                    buffer.write(pred_val(VoidPlus.simThreshold_ttl,
                                          Literal(matching_method.threshold).n3(ns_manager)))
                    buffer.write(pred_val(VoidPlus.thresholdRange_ttl, Literal("]0, 1]").n3(ns_manager)))

                if not matching_method.method_sim_name:
                    for (pred, val) in write_algorithm(matching_method.method_config, matching_method.method_info):
                        buffer.write(pred_val(pred, val))

                buffer.write("\n")
                if matching_method.is_list_match:
                    if matching_method.list_is_percentage:
                        has_list_matching_relative = True
                    else:
                        has_list_matching_absolute = True

                    buffer.write(pred_val('voidPlus:hasListConfiguration', blank_node([
                        ('voidPlus:listThreshold', Literal(matching_method.list_threshold).n3(ns_manager)),
                        ('voidPlus:appreciation',
                         "resource:" + ("RelativeCount" if matching_method.list_is_percentage else "AbsoluteCount"))
                    ])))

                sources = flatten(list(matching_method.sources.values()))
                targets = flatten(list(matching_method.targets.values()))

                transformers_sources = matching_method.transformers('sources')
                transformers_targets = matching_method.transformers('targets')

                sources_ref = F"resource:ResourcePartition-Sources-{matching_method.field_name}" \
                    if len(sources) > 1 or transformers_sources else \
                    F"resource:ResourcePartition-{sources[0].prop_original.hash}"
                targets_ref = F"resource:ResourcePartition-Targets-{matching_method.field_name}" \
                    if len(targets) > 1 or transformers_targets else \
                    F"resource:ResourcePartition-{targets[0].prop_original.hash}"

                buffer.write(pred_val(VoidPlus.entitySelectionSubj_ttl, sources_ref))
                buffer.write(pred_val(VoidPlus.entitySelectionObj_ttl, targets_ref,
                                      end=(not matching_method.is_intermediate)))

                if matching_method.is_intermediate:
                    buffer.write(pred_val(VoidPlus.intermediateSubjEntitySelection_ttl, multiple_val({
                        F"resource:ResourcePartition-{prop.prop_original.hash}"
                        for ets, props_ets in matching_method.intermediates.items()
                        for prop in props_ets['source']
                    })))

                    buffer.write(pred_val(VoidPlus.intermediateObjEntitySelection_ttl, multiple_val({
                        F"resource:ResourcePartition-{prop.prop_original.hash}"
                        for ets, props_ets in matching_method.intermediates.items()
                        for prop in props_ets['target']
                    }), end=True))

                if matching_method.method_sim_name:
                    buffer.write(F"\nresource:AlgorithmSequence-{matching_method.field_name}\n")
                    buffer.write(pred_val('a', NS.RDFS.sequence_ttl))

                    pred_vals = [(VoidPlus.method_ttl, F"resource:{matching_method.method_name}")] + \
                                write_algorithm(matching_method.method_config, matching_method.method_info)
                    buffer.write(pred_val('rdf:_1', blank_node(pred_vals)))

                    pred_vals = [(VoidPlus.method_ttl, F"resource:{matching_method.method_sim_name}"),
                                 (VoidPlus.normalized_ttl,
                                  Literal(matching_method.method_sim_normalized).n3(ns_manager))] + \
                                write_algorithm(matching_method.method_sim_config, matching_method.method_sim_info)
                    buffer.write(pred_val('rdf:_2', blank_node(pred_vals), end=True))

                if idx + 1 < len(self._matching_methods):
                    buffer.write("\n")

            if has_list_matching_absolute:
                buffer.write("\nresource:AbsoluteCount\n")
                buffer.write(pred_val(
                    NS.DCterms.description_ttl,
                    Literal("Establishes a link between the source and target when the absolute threshold is reached.",
                            lang='en').n3(ns_manager), end=True))

            if has_list_matching_relative:
                buffer.write("\nresource:RelativeCount\n")
                buffer.write(pred_val(
                    NS.DCterms.description_ttl,
                    Literal("Establishes a link when the percentage threshold is reached.", lang='en').n3(ns_manager),
                    end=True))

        def methods_predicate_selections():
            stopwords_selected = dict()

            def write_transformer(transformer, tabs=1):
                if transformer['name'] == 'STOPWORDS':
                    dictionary = transformer['parameters']['dictionary']
                    additional = transformer['parameters']['additional']

                    stopwords = get_stopwords(dictionary)
                    hash = hash_string_min(stopwords)
                    language = dictionary.split('_')[0]

                    uri = F"resource:{language[0].upper()}{language[1:]}-StopwordsList-{hash}"
                    buffer.write(pred_val(VoidPlus.stopWords_ttl, uri, tabs=tabs))
                    stopwords_selected[uri] = (stopwords, get_iso_639_1_code(language))

                    if additional:
                        uri = F"resource:StopwordsList-{hash_string_min(additional)}"
                        buffer.write(pred_val(VoidPlus.stopWords_ttl, uri, tabs=tabs))
                        stopwords_selected[uri] = (additional, None)
                else:
                    buffer.write(pred_val(VoidPlus.tranformationFunction_ttl,
                                          Literal(transformer['name']).n3(ns_manager), tabs=tabs))

                    if transformer['parameters']:
                        buffer.write(pred_val("voidPlus:hasTransformationParameters",
                                              Literal(transformer['parameters']).n3(ns_manager), end=False))

            buffer.write(self._header("METHODS'S PREDICATE SELECTIONS"))

            for matching_method in self._matching_methods:
                for is_source in (True, False):
                    matching_method_props = matching_method.sources if is_source else matching_method.targets
                    transformers = matching_method.transformers('sources' if is_source else 'targets')

                    has_multiple_props = len(flatten(list(matching_method_props.values()))) > 1
                    if transformers or has_multiple_props:
                        id = F"{'Sources' if is_source else 'Targets'}-{matching_method.field_name}"

                        logic_ops_info = self._logic_ops_info[matching_method.t_conorm]
                        fuzzy_txt = F"{logic_ops_info['label']} ({logic_ops_info['short']})"

                        threshold_txt = (F"[with sim ≥ {matching_method.threshold}]"
                                         if matching_method.threshold < 1 else F"[with sim = 1]") \
                            if matching_method.threshold > 0 else ''

                        root = Node(F"OR [{fuzzy_txt}] {threshold_txt}".strip())

                        buffer.write(F"resource:ResourcePartition-{id}\n")
                        buffer.write(pred_val('a', VoidPlus.EntitySelection_ttl))
                        buffer.write(pred_val(VoidPlus.hasFormulation_ttl,
                                              F"resource:PartitionFormulation-{id}", end=True))

                        buffer.write(F"\nresource:PartitionFormulation-{id}\n")
                        buffer.write(pred_val('a', VoidPlus.PartitionFormulation_ttl))

                        for transformer in transformers:
                            write_transformer(transformer)

                        for (idx, matching_method_prop) in enumerate(flatten(list(matching_method_props.values()))):
                            property = matching_method_prop.prop_original
                            buffer.write(pred_val(VoidPlus.part_ttl, F"resource:PropertyPartition-{property.hash}",
                                                  end=(not has_multiple_props)))
                            Node(F"resource:PropertyPartition-{property.hash}", parent=root)

                        if has_multiple_props:
                            buffer.write(pred_val(VoidPlus.formulaDescription_ttl,
                                                  Literal(self._expression(root)).n3(ns_manager)))
                            buffer.write(pred_val(VoidPlus.formulaTree_ttl,
                                                  Literal(F"\n{TAB}{self._tree(root)}\n{TAB}").n3(ns_manager),
                                                  end=True))

                        buffer.write("\n")

            for idx, (ets, matching_method_prop) in enumerate(self._matching_methods_props):
                property = matching_method_prop.prop_original

                buffer.write(F"resource:PropertyPartition-{property.hash}\n")
                buffer.write(pred_val('a', VoidPlus.PropertyPartition_ttl))
                buffer.write(pred_val(VoidPlus.subset_of_ttl, F"resource:ResourceSelection-{ets}"))

                for transformer in matching_method_prop.property_transformers:
                    write_transformer(transformer)

                buffer.write(property.n3(ns_manager, end=True))

                if len(stopwords_selected) or idx + 1 < len(self._matching_methods_props):
                    buffer.write("\n")

            for idx, (uri, (stopwords, language_code)) in enumerate(list(stopwords_selected.items())):
                buffer.write(F"{uri}\n")
                if language_code:
                    buffer.write(pred_val(NS.DC.language_ttl, F"{NS.ISO.prefix}:{language_code}"))

                new = f'\n{TAB}{TAB}'
                buffer.write(pred_val(VoidPlus.stopWordsList_ttl,
                                      F", ".join(F"{new if i % 10 == 0 else ''}{Literal(word).n3(ns_manager)}"
                                                 for i, word in enumerate(stopwords)), end=True))

                if idx + 1 < len(stopwords_selected):
                    buffer.write("\n")

        def methods_descriptions():
            buffer.write(self._header("METHODS'S DESCRIPTION"))

            method_infos = {matching_method.method_name for matching_method in self._matching_methods}
            for idx, method_name in enumerate(method_infos):
                method_info = self._matching_methods_info[method_name]

                buffer.write(F"resource:{method_name}\n")
                buffer.write(pred_val('a', VoidPlus.MatchingAlgorithm_ttl))
                buffer.write(pred_val(NS.RDFS.label_ttl, Literal(method_info['label'], lang='en').n3(ns_manager)))
                buffer.write(pred_val(NS.DCterms.description_ttl,
                                      Literal(method_info['description'], lang='en').n3(ns_manager)))
                buffer.write(pred_val(NS.RDFS.seeAlso_ttl, multiple_val([
                    URIRef(uri).n3(ns_manager) for uri in method_info['see_also']
                ]), end=True))

                if idx + 1 < len(method_infos):
                    buffer.write("\n")

        buffer = io.StringIO()

        if self._type == 'lens':
            lens_metadata()
            yield get_from_buffer(buffer)

            lens_logic_expression()
            yield get_from_buffer(buffer)

            buffer.write(F"\n\n{self._main_header('METADATA OF THE LINKSETS COMPOSING THE LENS')}")

        linkset_generic_metadata()
        yield get_from_buffer(buffer)

        linkset_logic()
        yield get_from_buffer(buffer)

        resource_selections()
        yield get_from_buffer(buffer)

        methods_signatures()
        yield get_from_buffer(buffer)

        methods_predicate_selections()
        yield get_from_buffer(buffer)

        methods_descriptions()
        yield buffer.getvalue()

    def _linkset_export_generator(self, links_iter, link_predicate, ns_manager,
                                  reification='none', use_graphs=True):
        buffer = io.StringIO()
        buffer.write(F"\n\n{self._main_header('ANNOTATED LINKSET' if self._type == 'linkset' else 'ANNOTATED LENS')}")

        if use_graphs:
            buffer.write(F"{self._type}:{self._job.job_id}-{self._id}\n{{\n")

        i = 0
        tabs = 2 if use_graphs else 1
        rdf_predicate = URIRef(link_predicate).n3(ns_manager)

        for link in links_iter:
            hash = hash_string_min((link['source'], link['target'])
                                   if link['link_order'] != 'target_source' else
                                   (link['target'], link['source'])) \
                if reification != 'none' and reification != 'rdf_star' else None

            source_uri = URIRef(link['source'] if link['link_order'] != 'target_source'
                                else link['target']).n3(ns_manager)
            target_uri = URIRef(link['target'] if link['link_order'] != 'target_source'
                                else link['source']).n3(ns_manager)
            predicate = F'resource:Singleton-{hash}' if reification == 'singleton' else rdf_predicate

            link_rdf = F"{source_uri}{TAB}{predicate}{TAB}{target_uri}"
            if reification == 'rdf_star':
                buffer.write(F"{TAB if use_graphs else ''}<<{link_rdf}>>\n")
            else:
                buffer.write(F"{TAB if use_graphs else ''}{link_rdf} .\n")

            if reification != 'none':
                if reification == 'standard':
                    buffer.write(F"\n{TAB if use_graphs else ''}resource:Reification-{hash}\n")
                    buffer.write(pred_val('a', 'rdf:Statement', tabs=tabs))
                    buffer.write(pred_val('rdf:predicate', predicate, tabs=tabs))
                    buffer.write(pred_val('rdf:subject', source_uri, tabs=tabs))
                    buffer.write(pred_val('rdf:object', target_uri, tabs=tabs))
                elif reification == 'singleton':
                    buffer.write(F"\n{TAB if use_graphs else ''}{predicate}\n")
                    buffer.write(pred_val('rdf:singletonPropertyOf', rdf_predicate, tabs=tabs))

                if link['cluster_hash_id']:
                    buffer.write(pred_val(VoidPlus.cluster_ID_ttl, F"cluster:{link['cluster_hash_id']}", tabs=tabs))

                strength = round(link['similarity'], 5) if link['similarity'] else 1
                buffer.write(pred_val(VoidPlus.strength_ttl, strength, tabs=tabs))

                validation_id = hash_string_min((link['source'], link['target']))
                buffer.write(pred_val(VoidPlus.has_validation_ttl, F"validation:{validation_id}", tabs=tabs, end=True))

            buffer.write("\n")

            i += 1
            if i > 1000:
                i = 0
                yield get_from_buffer(buffer)

        if use_graphs:
            buffer.write('}')

        yield buffer.getvalue()

    def _validations_export_generator(self, links_iter, ns_manager):
        def validation_metadata():
            buffer.write(self._header("LINK VALIDATION METADATA"))

            buffer.write(F"validationset:{self._job.job_id}-{self._type}-{self._id}\n")
            buffer.write(pred_val('a', VoidPlus.Validationset_ttl))
            buffer.write(pred_val(VoidPlus.hasTarget_ttl, F"{self._type}:{self._job.job_id}-{self._id}\n"))

            buffer.write(F"\n{TAB}### VOID+ VALIDATION STATS\n")
            link_totals = self._job.get_links_totals(self._id, self._type)

            if link_totals['accepted'] > 0:
                buffer.write(pred_val(VoidPlus.accepted_ttl, Literal(link_totals['accepted']).n3(ns_manager)))

            if link_totals['rejected'] > 0:
                buffer.write(pred_val(VoidPlus.rejected_ttl, Literal(link_totals['rejected']).n3(ns_manager)))

            if link_totals['not_sure'] > 0:
                buffer.write(pred_val(VoidPlus.uncertain_ttl, Literal(link_totals['not_sure']).n3(ns_manager)))

            if link_totals['not_validated'] > 0:
                buffer.write(pred_val(VoidPlus.unchecked_ttl, Literal(link_totals['not_validated']).n3(ns_manager)))

            buffer.write("\n")
            buffer.write(pred_val(NS.DCterms.description_ttl,
                                  'Unless explicitly stated in a specific validation resource, '
                                  'a. An accepted link entails that the validator agrees with the alignment (matching) '
                                  'in general and with the specific correspondence under scrutiny. '
                                  'b. A rejected link entails that the validator agrees with the alignment (matching) '
                                  'in general but disagrees with the specific correspondence under scrutiny. '
                                  'Together, the values of the selected properties provided by the validator '
                                  'justify her disagreement. c. Rejecting an alignment entails that '
                                  'the validator disagrees with the alignment in general and may have selected '
                                  'a set of properties for which the values justify her disagreement.', end=True))

        def validation_terminology():
            buffer.write(self._header("VALIDATION TERMINOLOGY"))

            for idx, validation_state_info in enumerate(list(self._validation_states_info.values())):
                buffer.write(F"resource:{validation_state_info['label']}\n")
                buffer.write(pred_val('a', VoidPlus.ValidationFlag_ttl))
                buffer.write(pred_val(NS.RDFS.label_ttl,
                                      Literal(validation_state_info['label'], lang='en').n3(ns_manager)))
                buffer.write(pred_val(NS.DCterms.description_ttl,
                                      Literal(validation_state_info['description'], lang='en').n3(ns_manager),
                                      end=True))

                if idx + 1 < len(self._validation_states_info.values()):
                    buffer.write("\n")

        def validation_set():
            buffer.write(self._header("VALIDATIONSET"))
            buffer.write(F"validationset:{self._job.job_id}-{self._type}-{self._id}\n{{\n")

            i = 0
            for link in links_iter:
                validation_id = hash_string_min((link['source'], link['target']))

                buffer.write(F"\n{TAB}validation:{validation_id}\n")
                buffer.write(pred_val('a', VoidPlus.Validation_ttl, tabs=2))

                if link['motivation']:
                    buffer.write(pred_val(VoidPlus.motivation_ttl, Literal(link['motivation']).n3(ns_manager), tabs=2))

                validation_info = self._validation_states_info[link['valid']]
                buffer.write(pred_val(VoidPlus.has_validation_status_ttl, F"resource:{validation_info['label']}",
                                      tabs=2, end=True))

                buffer.write("\n")

                i += 1
                if i > 1000:
                    i = 0
                    yield get_from_buffer(buffer)

            buffer.write('}')

        buffer = io.StringIO()

        validation_metadata()
        yield get_from_buffer(buffer)

        validation_terminology()
        yield get_from_buffer(buffer)

        validation_set()
        yield buffer.getvalue()

    def _clusters_export_generator(self, clusters_iter, ns_manager):
        def clusters_metadata():
            buffer.write(self._header("RESOURCE PARTITIONING METADATA"))

            buffer.write(F"clusterset:{self._job.job_id}-{self._type}-{self._id}\n")
            buffer.write(pred_val('a', VoidPlus.Clusterset_ttl))

            clustering = self._job.clustering(self._id, self._type)
            buffer.write(pred_val(VoidPlus.clusters_ttl, Literal(clustering['clusters_count']).n3(ns_manager)))
            buffer.write(pred_val(NS.VoID.entities_ttl, Literal(clustering['resources_size']).n3(ns_manager)))
            buffer.write(pred_val(VoidPlus.validations_ttl, "###VALIDATED"))

            buffer.write(pred_val(VoidPlus.largestNodeCount_ttl, Literal(clustering['largest_size']).n3(ns_manager)))
            buffer.write(pred_val(VoidPlus.largestLinkCount_ttl, Literal(clustering['largest_count']).n3(ns_manager)))

            buffer.write(pred_val(VoidPlus.hasTarget_ttl, F"{self._type}:{self._job.job_id}-{self._id}\n"))
            buffer.write(pred_val(VoidPlus.method_ttl, "resource:SimpleClustering", end=True))

            buffer.write('\n\nresource:SimpleClustering\n')
            buffer.write(pred_val('a', VoidPlus.ClusteringAlgorithm_ttl))
            buffer.write(pred_val(NS.DCterms.description_ttl, Literal(
                "A collection of clusters of resources where each cluster is obtained by the transitivity of links. "
                "In case these links are identity links, the clustered resources could be seen as co-referents "
                "and the network formed from the co-referents resources is an identity (link) network."
            ).n3(ns_manager)))
            buffer.write(pred_val(NS.RDFS.seeAlso_ttl,
                                  URIRef("https://doi.org/10.3233/SW-200410").n3(ns_manager), end=True))

        def clusters_set():
            buffer.write(self._header("ANNOTATED CO-REFERENT RESOURCES"))
            buffer.write(F"clusterset:{self._job.job_id}-{self._type}-{self._id}\n{{\n")

            i = 0
            for cluster in clusters_iter:
                buffer.write(F"\n{TAB}cluster:{cluster['hash_id']}\n")
                buffer.write(pred_val('a', VoidPlus.Cluster_ttl, tabs=2))

                buffer.write(pred_val(VoidPlus.links_ttl, Literal(cluster['links']).n3(ns_manager), tabs=2))
                buffer.write(pred_val(VoidPlus.size_ttl, Literal(cluster['size']).n3(ns_manager), tabs=2))
                buffer.write(pred_val(VoidPlus.extended_ttl, Literal(cluster['extended']).n3(ns_manager), tabs=2))
                buffer.write(pred_val(VoidPlus.reconciled_ttl, Literal(cluster['reconciled']).n3(ns_manager), tabs=2))
                buffer.write(pred_val(VoidPlus.hasItem_ttl, multiple_val([
                    URIRef(uri).n3(ns_manager) for uri in cluster['nodes']
                ], tabs=2), tabs=2, end=True))

                buffer.write("\n")

                i += 1
                if i > 50:
                    i = 0
                    yield get_from_buffer(buffer)

            buffer.write('}')

        buffer = io.StringIO()

        clusters_metadata()
        yield get_from_buffer(buffer)

        clusters_set()
        yield buffer.getvalue()

    @staticmethod
    def _main_header(x):
        liner = "\n"
        return F"{'#' * 110}\n#{x:^108}#\n{'#' * 110}{liner * 3}"

    @staticmethod
    def _header(x):
        liner = "\n"
        return F"{liner * 2}{'#' * 80:^110}\n{' ' * 15}#{x:^78}#\n{'#' * 80:^110}{liner * 3}"

    @staticmethod
    def _expression(root):
        def expression_generator(post_order):
            temporary, new = [], []
            for item in post_order:
                if item.strip() and all(not item.strip().lower().startswith(prefix)
                                        for prefix in ['and', 'or'] + list(RdfExport._lens_operators_info.keys())):
                    temporary.append(item)
                elif len(temporary) > 1:
                    new.append(F'({F" {item} ".join(temporary)})')
                    temporary.clear()
                elif len(temporary) == 1:
                    new = [F'({F" {item} ".join(new + temporary)})']
                    temporary.clear()
                else:
                    new.append(item)

            if len(new) > 1:
                new = expression_generator(new)

            return new if new else post_order

        return expression_generator([node.name for node in PostOrderIter(root)])[0]

    @staticmethod
    def _tree(root):
        return F'\n{TAB}'.join([F"{TAB}%s%s" % (pre, node.name)
                                for i, (pre, fill, node) in enumerate(RenderTree(root, style=DoubleStyle))])
