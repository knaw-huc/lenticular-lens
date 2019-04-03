<template>
    <div class="border mb-3 p-3" @mouseenter="hovering = true" @mouseleave="hovering = false">
        <div class="row justify-content-between">
            <div class="col-auto">
                <div class="row">
                    <label class="h4 col-auto align-self-center">Method</label>
                    <div class="col-auto form-group">
                        <select class="border-0 btn-outline-info form-control h-auto shadow" v-model="condition.method_index" @change="handleMethodIndexChange">
                            <option disabled selected value="">Select a method</option>
                            <option v-for="(method, index) in matching_methods" :value="index">{{ method.label }}</option>
                        </select>
                    </div>
                </div>
            </div>

            <div v-if="condition.method_index > 0 && typeof condition.method === 'object'" class="col-4">
                <div v-if="Array.isArray(condition.method[method_object.name])" class="row">
                    <div v-for="(item, index) in condition.method[method_object.name]" class="col">
                        <div v-if="typeof item === 'number'" class="form-group">
                            <input class="form-control" type="number" step="any" v-model.number="condition.method[method_object.name][index]">
                        </div>

                        <div v-if="item.type === 'matching_label'" class="form-group">
                            <select class="form-control" v-model="condition.method[method_object.name][index].value">
                                <option disabled selected value="">Select a Mapping</option>
                                <option v-for="match in $root.$children[0].matches" :value="match.id">{{ match.label }}</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <div class="form-group col-auto">
                <button-delete v-on:click="$emit('remove')" scale="1.7" :class="showOnHover" title="Delete this Method"/>
            </div>
        </div>

        <div class="row pl-5 mb-3">
            <div class="col">
                <div class="row">
                    <div class="h4 col">Sources</div>
                </div>
                <div class="row">
                    <div class="col">
                        <div v-for="resource in resources.sources" v-if="resource" class="row">
                            <div class="col">
                                <div class="row pl-5">
                                    <div class="h5 col-auto align-self-center">{{ resource.label }}</div>
                                    <div class="col-auto form-group">
                                        <select class="border-0 btn-outline-info col-auto form-control h-auto shadow">
                                            <option value="" disabled selected>Select a property</option>
<!--                                            <option-->
<!--                                                    v-for="(property_name, property_info) in $root.$children[0].datasets[resource.dataset_id][resource.collection_id]"-->
<!--                                                    :value="property_name"-->
<!--                                            >-->
<!--                                                {{ property_name }}-->
<!--                                            </option>-->
                                        </select>
                                    </div>
<!--                                    <matching-field-component-->
<!--                                        :match_id="match_id"-->
<!--                                        :resource_id="resource.id"-->
<!--                                        @remove="resource.matching_fields.splice(index, 1)"-->
<!--                                    ></matching-field-component>-->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="resources.targets.length > 0" class="row pl-5">
            <div class="col">
                <div class="row">
                    <div class="h4 col">Targets</div>
                </div>
                <div class="row">
                    <div class="col">
                        <div v-for="resource in resources.targets" class="row">
                            <div class="col">
                                <div class="row pl-5">
                                    <div class="h5 col-auto align-self-center">{{ resource.label }}</div>
                                    <div class="col-auto form-group">
                                        <select class="border-0 btn-outline-info col-auto form-control h-auto shadow">
                                            <option value="" disabled selected>Select a property</option>
                                        </select>
                                    </div>
<!--                                    <matching-field-component-->
<!--                                        :match_id="match_id"-->
<!--                                        :resource_id="resource.id"-->
<!--                                        @remove="resource.matching_fields.splice(index, 1)"-->
<!--                                    ></matching-field-component>-->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    import MatchingField from './MatchingField'

    export default {
        components: {
            'matching-field-component': MatchingField,
        },
        computed: {
            method_object() {
                return this.matching_methods[this.condition.method_index].object;
            },
            resources() {
                let app = this;

                function getResources(property_paths) {
                    let resources = [];

                    property_paths.forEach(property_path => {
                        if (property_path[0]) {
                            resources.push(app.$root.$children[0].getResourceById(property_path[0]));
                        }
                    });

                    return resources
                }

                return {
                    'sources': getResources(this.condition.sources),
                    'targets': getResources(this.condition.targets),
                }
            },
            showOnHover() {
                return this.hovering ? '' : ' invisible';
            },
        },
        data() {
            return {
                hovering: false,
                'matching_methods': [
                    {
                        'label': '=',
                        'object': '=',
                    },
                    {
                        'label': 'Trigram distance',
                        'object': {
                            'name': 'TRIGRAM_DISTANCE',
                            'value': {
                                'type': [],
                                'listItems': {
                                    'type': 0.30,
                                    'minValue': 0,
                                    'maxValue': 1,
                                },
                            },
                        },
                    },
                    {
                        'label': 'Levenshtein distance',
                        'object': {
                            'name': 'LEVENSHTEIN',
                            'value': {
                                'type': [],
                                'listItems': {
                                    'type': 1,
                                    'minValue': 0,
                                },
                            },
                        },
                    },
                    {
                        'label': 'Distance is between',
                        'object': {
                            'name': 'DISTANCE_IS_BETWEEN',
                            'value': {
                                'type': [],
                                'listItems': {
                                    'type': 0,
                                    'maxItems': 2,
                                    'minItems': 2,
                                },
                            }
                        }
                    },
                    {
                        'label': 'Is a Match in Set:',
                        'object': {
                            'name': 'IS_IN_SET',
                            'value': {
                                'type': [],
                                'listItems': {
                                    'type': {
                                        'type': 'matching_label',
                                    },
                                    'maxItems': 1,
                                    'minItems': 1,
                                },
                            },
                        },
                    },
                ],
            }
        },
        methods: {
            addMatchingField(event) {
                // Obsolete
                if (event) {
                    event.target.blur();
                }

                this.matching_fields_count++;

                let matching_field = {
                    'id': this.matching_fields_count,
                    'value': {
                        'property': [this.match_resource.resource, ''],
                        'transformers': [],
                        'value_type': '',
                        'function_name': '',
                    },
                };

                this.condition.matching_fields.push(matching_field);
            },
            handleMethodIndexChange() {
                if (typeof this.method_object === 'string') {
                    this.condition.method = this.method_object;
                } else {
                    this.condition.method = {};
                    this.condition.method[this.method_object.name] = JSON.parse(JSON.stringify(this.method_object.value.type));
                    for (let i = 0; i < (this.method_object.value.listItems.minItems || 1); i++) {
                        this.condition.method[this.method_object.name].push(this.method_object.value.listItems.type);
                    }
                }
            },
        },
        props: ['condition', 'match_id'],
    }
</script>