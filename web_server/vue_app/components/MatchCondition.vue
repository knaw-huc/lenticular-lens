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
                <div v-if="condition.method[method_object.name] === Object(condition.method[method_object.name])" class="row">
                    <div v-for="(item, index) in condition.method[method_object.name]" class="col">
                        <div class="form-group">
                            <label>
                                <template v-if="Object.prototype.toString.call(condition.method[method_object.name]) === '[object Object]'">
                                    {{ method_object.value.items[index].label }}
                                </template>
                                <template v-else>Value {{ index + 1 }}</template>

                                <input v-if="typeof item === 'number'" class="form-control" type="number" step="any" v-model.number="condition.method[method_object.name][index]">

                                <select v-if="item.type === 'matching_label'" class="form-control" v-model="condition.method[method_object.name][index].value">
                                    <option disabled selected value="">Select a Mapping</option>
                                    <option v-for="match in $root.$children[0].matches" :value="match.id">{{ match.label }}</option>
                                </select>
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <div class="form-group col-auto">
                <button-delete v-on:click="$emit('remove')" scale="1.7" :class="showOnHover" title="Delete this Method"/>
            </div>
        </div>

        <div class="row pl-5 mb-3" v-for="resources_key in ['sources', 'targets']">
            <div class="col">
                <div class="row">
                    <div class="h4 col-auto">{{ resources_key | capitalize }} properties</div>
                    <div v-if="unusedResources[resources_key].length > 0" class="col-auto form-group">
                        <v-select @input="condition[resources_key][$event].push({'property': [$event, '']})">
                            <option value="" disabled selected>Add property for Collection:</option>
                            <option v-for="resource in unusedResources[resources_key]" :value="resource">
                                {{ $root.$children[0].getResourceById(resource).label }}
                            </option>
                        </v-select>
                    </div>
                </div>
                <template v-for="collection_properties in condition[resources_key]">
                    <div v-for="(resource, index) in collection_properties" class="row">
                        <div class="col ml-5">
<!--                            <div v-for="(transformer, index) in resource.transformers" class="col-4">-->
<!--                                <div class="row">-->
<!--                                    <div class="form-group col-8">-->
<!--                                        <v-select v-model="resource.transformers[index]">-->
<!--                                            <option value="" selected disabled>Select a function</option>-->
<!--                                            <option v-for="av_transformer in transformers" :value="av_transformer">{{ av_transformer }}</option>-->
<!--                                        </v-select>-->
<!--                                    </div>-->

<!--                                    <div class="form-group">-->
<!--                                        <button-delete @click="resource.transformers.splice(index, 1)"/>-->
<!--                                    </div>-->
<!--                                </div>-->
<!--                            </div>-->

<!--                            <div class="form-group">-->
<!--                                <button-add @click="$root.$children[0].getOrCreate(resource, 'transformers', []).push('')" title="Add transformer"/>-->
<!--                            </div>-->

                            <property-component
                                    v-if="resource.property"
                                    :property="resource.property"
                                    @clone="collection_properties.splice(index + 1, 0, {'property': [collection_properties[index]['property'][0], '']})"
                                    @delete="$delete(collection_properties, index)"
                                    @resetProperty="resetProperty(collection_properties, index, $event)"
                            />
                        </div>
                    </div>
                </template>
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
            showOnHover() {
                return this.hovering ? '' : ' invisible';
            },
            unusedResources() {
                let resource_keys = ['sources', 'targets'];
                let unused_resources = {};

                resource_keys.forEach(resource_key => {
                    unused_resources[resource_key] = Object.keys(this.condition[resource_key]).filter(
                        resource_id => this.condition[resource_key][resource_id].length < 1
                    );
                });

                return unused_resources;
            },
        },
        data() {
            return {
                hovering: false,
                'matching_methods': [
                    {
                        'label': 'Is Equal',
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
                        'label': 'Time Delta',
                        'object': {
                            'name': 'TIME_DELTA',
                            'value': {
                                'type': {},
                                'items':{
                                    'years': {
                                        'label': 'Years',
                                        'type': 0,
                                        'minValue': 0,
                                    },
                                    'months': {
                                        'label': 'Months',
                                        'type': 0,
                                        'minValue': 0,
                                    },
                                    'days': {
                                        'label': 'Days',
                                        'type': 0,
                                        'minValue': 0,
                                    },
                                },
                            }
                        }
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
                'transformers': ['ecartico_full_name', 'to_date_immutable'],
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
                    if (Array.isArray(this.condition.method[this.method_object.name])) {
                        for (let i = 0; i < (this.method_object.value.listItems.minItems || 1); i++) {
                            this.condition.method[this.method_object.name].push(this.method_object.value.listItems.type);
                        }
                    } else {
                        Object.keys(this.method_object.value.items).forEach(value_item_key => {
                            this.condition.method[this.method_object.name][value_item_key] = this.method_object.value.items[value_item_key].type;
                        });
                    }
                }
            },
            resetProperty(properties, resource_index, property_index) {
                let property = properties[resource_index].property;
                let new_property = property.slice(0, property_index);
                new_property.push('');
                if (new_property.length % 2 > 0) {
                    new_property.push('');
                }

                this.$set(properties[resource_index], 'property', new_property);
            },
        },
        props: ['condition', 'match_id', 'resources'],
    }
</script>