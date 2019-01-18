<template>
<div class="container" id="app">
    <h1>Golden Agents Reconciliation</h1>
    <form @submit.prevent="submitForm" action="" method="post">
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
                <button v-on:click="addResource" type="button" class="add-resource form-control btn btn-success w-25">
                    + Add Collection
                </button>
            </div>
        </div>

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
                <button v-on:click="addMatch" type="button" class="form-control btn btn-success w-25">
                    + Add Alignment Mapping
                </button>
            </div>
        </div>

        <div class="form-group row align-items-end">
            <label class="col-auto" for="limit-all">Only use a sample of this amount of records for all resources (-1 is no limit):</label>
            <input type="number" min="-1" v-model.number="limit_all" class="form-control col-1" id="limit-all">
            <div class="col-1">
                <button type="button" class="form-control btn btn-info" @click="applyLimitAll">Apply</button>
            </div>
        </div>

        <div class="form-group mt-5">
            <button type="submit" class="form-control btn btn-success w-25">
                Generate JSON
            </button>
        </div>

        <div v-if="job_data">
            <div>
                Request received at: {{ job_data.requested_at }}
            </div>
            <div>
                Status: {{ job_data.status }}
            </div>
            <div v-if="job_data.processing_at">
                Processing started at: {{ job_data.processing_at }}
            </div>
            <div v-if="job_data.finished_at">
                Processing finished at: {{ job_data.finished_at }}
                <div v-for="match in matches">
                    <a :href="'/job/' + job_id + '/result/' + match.label" target="_blank">Results for {{ match.label }}</a>
                </div>
            </div>
        </div>
    </form>
</div>
</template>

