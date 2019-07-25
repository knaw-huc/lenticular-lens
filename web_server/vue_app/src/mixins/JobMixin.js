export default {
    data() {
        return {
            job: null,
            resources: [],
            matches: [],
            datasets: null,
        }
    },
    methods: {
        addResource() {
            this.resources.push({
                dataset_id: '',
                collection_id: '',
                'id': findId(this.resources),
                'filter': {
                    'type': 'AND',
                    'conditions': [],
                },
                limit: -1,
                related: [],
                related_array: false,
            });
        },

        addMatch() {
            this.matches.push({
                'id': findId(this.matches),
                'is_association': false,
                'label': 'Alignment ' + (this.matches.length + 1),
                'sources': [],
                'targets': [],
                'properties': [],
                'type': 'AND',
                'conditions': [],
            });
        },

        duplicateMatch(match) {
            const duplicate = copy(match);
            this.matches.push({
                ...duplicate,
                'id': findId(this.matches),
                'label': 'Alignment ' + (this.matches.length + 1),
            });
        },

        getResourceById(resource_id, resources = this.resources) {
            for (let i = 0; i < resources.length; i++) {
                if (resources[i].id === parseInt(resource_id) || resources[i].label === resource_id)
                    return resources[i];
            }
        },

        getMatchById(match_id, matches = this.matches) {
            for (let i = 0; i < matches.length; i++) {
                if (matches[i].id === parseInt(resource_id) || matches[i].label === match_id)
                    return matches[i];
            }
        },

        createReferencesForProperty(property, resources) {
            // Check if reference
            if (property.length > 2) {
                // Don't follow reference if user selected 'Value'
                if (property[2] === '__value__') {
                    return property.slice(0, 2)
                }

                let base_referenced_resource = this.getResourceById(property[0], resources);

                const resource_id = parseInt(property[0]);
                for (let i = 0; i < resources.length; i++) {
                    if (resources[i].id === resource_id || resources[i].label === resource_id)
                        base_referenced_resource = resources[i];
                }

                // Add resource
                let referenced_resource = {
                    "collection_id": property[2],
                    "dataset_id": base_referenced_resource.dataset_id,
                    "related": []
                };
                referenced_resource['label'] = this.$utilities.md5(property[0] + property[1] + JSON.stringify(referenced_resource));

                let resource_exists = false;
                resources.forEach(rc => {
                    if (rc.label === referenced_resource.label) {
                        resource_exists = true;
                        return false
                    }
                });
                if (!resource_exists) {
                    resources.push(referenced_resource);
                }

                // Add relation
                let relation = {
                    "resource": referenced_resource.label,
                    "local_property": property[1],
                    "remote_property": "uri"
                };
                let relation_exists = false;
                base_referenced_resource.related.forEach(existing_relation => {
                    if (JSON.stringify(existing_relation) === JSON.stringify(relation)) {
                        relation_exists = true;
                        return false
                    }
                });
                if (!relation_exists) {
                    base_referenced_resource.related.push(relation);
                }

                if (base_referenced_resource.related.length > 1) {
                    base_referenced_resource.related_array = true;
                }

                // Replace part of property that was processed and re-enter the function with that output
                return this.createReferencesForProperty([referenced_resource.label, property[3].toLowerCase()].concat(property.slice(4)), resources);
            }

            return property
        },

        async loadJobData(jobId) {
            const jobData = await callApi('/job/' + jobId);
            this.job = jobData;

            if (this.job.resources_form_data)
                this.resources = copy(this.job.resources_form_data);

            if (this.job.mappings_form_data)
                this.matches = copy(this.job.mappings_form_data);
        },

        async createJob(inputs) {
            const data = await callApi("/job/create/", inputs);
            return data.job_id;
        },

        async submit() {
            let new_resources = [];
            let resources_copy = copy(this.resources);
            let matches_copy = copy(this.matches);

            // Check for references
            resources_copy.forEach(resource_copy => {
                if (resource_copy.filter.type) {
                    getRecursiveConditions(resource_copy.filter.conditions).forEach(condition => {
                        condition.property = this.createReferencesForProperty(condition.property, resources_copy);
                    });
                }
            });

            matches_copy.forEach(match_copy => {
                ['sources', 'targets'].forEach(resources_key => {
                    match_copy[resources_key].forEach((resource_id, resource_index) => {
                        if (resource_id == parseInt(resource_id)) {
                            match_copy[resources_key][resource_index] = this.getResourceById(resource_id).label;
                        }
                    });
                });

                getRecursiveConditions(match_copy.conditions).forEach(condition => {
                    ['sources', 'targets'].forEach(resources_key => {
                        Object.keys(condition[resources_key]).forEach(resource_id => {
                            condition[resources_key][resource_id].forEach((property, property_index) => {
                                condition[resources_key][resource_id][property_index].property = this.createReferencesForProperty(property.property, resources_copy);
                                condition[resources_key][resource_id][property_index].property.forEach((property_part, property_part_index) => {
                                    if (!isNaN(parseInt(property_part)) && property_part >= 0)
                                        condition[resources_key][resource_id][property_index].property[property_part_index] = this.getResourceById(property_part).label;
                                });
                            });

                            condition[resources_key][this.getResourceById(resource_id).label] = condition[resources_key][resource_id];
                            delete condition[resources_key][resource_id];
                        });
                    });
                });
            });

            resources_copy.forEach(resource_copy => {
                if (resource_copy.filter && resource_copy.filter.type) {
                    getRecursiveConditions(resource_copy.filter.conditions).forEach(condition => {
                        if (condition.property[0] == parseInt(condition.property[0])) {
                            condition.property[0] = this.getResourceById(condition.property[0]).label;
                        }
                        condition.property[1] = condition.property[1].toLowerCase();
                        if (typeof condition.value_type !== 'undefined') {
                            condition[condition.value_type] = condition.value;
                            delete condition.value;
                            delete condition.value_type;
                        }
                    });
                }
                else {
                    delete resource_copy.filter;
                }

                if (resource_copy.related) {
                    resource_copy.related.forEach(related => {
                        if (related.resource == parseInt(related.resource)) {
                            related.resource = this.getResourceById(related.resource).label;
                        }
                        related.local_property = [related.local_property.toLowerCase()];
                        related.remote_property = [related.remote_property.toLowerCase()];
                        delete related.resource_index;
                    });

                    if (resource_copy.related_array) {
                        resource_copy.related = [resource_copy.related]
                    }
                }

                delete resource_copy.related_array;
                let resource_copy_copy = copy(resource_copy);
                delete resource_copy_copy.id;

                new_resources.push(resource_copy_copy);
            });

            await this.updateJob({
                job_id: this.job.job_id,
                job_title: this.job.job_title,
                job_description: this.job.job_description,
                resources: new_resources,
                matches: matches_copy,
                resources_original: this.resources,
                matches_original: this.matches,
                status: 'Requested',
            });
        },

        async updateJob(jobData) {
            await callApi("/job/update/", jobData);
        },

        async runAlignment(matchId, restart) {
            await this.submit();
            return await callApi(`/job/${this.job.job_id}/run_alignment/${matchId}`, {restart});
        },

        async getClusters(clusteringId, association) {
            return callApi(`/job/${this.job.job_id}/clusters/${clusteringId}?association=${association}`);
        },

        async createClustering(alignment, association_file, clustered) {
            return callApi(`/job/${this.job.job_id}/create_clustering/`, {
                alignment, association_file, clustered
            });
        },

        async getClusterGraphs(clusteringId, clusterId, graphData) {
            return callApi(`/job/${this.job.job_id}/cluster/${clusteringId}/${clusterId}/graph`, graphData);
        },

        async loadDatasets() {
            if (this.datasets)
                return;

            const datasets = await callApi("/datasets");

            // Make internal references for referenced collections
            Object.keys(datasets).forEach(dataset_name => {
                let dataset = datasets[dataset_name];
                Object.keys(dataset.collections).forEach(collection_name => {
                    let collection = dataset.collections[collection_name];
                    Object.keys(collection).forEach(property_name => {
                        let property = collection[property_name];
                        if (typeof property['referencedCollections'] !== 'undefined') {
                            let referenced_collections = property['referencedCollections'];
                            property['referencedCollections'] = {};
                            referenced_collections = referenced_collections.filter(ref_collection_name => {
                                return ref_collection_name !== 'tim_unknown'
                            });
                            referenced_collections.forEach(ref_collection_name => {
                                property['referencedCollections'][ref_collection_name] = dataset.collections[ref_collection_name];
                            });
                        }
                    });
                });
            });

            this.datasets = datasets;
        },
    },
};

function copy(obj) {
    return JSON.parse(JSON.stringify(obj));
}

function findId(objs) {
    let latestId = -1;
    objs.forEach(obj => {
        if (obj.id > latestId) latestId = obj.id;
    });
    return latestId + 1;
}

function getRecursiveConditions(filter_obj) {
    let conditions = [];
    let obj_arr;

    if (Array.isArray(filter_obj)) {
        obj_arr = filter_obj;
    }
    else if (Array.isArray(filter_obj.conditions)) {
        obj_arr = filter_obj.conditions;
    }

    if (obj_arr) {
        obj_arr.forEach(condition => {
            conditions = conditions.concat(getRecursiveConditions(condition));
        });
        return conditions;
    }
    else {
        return [filter_obj]
    }
}

async function callApi(path, body) {
    if (body) {
        const response = await fetch(path, {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            method: 'POST',
            body: JSON.stringify(body)
        });

        return response.json();
    }

    const response = await fetch(path);

    return response.json();
}