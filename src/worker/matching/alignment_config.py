from common.helpers import hash_string
from worker.matching.match import Match
from worker.matching.resource import Resource


class AlignmentConfig:
    def __init__(self, run_match, matches_data, resources_data):
        self.columns = {}
        self.run_match = run_match
        self.matches = list(map(lambda match: Match(match, self), matches_data))
        self.resources = list(map(lambda resource: Resource(resource, self), resources_data))

    @property
    def matches_to_run(self):
        matches_added = []
        matches_to_add = [self.run_match]
        matches_to_run = []

        while matches_to_add:
            match_to_add = matches_to_add[0]

            if match_to_add not in matches_added:
                for match in self.matches:
                    if match.id == match_to_add:
                        matches_to_run.insert(0, match)

                        if match.match_against:
                            matches_to_add.append(match.match_against)

                        matches_to_add.remove(match_to_add)
                        matches_added.append(match_to_add)
            else:
                matches_to_add.remove(match_to_add)

        return matches_to_run

    @property
    def resources_to_run(self):
        resources_to_add = []
        resources_to_run = []

        for match in self.matches_to_run:
            resources_to_add += [hash_string(resource) for resource in match.resources]

        resources_added = []
        while resources_to_add:
            resource_to_add = resources_to_add[0]

            if resource_to_add not in resources_added:
                for resource in self.resources:
                    if resource.label == resource_to_add:
                        resources_to_run.append(resource)

                        resources_to_add.remove(resource_to_add)
                        resources_added.append(resource_to_add)
            else:
                resources_to_add.remove(resource_to_add)

        return resources_to_run

    def get_match_by_id(self, id):
        for match in self.matches:
            if match.id == id:
                return match

        return None

    def get_resource_by_label(self, label):
        for resource in self.resources:
            if resource.label == label:
                return resource

        return None

    def get_resource_columns(self, label):
        if label not in self.columns:
            resource = self.get_resource_by_label(label)
            self.columns[label] = resource.collection.table_data['columns']

        return self.columns[label]