<script>
    import 'bootstrap/dist/css/bootstrap.css'
    import 'bootstrap-vue/dist/bootstrap-vue.css'

    import Resource from './components/Resource'
    import Match from './components/Match'

    export default {
        name: 'app',
        components: {
            'resource-component': Resource,
            'match-component': Match,
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
                        vue.datasets = data;

                        this.addResource();
                        this.addMatch();

                        this.resources = JSON.parse('[{"dataset_id":"ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_ondertrouwregister","collection_id":"saaOnt_IndexOpOndertrouwregister","id":1,"filter":{"type":"AND","conditions":[{"type":"date_is_within","property":[1,"saaOnt_registration_date"],"value":"16**"},{"type":"appearances","property":[1,"saaOnt_urlScanList"],"value_type":"max","value":6},{"type":"appearances","property":[2,"saaOnt_full_nameList"],"value_type":"max","value":5}]},"related":[],"related_array":false,"label":"marriage_record","limit":-1},{"dataset_id":"ufab7d657a250e3461361c982ce9b38f3816e0c4b__saa_index_op_ondertrouwregister","collection_id":"saaOnt_Person","id":2,"filter":{"type":"AND","conditions":[{"type":"!=","property":[2,"saaOnt_first_nameList"],"value":"..."},{"type":"!=","property":[2,"saaOnt_family_nameList"],"value":"..."}]},"related":[{"resource_index":"","resource":1,"local_property":"saaOnt_isInRecord","remote_property":"uri"}],"related_array":false,"label":"marriage_person","limit":-1},{"dataset_id":"ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico","collection_id":"schema_Person","id":3,"filter":{"type":"","conditions":[{"type":"","property":[3,""]},{"type":"","property":[3,""]},{"type":"","property":[3,""]}]},"related":[{"resource":4,"local_property":"uri","remote_property":"http___purl_org_vocab_bio_0_1_partnerList"}],"related_array":false,"label":"ecartico_person","limit":-1},{"dataset_id":"ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico","collection_id":"http___purl_org_vocab_bio_0_1_Marriage","id":4,"filter":{"type":"","conditions":[{"type":"","property":[4,""]},{"type":"","property":[4,""]},{"type":"","property":[4,""]}]},"related":[{"resource":5,"local_property":"http___www_w3_org_2006_time_hasTime","remote_property":"uri"},{"resource":6,"local_property":"http___www_w3_org_2006_time_hasTime","remote_property":"uri"}],"related_array":true,"label":"ecartico_marriage","limit":-1},{"dataset_id":"ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico","collection_id":"schema_StructuredValue","id":5,"filter":{"type":"","conditions":[{"type":"","property":[5,""]},{"type":"","property":[5,""]},{"type":"","property":[5,""]}]},"related":[],"related_array":false,"label":"ecartico_structured_value","limit":-1},{"dataset_id":"ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico","collection_id":"schema_StructuredValueDate","id":6,"filter":{"type":"","conditions":[{"type":"","property":[6,""]},{"type":"","property":[6,""]},{"type":"","property":[6,""]}]},"related":[],"related_array":false,"label":"ecartico_structured_value_date","limit":-1}]');
                        this.matches = JSON.parse('[{"id":1,"sources":[{"id":1,"matching_fields":[{"id":1,"value":{"property":[2,"saaOnt_full_nameList"],"transformers":["ecartico_full_name"],"value_type":"property","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[2,""],"transformers":[],"value_type":"","function_name":""},{"property":[2,""],"transformers":[],"value_type":"","function_name":""}]},"label":"name"},{"id":2,"value":{"property":[1,"saaOnt_registration_date"],"transformers":["to_date_immutable"],"value_type":"property","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[2,""],"transformers":[],"value_type":"","function_name":""},{"property":[2,""],"transformers":[],"value_type":"","function_name":""}]},"label":"date"}],"resource":2}],"targets":[{"id":1,"matching_fields":[{"id":1,"value":{"property":[3,"foaf_name"],"transformers":[],"value_type":"property","function_name":"","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[3,""],"transformers":[],"value_type":"","function_name":""},{"property":[3,""],"transformers":[],"value_type":"","function_name":""}]},"label":"name"},{"id":2,"value":{"property":[3,""],"transformers":["to_date_immutable"],"value_type":"function","function_name":"IF","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[3,""],"transformers":[],"value_type":"","function_name":"IS_URI","":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","":{"property":[3,""],"transformers":[],"value_type":""},"IF":{"property":[3,""],"transformers":[],"value_type":"","condition":{"property":[3,""],"transformers":[],"value_type":"","":{"property":[3,""],"transformers":[],"value_type":""},"IS_URI":{"property":[3,""],"transformers":[],"value_type":""}},"THEN":{"property":[3,""],"transformers":[],"value_type":""},"ELSE":{"property":[3,""],"transformers":[],"value_type":""}},"MIN_VALUE":[]},"IS_URI":{"property":[4,"http___www_w3_org_2006_time_hasTime"],"transformers":[],"value_type":"property","function_name":"","":{"property":[3,""],"transformers":[],"value_type":""},"IF":{"property":[3,""],"transformers":[],"value_type":"","condition":{"property":[3,""],"transformers":[],"value_type":"","":{"property":[3,""],"transformers":[],"value_type":""},"IS_URI":{"property":[3,""],"transformers":[],"value_type":""}},"THEN":{"property":[3,""],"transformers":[],"value_type":""},"ELSE":{"property":[3,""],"transformers":[],"value_type":""}},"MIN_VALUE":[]},"IF":{"property":[3,""],"transformers":[],"value_type":"","condition":{"property":[3,""],"transformers":[],"value_type":"","":{"property":[3,""],"transformers":[],"value_type":""},"IS_URI":{"property":[3,""],"transformers":[],"value_type":""}},"THEN":{"property":[3,""],"transformers":[],"value_type":""},"ELSE":{"property":[3,""],"transformers":[],"value_type":""}},"MIN_VALUE":[]},"THEN":{"property":[3,""],"transformers":[],"value_type":"function","function_name":"MIN_VALUE","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[5,"rdf_value"],"transformers":[],"value_type":"property","function_name":"","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[3,""],"transformers":[],"value_type":"","function_name":""},{"property":[3,""],"transformers":[],"value_type":"","function_name":""}]},{"property":[6,"http___www_w3_org_2006_time_before"],"transformers":[],"value_type":"property","function_name":"","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[3,""],"transformers":[],"value_type":"","function_name":""},{"property":[3,""],"transformers":[],"value_type":"","function_name":""}]}]},"ELSE":{"property":[4,"http___www_w3_org_2006_time_hasTime"],"transformers":[],"value_type":"property","function_name":"","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[3,""],"transformers":[],"value_type":"","function_name":"","":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[3,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[3,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[3,""],"transformers":[],"value_type":"","function_name":""},{"property":[3,""],"transformers":[],"value_type":"","function_name":""}]}},"MIN_VALUE":[{"property":[3,""],"transformers":[],"value_type":"","function_name":""},{"property":[3,""],"transformers":[],"value_type":"","function_name":""},{"property":[3,""],"transformers":[],"value_type":"","function_name":""},{"property":[3,""],"transformers":[],"value_type":"","function_name":""}]},"label":"date"}],"resource":3}],"conditions":{"type":"AND","items":[{"id":0,"matching_field":1,"method":{"DISTANCE_IS_BETWEEN":[-18250,18250]},"method_index":1},{"id":0,"matching_field":0,"method":"=","method_index":0}]},"label":"marriage_ecartico","matching_field_labels":["name","date"]},{"id":2,"sources":[{"id":1,"matching_fields":[{"id":1,"value":{"property":[2,"uri"],"transformers":[],"value_type":"property","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[2,""],"transformers":[],"value_type":"","function_name":""},{"property":[2,""],"transformers":[],"value_type":"","function_name":""}]},"label":"uri"},{"id":2,"value":{"property":[2,"saaOnt_full_nameList"],"transformers":[],"value_type":"property","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[2,""],"transformers":[],"value_type":"","function_name":""},{"property":[2,""],"transformers":[],"value_type":"","function_name":""}]},"label":"name"},{"id":3,"value":{"property":[1,"saaOnt_registration_date"],"transformers":["to_date_immutable"],"value_type":"property","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IF":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","condition":{"property":[2,""],"transformers":[],"value_type":"","function_name":"","":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"IS_URI":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"THEN":{"property":[2,""],"transformers":[],"value_type":"","function_name":""},"ELSE":{"property":[2,""],"transformers":[],"value_type":"","function_name":""}},"MIN_VALUE":[{"property":[2,""],"transformers":[],"value_type":"","function_name":""},{"property":[2,""],"transformers":[],"value_type":"","function_name":""}]},"label":"date"}],"resource":2}],"targets":[],"conditions":{"type":"AND","items":[{"id":0,"matching_field":0,"method":{"IS_IN_SET":[{"type":"matching_label","value":1}]},"method_index":2},{"id":0,"matching_field":2,"method":{"DISTANCE_IS_BETWEEN":[-18250,18250]},"method_index":1},{"id":0,"matching_field":1,"method":"=","method_index":0}]},"label":"marriage_marriage_ecartico","matching_field_labels":["uri","name","date"]}]');

                        this.resources_count = this.resources.length;
                        this.matches_count = this.matches.length;
                    });
            },
            getJobData() {
                if (this.job_id !== '') {
                    fetch('/job/' + this.job_id)
                        .then((response) => response.json())
                        .then((data) => {
                            this.job_data = data;

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
            getResourceById(resource_id) {
                for (let i = 0; i < this.resources.length; i++) {
                    if (this.resources[i].id == resource_id)
                        return this.resources[i];
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

                this.resources.forEach(resource => {
                    let resource_copy = JSON.parse(JSON.stringify(resource));

                    if (resource_copy.filter.type != '') {
                        resource_copy.filter.conditions.forEach(condition => {
                            condition.property[0] = this.getResourceById(condition.property[0]).label;
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

                    resource_copy.related.forEach(related => {
                        related.resource = this.getResourceById(related.resource).label;
                        related.local_property = [related.local_property.toLowerCase()];
                        related.remote_property = [related.remote_property.toLowerCase()];
                        delete related.resource_index;
                    });

                    if (resource_copy.related_array) {
                        resource_copy.related = [resource_copy.related]
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