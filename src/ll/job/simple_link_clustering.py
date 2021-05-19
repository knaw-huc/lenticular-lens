import logging

log = logging.getLogger(__name__)


class SimpleLinkClustering:
    def __init__(self, links_iter):
        self._links_iter = links_iter

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

        clusters = list(sorted(self.clusters.values(), key=lambda x: (len(x) * -1, min(x))))
        for (idx, nodes) in enumerate(clusters):
            if not self._stop:
                yield {'id': idx + 1, 'nodes': nodes}

        log.info('Clustering is completed')

    def add_link_to_cluster(self, source, target):
        has_parent_1 = source in self._root
        has_parent_2 = target in self._root

        if not has_parent_1 and not has_parent_2:
            parent = str(self._id_counter)
            self._id_counter += 1

            self._root[source] = parent
            self._root[target] = parent

            self.clusters[parent] = {source, target}
        elif has_parent_1 and has_parent_2:
            if self._root[source] != self._root[target]:
                parent1 = self._root[source]
                parent2 = self._root[target]

                if parent2 in self.clusters:
                    for child in self.clusters[parent2]:
                        self._root[child] = parent1

                    self.clusters[parent1] = self.clusters[parent1].union(self.clusters[parent2])
                    del self.clusters[parent2]
        else:
            child = target if has_parent_1 else source
            parent = self._root[source if has_parent_1 else target]

            self._root[child] = parent
            self.clusters[parent].add(child)
