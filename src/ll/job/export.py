import csv
import io
import itertools

from inspect import cleandoc
from datetime import datetime

from rdflib import Literal, URIRef, XSD, Graph
from rdflib.namespace import NamespaceManager
from anytree import Node, RenderTree, DoubleStyle, PostOrderIter

from ll.job.validation import Validation

from ll.namespaces.ll_namespace import LLNamespace as LL
from ll.namespaces.shared_ontologies import Namespaces as NS

from ll.util.hasher import hash_string_min
from ll.util.helpers import n3_pred_val, get_json_from_file, get_id_of_uri


class Export:
    _matching_methods_info = get_json_from_file('matching_methods.json')
    _predefined_metadata_prefix_mappings = {
        NS.RDF.prefix: str(NS.RDF.rdf),
        NS.RDFS.prefix: str(NS.RDFS.rdfs),
        NS.VoID.prefix: str(NS.VoID.void),
        NS.DCterms.prefix: str(NS.DCterms.dcterms),
        NS.Formats.prefix: str(NS.Formats.formats),
        NS.CC.prefix: str(NS.CC.cc),
        NS.XSD.prefix: str(NS.XSD.xsd),
    }
    _predefined_export_only_prefix_mappings = {
        NS.RDF.prefix: str(NS.RDF.rdf)
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
        self._matching_methods_source_props = {prop.prop_original
                                               for matching_method in self._matching_methods
                                               for ets, props_ets in matching_method.sources.items()
                                               for prop in props_ets}
        self._matching_methods_target_props = {prop.prop_original
                                               for matching_method in self._matching_methods
                                               for ets, props_ets in matching_method.targets.items()
                                               for prop in props_ets}
        self._matching_methods_props = self._matching_methods_source_props.union(self._matching_methods_target_props)
        self._all_props = self._filter_props.union(self._matching_methods_props)

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
                             export_metadata=True, export_link_metadata=True, export_linkset=True,
                             rdf_star=False, use_graphs=True, creator=None, publisher=None,
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

                        {LL.ontology_prefix}
                        {LL.resource_prefix}
                        {LL.linkset_prefix}
                """) + '\n\n')
            else:
                buffer.write(cleandoc(F"""
                        {NS.RDF.prefix_ttl}
                        {LL.ontology_prefix}
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
                                                          export_metadata, export_link_metadata, export_linkset)

        if export_linkset:
            links_iter = self._job.get_links(self._id, self._type, validation_filter=validation_filter)
            return itertools.chain(
                namespaces_metadata_generator(),
                self._rdf_linkset_export_generator(links_iter, link_pred_shortname, prefix_mappings,
                                                   export_link_metadata, rdf_star, use_graphs))

        return namespaces_metadata_generator()

    def _get_predefined_prefix_mappings(self, export_metadata):
        return self._predefined_metadata_prefix_mappings.copy() \
            if export_metadata else self._predefined_export_only_prefix_mappings.copy()

    def _determine_prefix_mappings(self, link_pred_prefix, link_pred_uri,
                                   export_metadata, export_link_metadata, export_linkset):
        predefined_prefix_mappings = self._get_predefined_prefix_mappings(export_metadata)

        if export_metadata:
            for property in self._all_props:
                predefined_prefix_mappings = {**predefined_prefix_mappings, **property.prefix_mappings}

        if export_link_metadata:
            if link_pred_prefix not in predefined_prefix_mappings:
                predefined_prefix_mappings[link_pred_prefix] = link_pred_uri

        if export_linkset:
            for ets in self._entity_type_selections:
                predefined_prefix_mappings = {**predefined_prefix_mappings, **ets.collection.uri_prefix_mappings}

        return predefined_prefix_mappings

    def _rdf_metadata_export(self, namespaces, link_pred_shortname, creator=None, publisher=None):
        def header(x):
            liner = "\n"
            return F"{liner * 2}{'#' * 80:^110}\n{' ' * 15}#{x:^78}#\n{'#' * 80:^110}{liner * 3}"

        def expression_generator(post_order):
            def r_expression_generator(post_order):
                temporary = []
                new = []

                for item in post_order:
                    if item.lower() not in ['and', 'or']:
                        temporary.append(item)
                    elif len(temporary) > 1:
                        new.append(F'( {F" {item.upper()} ".join(temporary)} )')
                        temporary.clear()
                    elif len(temporary) == 1:
                        new = [F'( {F" {item.upper()} ".join(new + temporary)} )']
                        temporary.clear()
                    else:
                        new.append(item)

                if len(new) > 1:
                    new = r_expression_generator(new)

                return new

            return r_expression_generator(post_order)[0]

        def generic_metadata():
            buffer.write(header('GENERIC METADATA'))

            for linkset in self._linksets:
                buffer.write(F"linkset:{linkset.id}\n")
                buffer.write(n3_pred_val('a', LL.Linkset_ttl))

                buffer.write(n3_pred_val(NS.VoID.feature_ttl, NS.Formats.turtle_ttl))
                buffer.write(n3_pred_val(NS.CC.attributionName_ttl, Literal('Lenticular Lenses', 'en').n3(ns_manager)))
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
                    buffer.write(n3_pred_val(LL.cluster_ttl, self._clusterings[linkset.id]['clusters_count']))

                validations = self._totals[linkset.id].get('accepted', 0) + self._totals[linkset.id].get('rejected', 0)
                buffer.write(n3_pred_val(LL.validations_tt, validations))

                remains = self._totals[linkset.id].get('not_validated', 0)
                buffer.write(n3_pred_val(LL.remains_ttl, remains))

                contradictions = self._totals[linkset.id].get('mixed', 0)
                buffer.write(n3_pred_val(LL.contradictions_tt, contradictions))

                buffer.write("\n")
                buffer.write("".join(n3_pred_val(LL.subTarget_ttl, F"resource:ResourceSelection-{selection.id}")
                                     for selection in linkset.sources))
                buffer.write("".join(n3_pred_val(LL.subTarget_ttl, F"resource:ResourceSelection-{selection.id}")
                                     for selection in linkset.targets))

                buffer.write("\n")
                buffer.write(n3_pred_val(LL.formulation_ttl, F"resource:LogicFormulation-{linkset.id}", end=True))

        def resource_selections():
            buffer.write(F"{header('RESOURCE SELECTIONS')}")

            for selection in self._entity_type_selections:
                root = selection.with_filters_recursive(
                    lambda children_nodes, type: Node(type, children=children_nodes),
                    lambda filter_func: Node(F"resource:PropertyPartition-{filter_func.property_field.hash}")
                )

                buffer.write(F"resource:{selection.id}\n")
                buffer.write(n3_pred_val('a', F"{NS.VoID.dataset_ttl}, {LL.EntitySelection_ttl}"))

                buffer.write(n3_pred_val(NS.RDFS.label_ttl, Literal(selection.label).n3(ns_manager)))
                if len(selection.description) > 0:
                    buffer.write(n3_pred_val(NS.DCterms.description_ttl, Literal(selection.description).n3(ns_manager)))

                buffer.write(n3_pred_val(LL.subset_of_ttl, F"resource:{selection.dataset_id}"))
                buffer.write(n3_pred_val(NS.DCterms.identifier_ttl, selection.collection.table_data['dataset_name']))
                buffer.write(
                    n3_pred_val(LL.hasFormulation_ttl, F"resource:PartitionFormulation-{selection.id}", end=True))

                buffer.write(F"\nresource:ClassPartition-{selection.id}\n")
                buffer.write(n3_pred_val('a', F"{LL.ClassPartition_ttl}"))
                buffer.write(n3_pred_val(NS.VoID.voidClass_ttl,
                                         selection.collection.table_data['collection_shortened_uri'], end=True))

                buffer.write(F"\nresource:PartitionFormulation-{selection.id}\n")
                buffer.write(n3_pred_val('a', F"{LL.PartitionFormulation_ttl}"))
                buffer.write(n3_pred_val(LL.hasItem_ttl, F"resource:ClassPartition-{selection.id}",
                                         end=(not selection.filter_properties)))

                for filter in selection.filters:
                    buffer.write(
                        n3_pred_val(LL.hasItem_ttl, F"resource:PropertyPartition-{filter.property_field.hash}"))

                if root:
                    expression = expression_generator(node.name for node in PostOrderIter(root))

                    buffer.write("\n")
                    buffer.write(n3_pred_val(LL.formulaDescription_ttl,
                                             Literal(F"resource:ClassPartition-{selection.id} AND {expression}").n3(
                                                 ns_manager)))

                    root.parent = Node("AND")
                    Node(F"resource:ClassPartition-{selection.id}", parent=root.parent)

                    f_tree = '\n\t'.join("%s%s" % (pre, node.name)
                                         for pre, fill, node in RenderTree(root.parent, style=DoubleStyle))

                    buffer.write("\n")
                    buffer.write(n3_pred_val(LL.formulaTree_ttl, Literal(F"\n\t{f_tree}").n3(ns_manager), end=True))

                for filter in selection.filters:
                    buffer.write(F"resource:PropertyPartition-{filter.property_field.hash}\n\n")
                    buffer.write(n3_pred_val('a', F"{LL.PropertyPartition_ttl}"))
                    buffer.write(filter.property_field.n3)

                    buffer.write(n3_pred_val(LL.filterFunction_ttl, Literal(filter.function_name).n3(ns_manager)))
                    if filter.value:
                        buffer.write(n3_pred_val(
                            LL.filterValue_ttl, Literal(filter.value).n3(ns_manager)
                            if type(filter.value) == 'str' else filter.value))

        def linkset_logic():
            buffer.write(header("LINKSET LOGIC EXPRESSIONS"))

            for linkset in self._linksets:
                root = linkset.with_matching_methods_recursive(
                    lambda children_nodes, operator, fuzzy: Node(operator, children=children_nodes),
                    lambda matching_method: Node(F"resource:MatchingMethod-{matching_method.field_name}")
                )

                buffer.write(F"resource:LogicFormulation-{linkset.id}\n")
                buffer.write(n3_pred_val('a', LL.LogicFormulation_ttl))

                for matching_method in linkset.matching_methods:
                    buffer.write(n3_pred_val(LL.part_ttl, F"resource:MatchingMethod-{matching_method.field_name}"))

                buffer.write("\n")
                expression = expression_generator(node.name for node in PostOrderIter(root))
                buffer.write(n3_pred_val(LL.formulaDescription_ttl, Literal(expression).n3(ns_manager)))
                buffer.write("\n")

                f_tree = '\n\t'.join("%s%s" % (pre, node.name)
                                     for pre, fill, node in RenderTree(root, style=DoubleStyle))
                buffer.write(n3_pred_val(LL.formulaTree_ttl, Literal(F"\n\t{f_tree}").n3(ns_manager), end=True))

        def methods_signatures():
            buffer.write(header('METHOD SIGNATURES'))

            for matching_method in self._matching_methods:
                buffer.write(F"resource:MatchingMethod-{matching_method.field_name}\n")
                buffer.write(n3_pred_val('a', LL.MatchingMethod_ttl))

                buffer.write(n3_pred_val(LL.method_ttl,
                                         F"resource:MatchingAlgorithm-{matching_method.method_name.lower()}"))
                if matching_method.method_sim_name:
                    buffer.write(n3_pred_val(LL.method_ttl,
                                             F"resource:MatchingAlgorithm-{matching_method.method_sim_name.lower()}"))
                buffer.write("\n")

                for is_source in (True, False):
                    predicate_type = LL.entitySelectionSubj_ttl if is_source else LL.entitySelectionObj_ttl
                    match_props = matching_method.sources if is_source else matching_method.targets

                    props = {prop.prop_original for ets, props_ets in match_props.items() for prop in props_ets}
                    for (idx, property) in enumerate(props):
                        buffer.write(n3_pred_val(predicate_type, F"resource:ResourceSelection-{property.hash}",
                                                 end=(not is_source and idx == len(props) - 1)))

        def methods_descriptions():
            buffer.write(header("METHODS'S DESCRIPTION"))

            method_infos = {matching_method.method_name for matching_method in self._matching_methods}
            for method_name in method_infos:
                method_info = self._matching_methods_info[method_name]

                buffer.write(F"resource:MatchingAlgorithm-{method_name.lower()}\n")
                buffer.write(n3_pred_val('a', LL.MatchingAlgorithm_ttl))
                buffer.write(n3_pred_val(NS.RDFS.label_ttl, Literal(method_info['label'], lang='en').n3(ns_manager)))
                buffer.write(n3_pred_val(NS.DCterms.description_ttl,
                                         Literal(method_info['description'], lang='en').n3(ns_manager)))
                buffer.write(n3_pred_val(LL.thresholdRange_ttl, method_info['threshold_range'], end=True))

        def methods_predicate_selections():
            buffer.write(header("METHODS'S PREDICATE SELECTIONS"))

            for property in self._matching_methods_props:
                buffer.write(F'resource:ResourceSelection-{property.hash}\n')
                buffer.write(n3_pred_val('a', LL.EntitySelection_ttl))
                buffer.write(n3_pred_val(LL.subset_of_ttl, F"resource:ResourceSelection-{property.ets.id}"))
                buffer.write(
                    n3_pred_val(LL.hasFormulation_ttl, F"resource:PartitionFormulation-{property.hash}", end=True))

                buffer.write(F"\nresource:PartitionFormulation-{property.hash}\n")
                buffer.write(n3_pred_val('a', F"{LL.PartitionFormulation_ttl}"))
                buffer.write(n3_pred_val(LL.hasItem_ttl, F"resource:PropertyPartition-{property.hash}", end=True))

                buffer.write(F"\nresource:PropertyPartition-{property.hash}\n")
                buffer.write(n3_pred_val('a', F"{LL.PropertyPartition_ttl}"))
                buffer.write(property.n3(end=True))

        buffer = io.StringIO()
        ns_manager = self._get_namespace_manager(namespaces)

        generic_metadata()
        resource_selections()
        linkset_logic()
        methods_signatures()
        methods_descriptions()
        methods_predicate_selections()

        return buffer.getvalue()

    def _rdf_linkset_export_generator(self, links_iter, link_pred_shortname, namespaces,
                                      export_link_metadata=True, rdf_star=False, use_graphs=True):
        buffer = io.StringIO()

        buffer.write(F"\n\n{'#' * 110}\n#{'ANNOTATED LINKSET':^108}#\n{'#' * 110}\n\n\n")
        if use_graphs:
            buffer.write(F"linkset:{self._id}\n{{\n")

        i = 0
        for link in links_iter:
            source_uri = link['source'] if link['link_order'] != 'target_source' else link['target']
            target_uri = link['target'] if link['link_order'] != 'target_source' else link['source']

            shortened_source_uri = source_uri
            shortened_target_uri = target_uri
            for prefix, uri in namespaces.items():
                if source_uri.startswith(uri):
                    shortened_source_uri = F"{prefix}:{source_uri.replace(uri, '')}"
                if target_uri.startswith(uri):
                    shortened_target_uri = F"{prefix}:{target_uri.replace(uri, '')}"

            if export_link_metadata and rdf_star:
                buffer.write(F"\t<<{shortened_source_uri}    {link_pred_shortname}    {shortened_target_uri}>>\n")
            else:
                end = ';' if not export_link_metadata and rdf_star else '.'
                buffer.write(F"\t{shortened_source_uri}    {link_pred_shortname}    {shortened_target_uri} {end}\n")

                if not rdf_star:
                    buffer.write(
                        F"\n\tresource:Reification-{hash_string_min((shortened_source_uri, shortened_target_uri))}\n")
                    buffer.write(F"\t{n3_pred_val('a', 'rdf:Statement')}")
                    buffer.write(F"\t{n3_pred_val('rdf:predicate', link_pred_shortname)}")
                    buffer.write(F"\t{n3_pred_val('rdf:subject', shortened_source_uri)}")
                    buffer.write(F"\t{n3_pred_val('rdf:object', shortened_target_uri, end=(not export_link_metadata))}")

            if export_link_metadata:
                strength = round(link['similarity'], 5) if link['similarity'] else 1
                buffer.write(F"\t{n3_pred_val(LL.strength_ttl, strength)}")

                if link['cluster_id']:
                    buffer.write(F"\t{n3_pred_val(LL.cluster_ID_ttl, link['cluster_id'])}")

                buffer.write(F"\t{n3_pred_val(LL.link_validation_tt, link['valid'], end=True)}")

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
