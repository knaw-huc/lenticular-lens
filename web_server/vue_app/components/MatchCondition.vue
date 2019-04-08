<template>
    <div class="border mb-3 p-3" @mouseenter="hovering = true" @mouseleave="hovering = false">
        <div class="row justify-content-between">
            <div class="col-auto">
                <div class="row">
                    <label class="h4 col-auto align-self-center">Method</label>
                    <div class="col-auto form-group">
                        <v-select v-model="condition.method_index" @input="handleMethodIndexChange">
                            <option disabled selected value="">Select a method</option>
                            <option v-for="(method, index) in matching_methods" :value="index">{{ method.label }}</option>
                        </v-select>
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
                    <div class="h4 col">Sources properties</div>
                </div>
                <div v-for="(resource, index) in resources.sources" v-if="resource" class="row">
                    <div class="col">
                            <property-component :property="condition.sources[index]" @resetProperty="resetProperty('sources', index, $event)"/>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="resources.targets.length > 0" class="row pl-5 mb-3">
            <div class="col">
                <div class="row">
                    <div class="h4 col">Targets properties</div>
                </div>
                <div v-for="(resource, index) in resources.targets" v-if="resource" class="row">
                    <div class="col">
                            <property-component :property="condition.targets[index]" @resetProperty="resetProperty('targets', index, $event)"/>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
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
            resetProperty(resource_type, resource_index, property_index) {
                let property = this.condition[resource_type][resource_index];
                let new_property = property.slice(0, property_index);
                new_property.push('');
                if (new_property.length % 2 > 0) {
                    new_property.push('');
                }

                this.$set(this.condition[resource_type], resource_index, new_property);
            },
        },
        props: ['condition', 'match_id'],
    }
</script>