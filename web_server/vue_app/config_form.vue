<template>
<div class="container" id="app">
    <form @submit.prevent="submitForm" action="" method="post">
    <form-wizard
        title="Lenticular Lenses II"
        subtitle="Reconcile data for Golden Agents"
        color="#efc501"
        shape="square"
        ref="formWizard"
    >
        <tab-content title="Collections">
        <div id="resources">
            <h2>Collections</h2>
            <resource-component
                    :resource="resource"
                    :datasets="datasets"
                    :resources="resources"
                    v-for="(resource, index) in resources"
                    :key="resource.id"
                    v-on:remove="resources.splice(index, 1)"
            ></resource-component>

            <div class="form-group mt-4">
                <button v-on:click="addResource" type="button" class="add-resource form-control btn btn-primary w-25">
                    + Add Collection
                </button>
            </div>
        </div>
        </tab-content>

        <tab-content title="Mappings">
        <div id="matches" class="mt-5">
            <h2>Alignment Mappings</h2>

            <match-component
                    :match="match"
                    :matches="matches"
                    :datasets="datasets"
                    :resources="resources"
                    v-for="(match, index) in matches"
                    :key="match.id"
                    @remove="matches.splice(index, 1)"
            ></match-component>

            <div class="form-group mt-4">
                <button v-on:click="addMatch" type="button" class="form-control btn btn-primary w-25">
                    + Add Alignment Mapping
                </button>
            </div>
        </div>
        </tab-content>

        <tab-content title="Results">
        <div v-if="job_data">
            <div>
                Request received at: {{ job_data.requested_at }}
            </div>
            <div>
                Status: <pre>{{ job_data.status }}</pre>
            </div>
            <div v-if="job_data.processing_at">
                Processing started at: {{ job_data.processing_at }}
            </div>
            <div v-if="job_data.finished_at">
                Processing finished at: {{ job_data.finished_at }}
                <div v-for="match in matches">
                    <a :href="'/job/' + job_id + '/result/' + match.label" target="_blank">Results for {{ match.label }}</a>
                </div>
                <div>
                    <a :href="'/job/' + job_id + '/result/download'" download>Download RDF</a>
                </div>
            </div>
        </div>
        </tab-content>

        <template v-if="props.activeTabIndex === 1" slot="next" scope="props">
            <wizard-button
                    v-if="job_data"
                    :style="props.fillButtonStyle"
                    :disabled="props.loading">
                Results
            </wizard-button>
            &nbsp;
            <wizard-button
                    v-if="has_changes"
                    :style="props.fillButtonStyle"
                    :disabled="props.loading"
                    @click.native="submitForm">
                Run Job
             </wizard-button>
        </template>
        <template slot="finish" scope="props" style="display: none">&#8203;</template>
    </form-wizard>
    </form>
</div>
</template>

