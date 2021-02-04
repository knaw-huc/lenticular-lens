import logging

from ll.util.helpers import to_nt_format
from ll.util.hasher import hasher

log = logging.getLogger(__name__)


class SimpleLinkClustering:
    def __init__(self, links_iter, convert_to_nt_format=False):
        self._links_iter = links_iter
        self._convert_to_nt_format = convert_to_nt_format

        self._stop = False
        self._all_links_processed = False
        self._id_counter = 0
        self._root = dict()

        self.links_processed = 0
        self.clusters = dict()

    def stop_clustering(self):
        self._stop = True

    def get_clusters(self):
        self._all_links_processed = False
        self._id_counter = 0
        self._root = dict()

        self.links_processed = 0
        self.clusters = dict()

        log.info('Iterating through the links')

        for link in self._links_iter:
            if not self._stop:
                self.add_link_to_cluster(link['source'], link['target'])
                self.links_processed += 1

        log.info('Processing the clusters for unique id and preparing for serialisation')

        self._all_links_processed = True
        for data in list(self.clusters.values()):
            if not self._stop:
                smallest_hash = None
                for node in data['nodes']:
                    hashed = hasher(hasher(node))
                    if not smallest_hash or hashed < smallest_hash:
                        smallest_hash = hashed

                cluster_id = "{}".format(str(smallest_hash).replace("-", "N")) \
                    if str(smallest_hash).startswith("-") \
                    else "P{}".format(smallest_hash)

                yield {'id': cluster_id, 'nodes': data['nodes'], 'links': data['links']}

        log.info('Clustering is completed')

    def add_link_to_cluster(self, subject, t_object):
        child_1 = to_nt_format(subject.strip()) if self._convert_to_nt_format else subject.strip()
        child_2 = to_nt_format(t_object.strip()) if self._convert_to_nt_format else t_object.strip()

        has_parent_1 = child_1 in self._root
        has_parent_2 = child_2 in self._root

        if not has_parent_1 and not has_parent_2:
            parent = str(self._id_counter)
            self._id_counter += 1

            self._root[child_1] = parent
            self._root[child_2] = parent

            self.clusters[parent] = {'nodes': {child_1, child_2}, 'links': [(child_1, child_2)]}
        elif has_parent_1 and has_parent_2:
            if self._root[child_1] != self._root[child_2]:
                parent1 = self._root[child_1]
                parent2 = self._root[child_2]

                if parent2 in self.clusters:
                    for child in self.clusters[parent2]['nodes']:
                        self._root[child] = parent1

                    self.clusters[parent1]['nodes'] = self.clusters[parent1]['nodes'] \
                        .union(self.clusters[parent2]['nodes'])
                    self.clusters[parent1]['links'] += self.clusters[parent2]['links']

                    self.clusters[parent1]['links'].append((child_1, child_2))
                    del self.clusters[parent2]
            else:
                parent = self._root[child_1]
                self.clusters[parent]['links'].append((child_1, child_2))
        else:
            child = child_2 if has_parent_1 else child_1
            parent = self._root[child_1 if has_parent_1 else child_2]
            self._root[child] = parent

            self.clusters[parent]['nodes'].add(child)
            self.clusters[parent]['links'].append((child_1, child_2))
