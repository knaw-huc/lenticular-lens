<template>
    <div class="p-3 border-left">
        <div class="form-check form-check-inline">
            <input class="form-check-input" type="radio" :id="unique_id + '_value_type_property'" :name="unique_id + '_value_type'" value="property" v-model="matching_field_value.value_type">
            <label class="form-check-label" :for="unique_id + '_value_type_property'">Property</label>
        </div>
        <div class="form-check form-check-inline">
            <input class="form-check-input" type="radio" :id="unique_id + '_value_type_function'" :name="unique_id + '_value_type'" value="function" v-model="matching_field_value.value_type">
            <label class="form-check-label" :for="unique_id + '_value_type_function'">Calculated value</label>
        </div>

        <div class="row">
            <div class="col-3" v-if="matching_field_value.value_type == ''"></div>

            <property-component
                    v-if="matching_field_value.value_type == 'property'"
                    v-model="matching_field_value.property"
                    :resources="$root.$children[0].datasets"
                    :value_index.number="0"
            />

            <div class="form-group col-3" v-if="matching_field_value.value_type == 'function'">
                <select class="form-control" v-model="matching_field_value.function_name">
                    <option value="" selected disabled>Select a function</option>
                    <option v-if="function_name != ''" v-for="(function_info, function_name) in sql_value_functions" :value="function_name">{{ function_info.label }}</option>
                </select>
            </div>
        </div>

        <div v-if="function_name != ''" v-for="(field_type, field_name) in sql_value_functions[function_name].fields">
            <label>{{ field_name }}</label>

            <matching-field-boolean-component
                    v-if="field_type == 'boolean'"
                    :resources="resources"
                    :sql_boolean_functions="sql_boolean_functions"
                    :function_name="function_name"
                    :field_name="field_name"
                    :matching_field_value="matching_field_value[function_name][field_name]"
                    :resource_id="resource_id"
                    :unique_id="unique_id + '_' + function_name + '_' + field_name"
                    :key="unique_id + '_' + function_name + '_' + field_name"
                    ></matching-field-boolean-component>

            <matching-field-value-component
                    v-if="field_type == 'value'"
                    :resources="resources"
                    :matching_field_value="matching_field_value[function_name][field_name]"
                    :resource_id="resource_id"
                    :unique_id="unique_id + '_field_' + field_name"
                    :key="unique_id + '_field_' + field_name">
            </matching-field-value-component>
        </div>

        <div v-if="Array.isArray(matching_field_value[function_name])">
            <matching-field-value-component
                    v-for="(value_item, index) in matching_field_value[function_name]"
                    :resources="resources"
                    :matching_field_value="value_item"
                    :resource_id="resource_id"
                    :unique_id="unique_id + '_value_item_' + index"
                    :key="unique_id + '_value_item_' + index"
                    :removable="true"
                    @remove="matching_field_value[function_name].splice(index, 1)"
            ></matching-field-value-component>
        </div>
        <button type="button" v-if="sql_value_functions[function_name].array_items" class="btn btn-primary w-25" @click="addValueItem()">+ Add Value</button>
    </div>
</template>

<script>
    import MatchingFieldBooleanComponent from "./MatchingFieldBoolean";
    import PropertyComponent from "./PropertyComponent";

    export default {
        components: {PropertyComponent, MatchingFieldBooleanComponent},
        computed: {
            function_name() {
                return this.matching_field_value.function_name;
            },
            properties() {
                let resource = this.get_resource_by_id(this.matching_field_value.property[0]);
                return this.$root.$children[0].datasets[resource.dataset_id]['collections'][resource.collection_id];
            },
        },
        data() {
            return {
                'empty_matching_field_value': {
                    'property': [this.resource_id, ''],
                    'transformers': [],
                    'value_type': '',
                    'function_name': '',
                },
                'sql_boolean_functions': {
                    '': {
                        'label': '',
                        'fields': [],
                    },
                    'IS_NOT_NULL': {
                        'label': 'Is not null',
                        'fields': {
                            '': 'value',
                        },
                    },
                    'IS_URI': {
                        'label': 'Is URI (starts with \'http\')',
                        'fields': {
                            '': 'value',
                        },
                    },
                },
                'sql_value_functions': {
                    '': {
                        'label': '',
                        'fields': [],
                    },
                    'IF': {
                        'label': 'IF',
                        'fields': {
                            'condition': 'boolean',
                            'THEN': 'value',
                            'ELSE': 'value',
                        },
                    },
                    'MIN_VALUE': {
                        'label': 'Lowest value in list',
                        'array_items': 'value',
                        'fields': [],
                    },
                },
                'sub_function_name': '',
            }
        },
        methods: {
            addValueItem(function_name, event) {
                if (!function_name) {
                    function_name = this.matching_field_value.function_name;
                }

                if (event) {
                    event.target.blur();
                }

                let value_item = {
                    'property': [this.resource_id, ''],
                    'transformers': [],
                    'value_type': '',
                    'function_name': '',
                };

                this.matching_field_value[function_name].push(value_item);
            },
            get_resource_by_id(resource_id) {
                for (let i = 0; i < this.resources.length; i++) {
                    if (this.resources[i].id == resource_id)
                        return this.resources[i];
                }
            },
        },
        mounted() {
            let empty_matching_field_value = {
                'property': [this.resource_id, ''],
                'transformers': [],
                'value_type': '',
                'function_name': '',
            };

            Object.keys(this.sql_value_functions).forEach(value_function_name => {
                if (typeof this.matching_field_value[value_function_name] === 'undefined') {
                    if (this.sql_value_functions[value_function_name].array_items) {
                        this.$set(this.matching_field_value, value_function_name, []);
                        this.addValueItem(value_function_name);
                        this.addValueItem(value_function_name);
                    } else {
                        this.$set(this.matching_field_value, value_function_name, JSON.parse(JSON.stringify(empty_matching_field_value)));
                    }
                }

                let sql_function_fields = this.sql_value_functions[value_function_name].fields;

                Object.keys(sql_function_fields).forEach(field_name => {
                    if (typeof this.matching_field_value[value_function_name][field_name] === 'undefined') {
                        this.$set(this.matching_field_value[value_function_name], field_name, JSON.parse(JSON.stringify(empty_matching_field_value)));
                    }
                    if (sql_function_fields[field_name] == 'boolean') {
                        Object.keys(this.sql_boolean_functions).forEach(boolean_function_name => {
                            if (typeof this.matching_field_value[value_function_name][field_name][boolean_function_name] === 'undefined') {
                                this.$set(this.matching_field_value[value_function_name][field_name], boolean_function_name, JSON.parse(JSON.stringify(empty_matching_field_value)));
                            }
                        });
                    }
                });
            });
        },
        name: 'matching-field-value-component',
        props: {
            matching_field_value: {},
            resources: {},
            'resource_id': '',
            'unique_id': '',
        },
    }
</script>