<script>
    import Resource from './components/Resource'
    import Match from './components/Match'

    export default {
        name: 'app',
        components: {
            'resource-component': Resource,
            'match-component': Match,
        },
        computed: {
            has_changes() {
                return !Boolean(this.job_data)
                    || JSON.stringify(this.resources) !== JSON.stringify(this.job_data['resources_form_data'])
                    || JSON.stringify(this.matches) !== JSON.stringify(this.job_data['mappings_form_data'])
            },
        },
        data() {
            return {
                datasets: [],
                job_id: '',
                job_data: null,
                resources: [],
                resources_count: 0,
                limit_all: -1,
                matches: [],
                matches_count: 0,
            }
        },
        methods: {
            addFilterCondition(resource) {
                let condition = {
                    'type': '',
                    'property': '',
                };
                resource.filter.conditions.push(condition);
            },
            addResource(event) {
                if (event) {
                    event.target.blur();
                }
                this.resources_count ++;
                let resource = {
                    dataset_id: '',
                    collection_id: '',
                    'id': this.resources_count,
                    'filter': {
                        'type': '',
                        'conditions': [],
                    },
                    limit: -1,
                    related: [],
                    related_array: false,
                };
                this.resources.push(resource);
            },
            addMatch(event) {
                if (event) {
                    event.target.blur();
                }
                this.matches_count++;
                let match = {
                    'id': this.matches_count,
                    'sources': [],
                    'targets': [],
                    'conditions': {
                        'type': 'AND',
                        'items': [],
                    },
                };
                this.matches.push(match);
            },
            applyLimitAll() {
                this.resources.forEach(resource => {
                    this.$set(resource, 'limit', this.limit_all);
                });
            },
            getDatasets() {
                let vue = this;
                fetch('/datasets')
                    .then((response) => response.json())
                    .then((data) => {
                        // Make internal references for referenced collections
                        Object.keys(data).forEach(dataset_name => {
                            let dataset = data[dataset_name];
                            Object.keys(dataset).forEach(collection_name => {
                                let collection = dataset[collection_name];
                                Object.keys(collection).forEach(property_name => {
                                    let property = collection[property_name];
                                    if (typeof property['referencedCollections'] !== 'undefined') {
                                        let referenced_collections = property['referencedCollections'];
                                        property['referencedCollections'] = {};
                                        referenced_collections.forEach(ref_collection_name => {
                                            property['referencedCollections'][ref_collection_name] = dataset[ref_collection_name];
                                        });
                                    }
                                });
                            });
                        });

                        vue.datasets = data;

                        let urlParams = new URLSearchParams(window.location.search);
                        let job_id = urlParams.get('job_id');
                        if (job_id) {
                            this.$refs.formWizard.activateAll();
                            this.$refs.formWizard.changeTab(0, 2);

                            this.job_id = job_id;
                            this.getJobData();
                        } else {
                            this.addResource();
                            this.addMatch();
                        }
                    });
            },
            getJobData() {
                if (this.job_id !== '') {
                    fetch('/job/' + this.job_id)
                        .then((response) => response.json())
                        .then((data) => {
                            this.job_data = JSON.parse(JSON.stringify(data));
                            if (this.resources_count < 1) {
                                this.resources = data.resources_form_data;
                                this.resources_count = this.resources.length;
                            }
                            if (this.matches_count < 1) {
                                this.matches = data.mappings_form_data;
                                this.matches_count = this.matches.length;
                            }

                            if (this.job_data.status !== 'Finished') {
                                setTimeout(this.getJobData, 5000);
                            }
                        })
                    ;
                }
            },
            getMatchById(match_id) {
                for (let i = 0; i < this.matches.length; i++) {
                    if (this.matches[i].id == match_id)
                        return this.matches[i];
                }
            },
            getResourceById(resource_id, resources = this.resources) {
                for (let i = 0; i < resources.length; i++) {
                    if (resources[i].id == resource_id)
                        return resources[i];
                }
            },
            submitForm() {
                let vue = this;
                function get_value(value_object, target_object) {
                    if (value_object.value_type === 'property') {
                        target_object.property = [
                            vue.getResourceById(value_object.property[0]).label.toLowerCase(),
                            value_object.property[1].toLowerCase()
                        ];
                    }

                    let exclude_keys = ['', 'function_name', 'property', 'transformers', 'value_type'];

                    if (value_object.value_type === 'function') {
                        if (Array.isArray(value_object[value_object.function_name])) {
                            target_object[value_object.function_name] = [];
                            value_object[value_object.function_name].forEach(parameter_object => {
                                let target_parameter_object = {};
                                target_object[value_object.function_name].push(get_value(parameter_object, target_parameter_object))
                            });
                        } else {
                            target_object[value_object.function_name] = {};
                            if (value_object[value_object.function_name].value_type === '') {
                                Object.keys(value_object[value_object.function_name]).forEach(field_name => {
                                    if (exclude_keys.indexOf(field_name) < 0) {
                                        target_object[value_object.function_name][field_name] = {};
                                        target_object[value_object.function_name][field_name] = get_value(value_object[value_object.function_name][field_name], target_object[value_object.function_name][field_name]);
                                    }
                                });
                            } else {
                                target_object[value_object.function_name] = get_value(value_object[value_object.function_name], target_object[value_object.function_name])
                            }
                        }
                    }

                    if (value_object.value_type === '') {
                        Object.keys(value_object).forEach(field_name => {
                            if (exclude_keys.indexOf(field_name) < 0) {
                                target_object[field_name] = {};
                                target_object[field_name] = get_value(value_object[field_name], target_object[field_name]);
                            }
                        });
                    }

                    if (value_object.transformers && value_object.transformers.length > 0) {
                        target_object.transformers = value_object.transformers;
                    }

                    return target_object;
                }

                let resources = [];
                let resources_copy = JSON.parse(JSON.stringify(this.resources));

                // Check for references
                resources_copy.forEach(resource_copy => {
                    if (resource_copy.filter.type) {
                        resource_copy.filter.conditions.forEach(condition => {
                            // Check if reference
                            if (condition.property.length > 2) {
                                let base_referenced_resource = this.getResourceById(condition.property[0], resources_copy);

                                // Add resource
                                let referenced_resource = {
                                    "collection_id": condition.property[2],
                                    "dataset_id": base_referenced_resource.dataset_id
                                };
                                referenced_resource['label'] = this.$utilities.md5(JSON.stringify(referenced_resource));

                                let resource_exists = false;
                                resources_copy.forEach(rc => {
                                    if (rc.label === referenced_resource.label) {
                                        resource_exists = true;
                                        return false
                                    }
                                });
                                if (!resource_exists) {
                                    resources_copy.push(referenced_resource);
                                }

                                // Add relation
                                base_referenced_resource.related.push({
                                    "resource": referenced_resource.label,
                                    "local_property": condition.property[1],
                                    "remote_property": "uri"
                                });

                                // Replace condition property
                                condition.property = [referenced_resource.label, condition.property[3].toLowerCase()]
                            }
                        });
                    }
                });

                resources_copy.forEach(resource_copy => {
                    if (resource_copy.filter && resource_copy.filter.type) {
                        resource_copy.filter.conditions.forEach(condition => {
                            if (condition.property[0] === parseInt(condition.property[0])) {
                                condition.property[0] = this.getResourceById(condition.property[0]).label;
                            }
                            condition.property[1] = condition.property[1].toLowerCase();
                            if (typeof condition.value_type !== 'undefined') {
                                condition[condition.value_type] = condition.value;
                                delete condition.value;
                                delete condition.value_type;
                            }
                        });
                    } else {
                        delete resource_copy.filter;
                    }

                    if (resource_copy.related) {
                        resource_copy.related.forEach(related => {
                            if (related.resource === parseInt(related.resource)) {
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
                    delete resource_copy.id;

                    resources.push(resource_copy);
                });

                let matches = [];
                this.matches.forEach(match_original => {
                    let match = {
                        'label': match_original.label,
                        'sources': [],
                        'targets': [],
                        'conditions': [],
                    };

                    match_original.sources.forEach(resource_original => {
                        if (!resource_original.resource)
                            return;

                        let resource = {
                            'resource': this.getResourceById(resource_original.resource).label,
                            'matching_fields': [],
                        };

                        resource_original.matching_fields.forEach(matching_field_original => {
                            let matching_field = {'label': matching_field_original.label};
                            if (matching_field_original.value.value_type === 'function') {
                                matching_field.value = {};
                                matching_field.value = get_value(matching_field_original.value, matching_field.value);
                            } else {
                                matching_field = get_value(matching_field_original.value, matching_field);
                            }
                            resource.matching_fields.push(matching_field);
                        });

                        match.sources.push(resource);
                    });

                    match_original.targets.forEach(resource_original => {
                        if (!resource_original.resource)
                            return;

                        let resource = {
                            'resource': this.getResourceById(resource_original.resource).label,
                            'matching_fields': [],
                        };

                        resource_original.matching_fields.forEach(matching_field_original => {
                            let matching_field = {'label': matching_field_original.label};
                            if (matching_field_original.value.value_type === 'function') {
                                matching_field.value = {};
                                matching_field.value = get_value(matching_field_original.value, matching_field.value);
                                matching_field.transformers = JSON.parse(JSON.stringify(matching_field.value.transformers));
                                delete matching_field.value.transformers;
                            } else {
                                matching_field = get_value(matching_field_original.value, matching_field);
                            }
                            resource.matching_fields.push(matching_field);
                        });

                        match.targets.push(resource);
                    });

                    if (match.targets.length === 0) {
                        delete match.targets;
                    }

                    match.conditions = {
                        'type': match_original.conditions.type,
                        'items': [],
                    };

                    match_original.conditions.items.forEach(item_original => {
                        if (item_original.matching_field === '')
                            return;

                        let item = {
                            'matching_field': match_original.matching_field_labels[item_original.matching_field],
                        };
                        if (typeof item_original.method === 'string') {
                            item.method = item_original.method;
                        } else {
                            item.method = {};
                            Object.keys(item_original.method).forEach(method_name => {
                                item.method[method_name] = [];
                                item_original.method[method_name].forEach(parameter_object => {
                                    if (parameter_object.type === 'matching_label') {
                                        item.method[method_name].push(this.getMatchById(parameter_object.value).label);
                                    } else {
                                        item.method[method_name].push(JSON.parse(JSON.stringify(parameter_object)));
                                    }
                                });
                            });
                        }

                        match.conditions.items.push(item);
                    });

                    matches.push(match);
                });

                let data = {
                    'resources': resources,
                    'matches': matches,
                    'resources_original': this.resources,
                    'matches_original': this.matches,
                };

                fetch("/handle_json_upload/",
                    {
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                        },
                        method: "POST",
                        body: JSON.stringify(data)
                    }
                )
                    .then((response) => response.json())
                    .then((data) => {
                        this.$set(this, 'job_id', data.job_id);

                        let parsedUrl = new URL(window.location.href);
                        parsedUrl.searchParams.set('job_id', data.job_id);
                        window.history.pushState(null, null, parsedUrl.href);

                        this.getJobData();
                    }
                );
            }
        },
        mounted() {
            this.getDatasets();
        },
    };
</script>