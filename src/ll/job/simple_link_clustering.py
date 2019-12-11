import ll.Generic.Utility as Ut


class SimpleLinkClustering:
    def __init__(self, links_iter, convert_to_nt_format=False):
        self.links_iter = links_iter
        self.convert_to_nt_format = convert_to_nt_format

        self.stop = False
        self.all_links_processed = False
        self.links_processed = 0
        self.id_counter = 0
        self.clusters = dict()
        self.root = dict()

    def stop_clustering(self):
        self.stop = True

    def get_clusters(self):
        self.all_links_processed = False
        self.links_processed = 0
        self.id_counter = 0
        self.clusters = dict()
        self.root = dict()

        for link in self.links_iter:
            if not self.stop:
                self.add_link_to_cluster(link['source'], link['target'])
                self.links_processed += 1

        self.all_links_processed = True
        for data in list(self.clusters.values()):
            if not self.stop:
                smallest_hash = None
                for node in data['nodes']:
                    hashed = Ut.hasher(Ut.hasher(node))
                    if not smallest_hash or hashed < smallest_hash:
                        smallest_hash = hashed

                cluster_id = "{}".format(str(smallest_hash).replace("-", "N")) \
                    if str(smallest_hash).startswith("-") \
                    else "P{}".format(smallest_hash)

                yield {'id': cluster_id, 'nodes': data['nodes'], 'links': data['links']}

    def add_link_to_cluster(self, subject, t_object):
        child_1 = Ut.to_nt_format(subject.strip()) if self.convert_to_nt_format else subject.strip()
        child_2 = Ut.to_nt_format(t_object.strip()) if self.convert_to_nt_format else t_object.strip()

        has_parent_1 = child_1 in self.root
        has_parent_2 = child_2 in self.root

        if not has_parent_1 and not has_parent_2:
            parent = str(self.id_counter)
            self.id_counter += 1

            self.root[child_1] = parent
            self.root[child_2] = parent

            self.clusters[parent] = {'nodes': {child_1, child_2}, 'links': {(child_1, child_2)}}
        elif has_parent_1 and has_parent_2:
            if self.root[child_1] != self.root[child_2]:
                parent1 = self.root[child_1]
                parent2 = self.root[child_2]

                if parent2 in self.clusters:
                    for child in self.clusters[parent2]['nodes']:
                        self.root[child] = parent1

                    self.clusters[parent1]['nodes'] = self.clusters[parent1]['nodes'] \
                        .union(self.clusters[parent2]['nodes'])
                    self.clusters[parent1]['links'] = self.clusters[parent1]['links'] \
                        .union(self.clusters[parent2]['links'])

                    self.clusters[parent1]['links'].add((child_1, child_2))
                    del self.clusters[parent2]
            else:
                parent = self.root[child_1]
                self.clusters[parent]['links'].add((child_1, child_2))
        else:
            child = child_2 if has_parent_1 else child_1
            parent = self.root[child_1 if has_parent_1 else child_2]
            self.root[child] = parent

            self.clusters[parent]['nodes'].add(child)
            self.clusters[parent]['links'].add((child_1, child_2))
