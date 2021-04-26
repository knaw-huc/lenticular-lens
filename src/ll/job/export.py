import csv
import io
import itertools

from inspect import cleandoc
from datetime import datetime

from rdflib import Literal, URIRef, XSD, Graph
from rdflib.namespace import NamespaceManager
from anytree import Node, RenderTree, DoubleStyle, PostOrderIter

from ll.job.validation import Validation

from ll.namespaces.void_plus import VoidPlus
from ll.namespaces.shared_ontologies import Namespaces as NS

from ll.util.hasher import hash_string_min
from ll.util.stopwords import get_stopwords, get_iso_639_1_code
from ll.util.helpers import n3_pred_val, get_json_from_file, flatten


class Export:
    _logic_ops_info = get_json_from_file('logic_ops.json')
    _matching_methods_info = get_json_from_file('matching_methods.json')
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

    def __init__(self, job, type, id):
        self._job = job
        self._type = type
        self._id = id

        spec = self._job.get_spec_by_id(self._id, self._type)
        self._linksets = {spec} if self._type == 'linkset' else {linkset for linkset in spec.linksets}
        self._stats = {linkset.id: job.linkset(linkset.id) for linkset in self._linksets}
        self._clusterings = {linkset.id: job.clustering(linkset.id, 'linkset') for linkset in self._linksets}
        self._totals = {linkset.id: job.get_links_totals(linkset.id, 'linkset') for linkset in self._linksets}

        self._entity_type_selections = spec.entity_type_selections if self._type == 'linkset' else \
            {ets for linkset in self._linksets for ets in linkset.entity_type_selections}
        self._matching_methods = spec.matching_methods if self._type == 'linkset' else \
            [matching_method for linkset in self._linksets for matching_method in linkset.matching_methods]

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

    def csv_export_generator(self, validation_filter=Validation.ALL):
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(['Source URI', 'Target URI', 'Strength', 'Valid', 'Cluster ID'])

        i = 0
        for link in self._job.get_links(self._id, self._type, validation_filter=validation_filter):
            similarity = round(link['similarity'], 5) if link['similarity'] else 1
            cluster_id = link['cluster_id'] if link['cluster_id'] else ''

            source_uri = link['source'] if link['link_order'] != 'target_source' else link['target']
            target_uri = link['target'] if link['link_order'] != 'target_source' else link['source']

            writer.writerow([source_uri, target_uri, similarity, link['valid'], cluster_id])

            i += 1
            if i > 1000:
                i = 0
                yield self._get_from_buffer(buffer)

        yield buffer.getvalue()

    def rdf_export_generator(self, link_pred_namespace, link_pred_shortname,
                             export_metadata=True, export_linkset=True,
                             reification='none', use_graphs=True, creator=None, publisher=None,
                             validation_filter=Validation.ALL):
        def rdf_namespaces_export():
            buffer = io.StringIO()
            buffer.write(F"{'#' * 110}\n#{'NAMESPACES':^108}#\n{'#' * 110}\n\n")

            if export_metadata:
                buffer.write(cleandoc(F"""
                        {NS.RDF.prefix_ttl}
                        {NS.RDFS.prefix_ttl}
                        {NS.VoID.prefix_ttl}
                        {NS.DCterms.prefix_ttl}
                        {NS.Formats.prefix_ttl}
                        {NS.CC.prefix_ttl}
                        {NS.XSD.prefix_ttl}

                        {VoidPlus.ontology_prefix_ttl}
                        {VoidPlus.resource_prefix_ttl}
                        {VoidPlus.linkset_prefix_ttl}
                """) + '\n\n')
            else:
                buffer.write(cleandoc(F"""
                        {NS.RDF.prefix_ttl}
                        {VoidPlus.ontology_prefix_ttl}
                """) + '\n\n')

            for prefix, uri in prefix_mappings.items():
                if prefix not in predefined_prefix_mappings:
                    buffer.write(F"@prefix {prefix:>{20}}: {URIRef(uri).n3()} .\n")

            return buffer.getvalue()

        def namespaces_metadata_generator():
            yield rdf_namespaces_export()

            if export_metadata:
                yield self._rdf_metadata_export(prefix_mappings, link_pred_shortname, creator, publisher)

        link_pred = link_pred_shortname.split(':')
        predefined_prefix_mappings = self._get_predefined_prefix_mappings(export_metadata)
        prefix_mappings = self._determine_prefix_mappings(link_pred[0], link_pred_namespace,
                                                          export_metadata, export_linkset)

        if export_linkset:
            links_iter = self._job.get_links(self._id, self._type, validation_filter=validation_filter)
            return itertools.chain(
                namespaces_metadata_generator(),
                self._rdf_linkset_export_generator(links_iter, link_pred_namespace + link_pred[1], prefix_mappings,
                                                   reification, use_graphs))

        return namespaces_metadata_generator()

    def _get_predefined_prefix_mappings(self, export_metadata):
        return self._predefined_metadata_prefix_mappings.copy() \
            if export_metadata else self._predefined_export_only_prefix_mappings.copy()

    def _determine_prefix_mappings(self, link_pred_prefix, link_pred_uri, export_metadata, export_linkset):
        predefined_prefix_mappings = self._get_predefined_prefix_mappings(export_metadata)

        if export_metadata:
            for property in self._all_props:
                predefined_prefix_mappings = {**predefined_prefix_mappings, **property.prefix_mappings}

            # TODO: Better handling of matching method property value namespaces
            for method_info in flatten([[mm.method_info, mm.method_sim_info] for mm in self._matching_methods]):
                for prop_key in method_info.get('extra_properties', {}).keys():
                    predicate = method_info['extra_properties'][prop_key]['predicate']
                    if 'http://www.w3.org/2006/time#' in predicate and 'time' not in predefined_prefix_mappings:
                        predefined_prefix_mappings['time'] = 'http://www.w3.org/2006/time#'

            for transformer in self._all_transformers:
                if transformer['name'] == 'STOPWORDS':
                    if NS.DC.prefix not in predefined_prefix_mappings:
                        predefined_prefix_mappings[NS.DC.prefix] = NS.DC.dc
                    if NS.ISO.prefix not in predefined_prefix_mappings:
                        predefined_prefix_mappings[NS.ISO.prefix] = NS.ISO.iso

        if export_linkset:
            if link_pred_prefix not in predefined_prefix_mappings:
                predefined_prefix_mappings[link_pred_prefix] = link_pred_uri

            for ets in self._entity_type_selections:
                predefined_prefix_mappings = {**predefined_prefix_mappings, **ets.collection.uri_prefix_mappings}

        return predefined_prefix_mappings

    def _rdf_metadata_export(self, namespaces, link_pred_shortname, creator=None, publisher=None):
        def header(x):
            liner = "\n"
            return F"{liner * 2}{'#' * 80:^110}\n{' ' * 15}#{x:^78}#\n{'#' * 80:^110}{liner * 3}"

        def expression(root):
            def expression_generator(post_order):
                temporary, new = [], []
                for item in post_order:
                    if item.strip() \
                            and not item.strip().lower().startswith("and") \
                            and not item.strip().lower().startswith("or"):
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

        def tree(root):
            return F'\n    '.join([F"    %s%s" % (pre, node.name)
                                   for i, (pre, fill, node) in enumerate(RenderTree(root, style=DoubleStyle))])

        def generic_metadata():
            buffer.write(header('GENERIC METADATA'))

            for idx, linkset in enumerate(self._linksets):
                buffer.write(F"linkset:{self._job.job_id}-{linkset.id}\n")
                buffer.write(n3_pred_val('a', VoidPlus.Linkset_ttl))

                buffer.write(n3_pred_val(NS.VoID.feature_ttl, F"{NS.Formats.turtle_ttl}, {NS.Formats.triG_ttl}"))
                buffer.write(n3_pred_val(NS.CC.attributionName_ttl, Literal('Lenticular Lens', 'en').n3(ns_manager)))
                buffer.write(n3_pred_val(NS.CC.license_ttl,
                                         URIRef('http://purl.org/NET/rdflicense/W3C1.0').n3(ns_manager)))
                buffer.write(n3_pred_val(NS.DCterms.created_ttl,
                                         Literal(datetime.utcnow(), datatype=XSD.dateTime).n3(ns_manager)))

                if creator and len(creator.strip()) > 0:
                    buffer.write(n3_pred_val(NS.DCterms.creator_ttl, Literal(creator.strip()).n3(ns_manager)))
                if publisher and len(publisher.strip()) > 0:
                    buffer.write(n3_pred_val(NS.DCterms.creator_ttl, Literal(publisher.strip()).n3(ns_manager)))

                buffer.write(n3_pred_val(NS.VoID.linkPredicate_tt, link_pred_shortname))

                buffer.write(n3_pred_val(NS.RDFS.label_ttl, Literal(linkset.label).n3(ns_manager)))
                if linkset.description and len(linkset.description) > 0:
                    buffer.write(n3_pred_val(NS.DCterms.description_ttl, Literal(linkset.description).n3(ns_manager)))
                    buffer.write("\n")

                if self._stats[linkset.id].get('distinct_links_count', -1) > -1:
                    buffer.write(n3_pred_val(NS.VoID.triples_ttl, self._stats[linkset.id]['distinct_links_count']))

                if self._stats[linkset.id].get('distinct_linkset_sources_count', -1) > -1:
                    buffer.write(n3_pred_val(NS.VoID.distinctSubjects_ttl,
                                             self._stats[linkset.id]['distinct_linkset_sources_count']))

                if self._stats[linkset.id].get('distinct_linkset_targets_count', -1) > -1:
                    buffer.write(n3_pred_val(NS.VoID.distinctObjects_ttl,
                                             self._stats[linkset.id]['distinct_linkset_targets_count']))

                if self._clusterings[linkset.id].get('clusters_count', -1) > -1:
                    buffer.write(n3_pred_val(VoidPlus.cluster_ttl, self._clusterings[linkset.id]['clusters_count']))

                validations = self._totals[linkset.id].get('accepted', 0) + self._totals[linkset.id].get('rejected', 0)
                buffer.write(n3_pred_val(VoidPlus.validations_tt, validations))

                remains = self._totals[linkset.id].get('not_validated', 0)
                buffer.write(n3_pred_val(VoidPlus.remains_ttl, remains))

                contradictions = self._totals[linkset.id].get('mixed', 0)
                buffer.write(n3_pred_val(VoidPlus.contradictions_tt, contradictions))

                buffer.write("\n")
                buffer.write("".join(n3_pred_val(VoidPlus.subTarget_ttl,
                                                 F"resource:ResourceSelection-{self._job.job_id}-{selection.id}")
                                     for selection in linkset.sources))
                buffer.write("".join(n3_pred_val(VoidPlus.objTarget_ttl,
                                                 F"resource:ResourceSelection-{self._job.job_id}-{selection.id}")
                                     for selection in linkset.targets))

                buffer.write("\n")
                buffer.write(n3_pred_val(VoidPlus.formulation_ttl,
                                         F"resource:LinksetFormulation-{self._job.job_id}-{linkset.id}", end=True))

                if idx + 1 < len(self._linksets):
                    buffer.write("\n")

        def linkset_logic():
            def write_node(children_nodes, operator, fuzzy, threshold):
                logic_ops_info = self._logic_ops_info[fuzzy]
                fuzzy_txt = F"{logic_ops_info['label']} ({logic_ops_info['short']})"

                threshold_txt = (F"[with sim ≥ {threshold}]" if threshold < 1 else F"[with sim = 1]") \
                    if threshold > 0 else ''

                return Node(F"{operator} [{fuzzy_txt}] {threshold_txt}".strip(), children=children_nodes)

            buffer.write(header("LINKSET LOGIC EXPRESSION"))

            for idx, linkset in enumerate(self._linksets):
                root = linkset.with_matching_methods_recursive(
                    write_node,
                    lambda matching_method: Node(F"resource:{matching_method.method_name}-{matching_method.field_name}")
                )

                buffer.write(F"resource:LinksetFormulation-{self._job.job_id}-{linkset.id}\n")
                buffer.write(n3_pred_val('a', VoidPlus.LogicFormulation_ttl))

                for matching_method in linkset.matching_methods:
                    buffer.write(n3_pred_val(VoidPlus.part_ttl,
                                             F"resource:{matching_method.method_name}-{matching_method.field_name}"))
                buffer.write("\n")

                buffer.write(n3_pred_val(VoidPlus.formulaDescription_ttl, Literal(expression(root)).n3(ns_manager)))
                buffer.write("\n")

                buffer.write(n3_pred_val(VoidPlus.formulaTree_ttl,
                                         Literal(F"\n\t{tree(root)}\n\t").n3(ns_manager), end=True))

                if idx + 1 < len(self._linksets):
                    buffer.write("\n")

        def resource_selections():
            buffer.write(F"{header('RESOURCE SELECTIONS')}")

            for idx, selection in enumerate(sorted(self._entity_type_selections, key=lambda ets: ets.id)):
                root = selection.with_filters_recursive(
                    lambda children_nodes, type: Node(type, children=children_nodes),
                    lambda filter_func: Node(F"resource:PropertyPartition-{filter_func.hash}")
                )

                buffer.write(F"resource:ResourceSelection-{self._job.job_id}-{selection.id}\n")
                buffer.write(n3_pred_val('a', F"{NS.VoID.dataset_ttl}, {VoidPlus.EntitySelection_ttl}"))

                buffer.write(n3_pred_val(NS.RDFS.label_ttl, Literal(selection.label).n3(ns_manager)))
                if selection.description:
                    buffer.write(n3_pred_val(NS.DCterms.description_ttl, Literal(selection.description).n3(ns_manager)))

                buffer.write(n3_pred_val(VoidPlus.subset_of_ttl, F"resource:{selection.dataset_id}"))
                buffer.write(n3_pred_val(NS.DCterms.identifier_ttl,
                                         Literal(selection.collection.table_data['dataset_name']).n3(ns_manager)))
                buffer.write(n3_pred_val(VoidPlus.hasFormulation_ttl,
                                         F"resource:SelectionFormulation-{self._job.job_id}-{selection.id}", end=True))

                buffer.write(F"\nresource:ClassPartition-{self._job.job_id}-{selection.id}\n")
                buffer.write(n3_pred_val('a', F"{VoidPlus.ClassPartition_ttl}"))
                buffer.write(n3_pred_val(NS.VoID.voidClass_ttl,
                                         URIRef(selection.collection.table_data['collection_uri']).n3(ns_manager),
                                         end=True))

                buffer.write(F"\nresource:SelectionFormulation-{self._job.job_id}-{selection.id}\n")
                buffer.write(n3_pred_val('a', F"{VoidPlus.PartitionFormulation_ttl}"))
                buffer.write(n3_pred_val(VoidPlus.hasItem_ttl,
                                         F"resource:ClassPartition-{self._job.job_id}-{selection.id}",
                                         end=(not selection.filter_properties)))

                if not selection.filter_properties:
                    buffer.write("\n")

                for filter in selection.filters:
                    buffer.write(n3_pred_val(VoidPlus.hasItem_ttl, F"resource:PropertyPartition-{filter.hash}"))

                if root:
                    root.parent = Node("AND")
                    Node(F"resource:ClassPartition-{selection.id}", parent=root.parent)

                    buffer.write("\n")
                    buffer.write(n3_pred_val(VoidPlus.formulaDescription_ttl,
                                             Literal(expression(root.parent)).n3(ns_manager)))

                    buffer.write("\n")
                    buffer.write(n3_pred_val(VoidPlus.formulaTree_ttl,
                                             Literal(F"\n\t{tree(root.parent)}\n\t").n3(ns_manager), end=True))

                for filter in selection.filters:
                    buffer.write(F"\nresource:PropertyPartition-{filter.hash}\n")
                    buffer.write(n3_pred_val('a', F"{VoidPlus.PropertyPartition_ttl}"))
                    buffer.write(filter.property_field.n3(ns_manager))

                    buffer.write(n3_pred_val(VoidPlus.filterFunction_ttl, Literal(filter.function_name).n3(ns_manager),
                                             end=(not filter.value)))
                    if filter.value:
                        buffer.write(n3_pred_val(
                            VoidPlus.filterValue_ttl, Literal(filter.value).n3(ns_manager),
                            end=('format' not in filter.parameters)))
                    if 'format' in filter.parameters:
                        buffer.write(n3_pred_val(VoidPlus.filterFormat_ttl,
                                                 Literal(filter.parameters['format']).n3(ns_manager), end=True))

                if idx + 1 < len(self._entity_type_selections):
                    buffer.write("\n")

        def methods_signatures():
            def write_algorithm(method_config, method_info, tabs=1):
                if method_info['threshold_range'] == ']0, 1]':
                    buffer.write(n3_pred_val(VoidPlus.simThreshold_ttl,
                                             Literal(method_config['threshold']).n3(ns_manager), tabs=tabs))
                buffer.write(n3_pred_val(VoidPlus.thresholdRange_ttl,
                                         Literal(method_info['threshold_range']).n3(ns_manager), tabs=tabs))

                for prop_key in method_info.get('extra_properties', {}).keys():
                    predicate = method_info['extra_properties'][prop_key]['predicate']

                    value = method_config[prop_key]
                    if 'values' in method_info['extra_properties'][prop_key]:
                        value = method_info['extra_properties'][prop_key]['values'][value]

                    # TODO: Better uri and namespace handling
                    if isinstance(value, list):
                        is_uri = isinstance(value[0], str) and value[0].startswith('http')
                        buffer.write(n3_pred_val(
                            URIRef(predicate).n3(ns_manager),
                            ', '.join([URIRef(v).n3(ns_manager)
                                       if is_uri else Literal(v).n3(ns_manager) for v in value]),
                            tabs=tabs))
                    else:
                        is_uri = isinstance(value, str) and value.startswith('http')
                        buffer.write(n3_pred_val(
                            URIRef(predicate).n3(ns_manager),
                            URIRef(value).n3(ns_manager) if is_uri else Literal(value).n3(ns_manager),
                            tabs=tabs))

            buffer.write(header('METHOD SIGNATURES'))

            has_list_matching_absolute, has_list_matching_relative = False, False
            for idx, matching_method in enumerate(self._matching_methods):
                buffer.write(F"resource:{matching_method.method_name}-{matching_method.field_name}\n")
                buffer.write(n3_pred_val('a', VoidPlus.MatchingMethod_ttl))

                if matching_method.method_sim_name:
                    buffer.write(n3_pred_val(VoidPlus.methodSequence_ttl,
                                             F"resource:AlgorithmSequence-{matching_method.field_name}"))
                else:
                    buffer.write(n3_pred_val(VoidPlus.method_ttl, F"resource:{matching_method.method_name}"))

                if matching_method.threshold:
                    buffer.write(n3_pred_val(VoidPlus.combiThreshold_ttl,
                                             Literal(matching_method.threshold).n3(ns_manager)))
                    buffer.write(n3_pred_val(VoidPlus.combiThresholdRange_ttl, Literal("]0, 1]").n3(ns_manager)))

                if not matching_method.method_sim_name:
                    write_algorithm(matching_method.method_config, matching_method.method_info)

                buffer.write("\n")
                if matching_method.is_list_match:
                    if matching_method.list_is_percentage:
                        has_list_matching_relative = True
                    else:
                        has_list_matching_absolute = True

                    buffer.write(F"    voidPlus:hasListConfiguration\n        [\n")
                    buffer.write(n3_pred_val(
                        F"        voidPlus:listThreshold", Literal(matching_method.list_threshold).n3(ns_manager)))
                    buffer.write(n3_pred_val(
                        F"        voidPlus:appreciation", "resource:" + (
                            "RelativeCount" if matching_method.list_is_percentage else "AbsoluteCount")))
                    buffer.write(F"        ] ;\n")

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

                buffer.write(n3_pred_val(VoidPlus.entitySelectionSubj_ttl, sources_ref))
                buffer.write(n3_pred_val(VoidPlus.entitySelectionObj_ttl, targets_ref,
                                         end=(not matching_method.is_intermediate)))

                if matching_method.is_intermediate:
                    props_source = {prop.prop_original for ets, props_ets in matching_method.intermediates.items()
                                    for prop in props_ets['source']}
                    props_target = {prop.prop_original for ets, props_ets in matching_method.intermediates.items()
                                    for prop in props_ets['target']}

                    props = props_source.union(props_target)
                    for idx, property in enumerate(props):
                        buffer.write(n3_pred_val(VoidPlus.intermediateEntitySelection_ttl,
                                                 F"resource:ResourcePartition-{property.hash}",
                                                 end=(idx + 1 == len(props))))

                if matching_method.method_sim_name:
                    buffer.write(F"\nresource:AlgorithmSequence-{matching_method.field_name}\n")
                    buffer.write(n3_pred_val('a', NS.RDFS.sequence_ttl))

                    buffer.write("\n    rdf:_1\n        [\n")
                    buffer.write(n3_pred_val(VoidPlus.method_ttl,
                                             F"resource:{matching_method.method_name}", tabs=3))
                    write_algorithm(matching_method.method_config, matching_method.method_info, tabs=3)
                    buffer.write("        ] ;\n")

                    buffer.write("\n    rdf:_2\n        [\n")
                    buffer.write(n3_pred_val(VoidPlus.method_ttl,
                                             F"resource:{matching_method.method_sim_name}", tabs=3))
                    buffer.write(n3_pred_val(VoidPlus.normalized_ttl,
                                             Literal(matching_method.method_sim_normalized).n3(ns_manager), tabs=3))
                    write_algorithm(matching_method.method_sim_config, matching_method.method_sim_info, tabs=3)
                    buffer.write("        ] .\n")

                if idx + 1 < len(self._matching_methods):
                    buffer.write("\n")

            if has_list_matching_absolute:
                buffer.write("\nresource:AbsoluteCount\n")
                buffer.write(n3_pred_val(
                    NS.DCterms.description_ttl,
                    Literal("Establishes a link between the source and target when the absolute threshold is reached.",
                            lang='en').n3(ns_manager), end=True))

            if has_list_matching_relative:
                buffer.write("\nresource:RelativeCount\n")
                buffer.write(n3_pred_val(
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
                    buffer.write(n3_pred_val(VoidPlus.stopWords_ttl, uri, tabs=tabs))
                    stopwords_selected[uri] = (stopwords, get_iso_639_1_code(language))

                    if additional:
                        uri = F"resource:StopwordsList-{hash_string_min(additional)}"
                        buffer.write(n3_pred_val(VoidPlus.stopWords_ttl, uri, tabs=tabs))
                        stopwords_selected[uri] = (additional, None)
                else:
                    buffer.write(n3_pred_val(VoidPlus.tranformationFunction_ttl,
                                             Literal(transformer['name']).n3(ns_manager), tabs=tabs))

            buffer.write(header("METHODS'S PREDICATE SELECTIONS"))

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
                        buffer.write(n3_pred_val('a', VoidPlus.EntitySelection_ttl))
                        buffer.write(n3_pred_val(VoidPlus.hasFormulation_ttl,
                                                 F"resource:PartitionFormulation-{id}", end=True))

                        buffer.write(F"\nresource:PartitionFormulation-{id}\n")
                        buffer.write(n3_pred_val('a', VoidPlus.PartitionFormulation_ttl))

                        for transformer in transformers:
                            write_transformer(transformer)

                        for (idx, matching_method_prop) in enumerate(flatten(list(matching_method_props.values()))):
                            property = matching_method_prop.prop_original
                            buffer.write(n3_pred_val(VoidPlus.part_ttl, F"resource:PropertyPartition-{property.hash}",
                                                     end=(not has_multiple_props)))
                            Node(F"resource:PropertyPartition-{property.hash}", parent=root)

                        if has_multiple_props:
                            buffer.write(n3_pred_val(VoidPlus.formulaDescription_ttl,
                                                     Literal(expression(root)).n3(ns_manager)))
                            buffer.write(n3_pred_val(VoidPlus.formulaTree_ttl,
                                                     Literal(F"\n\t{tree(root)}\n\t").n3(ns_manager), end=True))

                        buffer.write("\n")

            for idx, (ets, matching_method_prop) in enumerate(self._matching_methods_props):
                property = matching_method_prop.prop_original

                buffer.write(F"resource:PropertyPartition-{property.hash}\n")
                buffer.write(n3_pred_val('a', VoidPlus.PropertyPartition_ttl))
                buffer.write(n3_pred_val(VoidPlus.subset_of_ttl, F"resource:ResourceSelection-{ets}"))

                for transformer in matching_method_prop.property_transformers:
                    write_transformer(transformer)

                buffer.write(property.n3(ns_manager, end=True))

                if len(stopwords_selected) or idx + 1 < len(self._matching_methods_props):
                    buffer.write("\n")

            for idx, (uri, (stopwords, language_code)) in enumerate(list(stopwords_selected.items())):
                buffer.write(F"{uri}\n")
                if language_code:
                    buffer.write(n3_pred_val(NS.DC.language_ttl, F"{NS.ISO.prefix}:{language_code}"))

                new = '\n        '
                buffer.write(n3_pred_val(VoidPlus.stopWordsList_ttl,
                                         F", ".join(F"{new if i % 10 == 0 else ''}{Literal(word).n3(ns_manager)}"
                                                    for i, word in enumerate(stopwords)), end=True))

                if idx + 1 < len(stopwords_selected):
                    buffer.write("\n")

        def methods_descriptions():
            buffer.write(header("METHODS'S DESCRIPTION"))

            method_infos = {matching_method.method_name for matching_method in self._matching_methods}
            for idx, method_name in enumerate(method_infos):
                method_info = self._matching_methods_info[method_name]

                buffer.write(F"resource:MatchingAlgorithm-{method_name}\n")
                buffer.write(n3_pred_val('a', VoidPlus.MatchingAlgorithm_ttl))
                buffer.write(n3_pred_val(NS.RDFS.label_ttl, Literal(method_info['label'], lang='en').n3(ns_manager)))
                buffer.write(n3_pred_val(NS.DCterms.description_ttl,
                                         Literal(method_info['description'], lang='en').n3(ns_manager), end=True))

                if idx + 1 < len(method_infos):
                    buffer.write("\n")

        def validation_terminology():
            buffer.write(header("VALIDATION TERMINOLOGY"))

            for idx, validation_state_info in enumerate(list(self._validation_states_info.values())):
                buffer.write(F"{validation_state_info['predicate']}\n")
                buffer.write(n3_pred_val(NS.RDFS.label_ttl,
                                         Literal(validation_state_info['label'], lang='en').n3(ns_manager)))
                buffer.write(n3_pred_val(NS.DCterms.description_ttl,
                                         Literal(validation_state_info['description'], lang='en').n3(ns_manager),
                                         end=True))

                if idx + 1 < len(self._validation_states_info.values()):
                    buffer.write("\n")

        buffer = io.StringIO()
        ns_manager = self._get_namespace_manager(namespaces)

        generic_metadata()
        linkset_logic()
        resource_selections()
        methods_signatures()
        methods_predicate_selections()
        methods_descriptions()
        validation_terminology()

        return buffer.getvalue()

    def _rdf_linkset_export_generator(self, links_iter, link_predicate, namespaces,
                                      reification='none', use_graphs=True):
        buffer = io.StringIO()
        ns_manager = self._get_namespace_manager(namespaces)

        buffer.write(F"\n\n{'#' * 110}\n#{'ANNOTATED LINKSET':^108}#\n{'#' * 110}\n\n\n")
        if use_graphs:
            buffer.write(F"linkset:{self._job.job_id}-{self._id}\n{{\n")

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

            link_rdf = F"{source_uri}    {predicate}    {target_uri}"
            if reification == 'rdf_star':
                buffer.write(F"{'    ' if use_graphs else ''}<<{link_rdf}>>\n")
            else:
                buffer.write(F"{'    ' if use_graphs else ''}{link_rdf} .\n")

            if reification != 'none':
                if reification == 'standard':
                    buffer.write(F"\n{'    ' if use_graphs else ''}resource:Reification-{hash}\n")
                    buffer.write(n3_pred_val('a', 'rdf:Statement', tabs=tabs))
                    buffer.write(n3_pred_val('rdf:predicate', predicate, tabs=tabs))
                    buffer.write(n3_pred_val('rdf:subject', source_uri, tabs=tabs))
                    buffer.write(n3_pred_val('rdf:object', target_uri, tabs=tabs))
                elif reification == 'singleton':
                    buffer.write(F"\n{'    ' if use_graphs else ''}{predicate}\n")
                    buffer.write(n3_pred_val('rdf:singletonPropertyOf', rdf_predicate, tabs=tabs))

                strength = round(link['similarity'], 5) if link['similarity'] else 1
                buffer.write(n3_pred_val(VoidPlus.strength_ttl, strength, tabs=tabs))

                validation_info = self._validation_states_info[link['valid']]
                buffer.write(n3_pred_val(VoidPlus.link_validation_tt, validation_info['predicate'],
                                         tabs=tabs, end=(not link['cluster_id'])))

                if link['cluster_id']:
                    buffer.write(n3_pred_val(VoidPlus.cluster_ID_ttl, Literal(link['cluster_id']).n3(ns_manager),
                                             tabs=tabs, end=True))

            buffer.write("\n")

            i += 1
            if i > 1000:
                i = 0
                yield self._get_from_buffer(buffer)

        if use_graphs:
            buffer.write('}')

        yield buffer.getvalue()

    @staticmethod
    def _get_namespace_manager(ns):
        namespace_manager = NamespaceManager(Graph())
        for prefix, uri in ns.items():
            namespace_manager.bind(prefix, uri)

        return namespace_manager

    @staticmethod
    def _get_from_buffer(buffer):
        buffer.seek(0)
        text = buffer.read()

        buffer.truncate(0)
        buffer.seek(0)

        return text
