<template>
    <div class="row">
        <div class="form-group col-4">
            <select class="form-control" v-model="condition.matching_field">
                <option disabled selected value="">Select a Matching Field</option>
                <option v-for="(label, index) in matching_field_labels" :value="index">{{ label }}</option>
            </select>
        </div>

        <div class="form-group col-3">
            <select class="form-control" v-model="condition.method_index" @change="handleMethodIndexChange">
                <option disabled selected value="">Select a method</option>
                <option v-for="(method, index) in matching_methods" :value="index">{{ method.label }}</option>
            </select>
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
                            <option v-for="match in $parent.matches" :value="match.id">{{ match.label }}</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>

        <div class="form-group col-1">
            <button v-on:click="$emit('remove')" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
        </div>
    </div>
</template>

<script>
    export default {
        computed: {
            method_object() {
                return this.matching_methods[this.condition.method_index].object;
            },
        },
        data() {
            return {
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
            handleMethodIndexChange() {
                if (typeof this.method_object === 'string') {
                    this.condition.method = this.method_object;
                } else {
                    this.condition.method = {};
                    this.condition.method[this.method_object.name] = JSON.parse(JSON.stringify(this.method_object.value.type));
                    if (this.method_object.value.listItems) {
                        for (let i = 0; i < (this.method_object.value.listItems.minItems | 1); i++) {
                            this.condition.method[this.method_object.name].push(this.method_object.value.listItems.type);
                        }
                    }
                }
            },
        },
        props: ['condition', 'matching_field_labels'],
    }
</script>