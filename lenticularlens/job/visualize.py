from copy import deepcopy
from collections import defaultdict

from lenticularlens.util.hasher import hash_string_min
from lenticularlens.util.helpers import get_id_of_uri

short_distance = 350
related_distance = 550


def get_visualization(job, id, type, cluster_id, associations=None, include_compact=False):
    def create_key(id1, id2):
        return hash_string_min((id1, id2) if id1 < id2 else (id2, id1))

    def create_node(id, group, label=None, dataset=None, entity=None, local_id=None, size=8, group_size=None,
                    investigated=True, strength=None, satellite=False, missing_links=None, org_node=None):
        new_node = {k: v for k, v in {
            'id': id,
            'dataset': dataset,
            'entity': entity,
            'local_id': local_id,
            'label': label,
            'group': group,
            'size': size,
            'nodes': group_size,
            'investigated': investigated,
            'strength': strength,
            'satellite': satellite,
            'missing_links': missing_links
        }.items() if v is not None}

        if org_node:
            return {**org_node, **new_node}

        return new_node

    def create_link(source, target, strength=None, is_association=False, dist_factor=None, count=1, link_thickness=2):
        return {k: v for k, v in {
            'source': source,
            'target': target,
            'strength': strength,
            'distance': short_distance,
            'dist_factor': dist_factor,
            'count': count,
            'value': 4 if count == 1 else count * link_thickness,
            'color': 'purple' if is_association else ('black' if strength == 1 else 'red'),
            'dash': '20,10,5,5,5,10' if is_association else F"3,{(20 * (1 - strength)):.3f}"
        }.items() if v is not None}

    def get_compact():
        def update_inter_link(delete=None):
            if delete is None:
                inter_key = create_key(new_root[link['source']], new_root[link['target']])
                if inter_key not in inter_links:
                    inter_links[inter_key] = [new_root[link['source']], new_root[link['target']], link['strength'], 1]
                else:
                    inter_links[inter_key][3] += 1
                    if inter_links[inter_key][2] < link['strength']:
                        inter_links[inter_key][2] = link['strength']
            else:
                to_del = set()
                for del_k, del_item in inter_links.items():
                    if delete in del_item:
                        to_del.add(del_k)

                for deletion_key in to_del:
                    del_item = inter_links[deletion_key]
                    new_group = new_root[list(new_clusters[delete])[0]]

                    is_source = (delete == del_item[0])
                    if is_source:
                        del_item[0] = new_group
                    else:
                        del_item[1] = new_group

                    new_key = create_key(new_group, del_item[1]) if is_source else create_key(del_item[0], new_group)
                    if new_key not in inter_links:
                        inter_links[new_key] = del_item
                    else:
                        inter_links[new_key][3] += del_item[3]
                        if inter_links[new_key][2] < del_item[2]:
                            inter_links[new_key][2] = del_item[2]

                    del inter_links[deletion_key]

        def increase_sub_cluster_link_count(key, additional=0):
            if key in sub_cluster_link_count:
                sub_cluster_link_count[key] += 1 + additional
            else:
                sub_cluster_link_count[key] = 1 + additional

        def vis_community(vis, reducer=1, children=None):
            def swallow(complex=False, parent=None):
                if len(vis['links']) == 0:
                    return

                if complex:
                    biggest_list = []
                    for arc in vis['links']:
                        if child == arc['source'] or child == arc['target']:
                            id = arc['target'] if arc['source'] == child else arc['source']

                            if len(biggest_list) == 0 or biggest_list[0][1] < arc['strength']:
                                biggest_list = [(id, arc['strength'])]
                            elif biggest_list[0][1] == arc['strength']:
                                biggest_list += [(id, arc['strength'])]

                    biggest_parent = None
                    for cid, strength in biggest_list:
                        if biggest_parent is None:
                            biggest_parent = cid
                        elif nodes[biggest_parent]['nodes'] <= nodes[cid]['nodes']:
                            biggest_parent = cid

                    if biggest_parent is None:
                        return

                    parent = biggest_parent
                    nodes[parent]['satellite'] = True

                if parent not in visited_parent:
                    visited_parent.add(parent)
                    nodes[parent]['child'] = {'nodes': [deepcopy(nodes[parent])], 'links': []}
                    nodes[parent]['satellite'] = True

                pairs = nodes[parent]['nodes'] * (nodes[parent]['nodes'] - 1) / 2
                curr_link_count = round(pairs * (1 - nodes[parent]['missing_links']))

                nodes[parent]['nodes'] += nodes[child]['nodes']
                pairs = nodes[parent]['nodes'] * (nodes[parent]['nodes'] - 1) / 2

                removals = []
                for counter, arc in enumerate(vis['links']):
                    src_id, trg_id = arc['source'], arc['target']
                    if src_id == child or trg_id == child:
                        link_count[parent] = arc['count'] if arc['count'] > 0 else 1

                        if nodes[child] not in nodes[parent]['child']['nodes']:
                            nodes[parent]['child']['nodes'] += [nodes[child]]

                        if nodes[child] in vis['nodes']:
                            vis['nodes'].remove(nodes[child])
                            if not complex:
                                removals.append(counter)

                        if complex:
                            removals.append(counter)

                if nodes[child]['nodes'] > 1:
                    child_pairs = nodes[child]['nodes'] * (nodes[child]['nodes'] - 1) / 2
                    child_curr_link_count = round(child_pairs * (1 - nodes[child]['missing_links']))
                    link_count[parent] += child_curr_link_count

                if complex:
                    removals = sorted(removals, reverse=True)

                for remove_idx in removals:
                    source, target = vis['links'][remove_idx]['source'], vis['links'][remove_idx]['target']

                    if not complex or source == parent or target == parent:
                        nodes[parent]['child']['links'] += [vis['links'][remove_idx]]
                        del vis['links'][remove_idx]
                    else:
                        check = False

                        source_is_child = source == child
                        other_child = target if source_is_child else source

                        for inter_link in vis['links']:
                            inter_source, inter_target = inter_link['source'], inter_link['target']

                            if inter_source in [parent, other_child] and inter_target in [parent, other_child]:
                                inter_link['count'] += vis['links'][remove_idx]['count']
                                check = True
                                del vis['links'][remove_idx]

                        if check is False:
                            vis['links'][remove_idx]['source' if source_is_child else 'target'] = parent

                nodes[parent]['missing_links'] = (pairs - (curr_link_count + link_count[parent])) / float(pairs)

            if children is None:
                children = defaultdict(list)
            else:
                children.clear()

            max = 0
            visited_parent = set()
            link_count = defaultdict(int)

            if len(vis['links']) == 0:
                return vis

            nodes = dict()
            for node in vis['nodes']:
                nodes[node['id']] = node
                if 'nodes' in node and max < node['nodes']:
                    max = node['nodes']

            if reducer and reducer >= max:
                reducer = max - 5

            parents = defaultdict(list)
            for arc in vis['links']:
                source, target = arc['source'], arc['target']

                if 'nodes' in nodes[source] and nodes[source]['nodes'] > nodes[target]['nodes']:
                    if nodes[target]['nodes'] <= reducer:
                        parents[source].append(target)
                        children[target].append(source)
                elif 'nodes' in nodes[source] and nodes[source]['nodes'] <= reducer:
                    parents[target].append(source)
                    children[source].append(target)

            cond = False
            for parent, infants in parents.items():
                for child in infants:
                    if child not in parents and len(children[child]) == 1:
                        swallow(parent=parent)
                        cond = True
                        del children[child]

            if cond:
                cond = False
                vis_community(vis, reducer=reducer, children=children)

                sorted_children = dict(sorted(children.items(), key=lambda item: nodes[item[0]]['nodes']))
                for child, parents_ in sorted_children.items():
                    swallow(complex=True)
                    cond = True
                    del children[child]

                if cond:
                    vis_community(vis, reducer=reducer, children=children)

            return vis

        unique_strengths = sorted({link['strength'] for link in links}, reverse=True)
        aggregated = {value: [] for value in unique_strengths}

        grouped_links = {bin_key: [] for bin_key in aggregated}
        for link in links:
            grouped_links[link['strength']].append(link)

        added = set()
        compact = defaultdict(list)
        loners, sub_cluster_link_count, new_clusters, group_map, new_root, inter_links \
            = dict(), dict(), dict(), dict(), dict(), dict()
        for constraint_key in aggregated.keys():
            groups = aggregated[constraint_key]

            for link in grouped_links[constraint_key]:
                src_pos = groups.index(new_root[link['source']]) \
                    if (link['source'] in new_root) and (new_root[link['source']] in groups) else None
                trg_pos = groups.index(new_root[link['target']]) \
                    if (link['target'] in new_root) and (new_root[link['target']] in groups) else None

                for (uri, tag) in [(link['source'], 'src'), (link['target'], 'trg')]:
                    if uri in loners:
                        loner_constraint = loners[uri][0]
                        loner_group_id = loners[uri][1]

                        aggregated[loner_constraint].remove(loner_group_id)
                        aggregated[constraint_key].append(loner_group_id)

                        group_map[loner_group_id] = constraint_key
                        del loners[uri]

                        if tag == 'src':
                            src_pos = aggregated[constraint_key].index(loner_group_id)
                        else:
                            trg_pos = aggregated[constraint_key].index(loner_group_id)

                group_id = create_key(link['source'], link['target'])
                if src_pos == trg_pos is None:
                    source_not_in_added = link['source'] not in added
                    target_not_in_added = link['target'] not in added

                    if source_not_in_added or target_not_in_added:
                        groups += [group_id]
                        group = set()

                        for uri in [link['source'], link['target']]:
                            if uri not in added:
                                group.add(uri)
                                added.add(uri)
                                new_root[uri] = group_id

                        new_clusters[group_id] = group
                        group_map[group_id] = constraint_key

                        if source_not_in_added and target_not_in_added:
                            sub_cluster_link_count[group_id] = 1
                            compact[group_id].append(link)
                        elif new_root[link['source']] != new_root[link['target']]:
                            update_inter_link()
                    elif new_root[link['source']] == new_root[link['target']]:
                        sub_cluster_link_count[new_root[link['source']]] += 1
                        compact[new_root[link['source']]].append(link)
                    else:
                        update_inter_link()
                elif (src_pos is not None and trg_pos is None) or (src_pos is None and trg_pos is not None):
                    for uri, other_uri, pos in [(link['source'], link['target'], src_pos),
                                                (link['target'], link['source'], trg_pos)]:
                        if uri not in added and pos is None:
                            added.add(uri)
                            new_clusters[new_root[other_uri]].add(uri)
                            compact[new_root[other_uri]].append(link)
                            new_root[uri] = new_root[other_uri]

                            increase_sub_cluster_link_count(new_root[other_uri])
                        elif pos is None and new_root[link['source']] == new_root[link['target']]:
                            increase_sub_cluster_link_count(new_root[link['source']])
                            compact[new_root[link['source']]].append(link)
                        elif pos is None:
                            update_inter_link()
                elif src_pos is not None and trg_pos is not None and src_pos != trg_pos:
                    trg_grp = new_clusters[new_root[link['target']]]
                    src_grp = new_clusters[new_root[link['source']]]

                    src_grp_is_bigger = len(src_grp) > len(trg_grp)
                    uri = link['source'] if src_grp_is_bigger else link['target']
                    other_uri = link['target'] if src_grp_is_bigger else link['source']

                    big = src_grp if src_grp_is_bigger else trg_grp
                    small = trg_grp if src_grp_is_bigger else src_grp

                    del_key = new_root[other_uri]
                    key = new_root[uri]

                    compact[key].append(link)
                    compact[key] += compact[del_key]
                    del compact[del_key]

                    for item in small:
                        big.add(item)
                        new_clusters[key].add(item)
                        new_root[item] = new_root[uri]

                    increase_sub_cluster_link_count(
                        key, sub_cluster_link_count[del_key] if del_key in sub_cluster_link_count else 0)
                    if del_key in sub_cluster_link_count:
                        del sub_cluster_link_count[del_key]

                    update_inter_link(delete=del_key)

                    del new_clusters[del_key]
                    del group_map[del_key]

                    groups.remove(del_key)
                elif src_pos is not None and trg_pos is not None and src_pos == trg_pos:
                    increase_sub_cluster_link_count(new_root[link['source']])
                    compact[new_root[link['source']]].append(link)

            for group_id in groups:
                group = new_clusters[group_id]
                if len(group) == 1:
                    loners[list(group)[0]] = constraint_key, group_id

        nodes_view = []
        for key in new_clusters:
            group_size = len(new_clusters[key])
            possible = group_size * (group_size - 1) / 2

            temp = possible - sub_cluster_link_count[key] if key in sub_cluster_link_count else 0
            temp = temp if temp > 0 else 0
            missing_links = temp / possible if possible > 0 else 0

            if key in group_map:
                node_with_child = create_node(
                    key, 1 if group_size == 1 else key,
                    group_size=group_size, size=10, strength=group_map[key], missing_links=missing_links
                )

                if key in compact:
                    compact_nodes = {}
                    compact_links = []

                    for link in compact[key]:
                        for node in [link['source'], link['target']]:
                            if node not in compact_nodes:
                                compact_nodes[node] = create_node(node, key, org_node=nodes[node])

                        compact_links.append(create_link(link['source'], link['target'], strength=link['strength']))

                    node_with_child['child'] = {'nodes': list(compact_nodes.values()), 'links': compact_links}

                nodes_view.append(node_with_child)

        links_view = []
        link_checker = set()
        for key, link in inter_links.items():
            dist_factor = [len(new_clusters[link[0]]), len(new_clusters[link[1]])]
            current = create_link(link[0], link[1], strength=link[2], count=link[3], dist_factor=dist_factor)

            labels = F"{link[0]}-{link[1]}"
            if labels not in link_checker:
                links_view += [current]
                link_checker.add(labels)
            else:
                for dictionary in links_view:
                    curr_label = F"{dictionary['source']}-{dictionary['target']}"
                    if labels == curr_label:
                        dictionary['strength'] = max(dictionary['strength'], current['strength'])
                        break

        node_total_ratio = round(15 * len(nodes) / 100)

        return vis_community({'nodes': nodes_view, 'links': links_view}, reducer=node_total_ratio)

    nodes = {}
    links = []
    for link in job.get_links(id, type, cluster_ids=[cluster_id], with_view_properties='single'):
        for (node, ets_id, value) in [(link['source'], link['source_collections'][0], link['source_values']),
                                      (link['target'], link['target_collections'][0], link['target_values'])]:
            if node not in nodes:
                ets = job.get_entity_type_selection_by_id(ets_id)
                dataset_name = ets.collection.table_data['dataset_name']
                collection_uri = ets.collection.table_data['collection_shortened_uri']
                node_id = get_id_of_uri(node)

                label = F"{dataset_name} {collection_uri} {node_id}"
                if value and value[0]['values']:
                    label = F"{value[0]['values'][0]} ({label})"

                nodes[node] = create_node(
                    node, hash_string_min(ets.dataset_id),
                    label="-- " + label,
                    dataset=dataset_name, entity=collection_uri, local_id=node_id
                )

        links.append(create_link(link['source'], link['target'], strength=round(float(link['similarity']), 3)))

    vis = {'cluster_graph': {'nodes': list(nodes.values()), 'links': links}}
    if include_compact:
        vis['cluster_graph_compact'] = get_compact()

    if associations:
        links += [create_link(link[0], link[1], is_association=True)
                  for link in associations if link[0] in nodes and link[1] in nodes]

    return vis
