<template>
    <div class="p-3 border-left">
        <div class="form-group col-3">
            <select class="form-control" v-model="matching_field_value.function_name">
                <option value="" selected disabled>Select a function</option>
                <option v-if="sql_function_name != ''" v-for="(function_info, sql_function_name) in sql_boolean_functions"
                        :value="sql_function_name">{{ function_info.label }}
                </option>
            </select>
        </div>
        <div v-if="matching_field_value.function_name != ''">
            <matching-field-value-component
                    v-for="(sub_field_type, sub_field_name) in sql_boolean_functions[matching_field_value.function_name].fields"
                    v-if="sub_field_type == 'value'"
                    :resources="resources"
                    :matching_field_value="matching_field_value[matching_field_value.function_name]"
                    :resource_id="resource_id"
                    :unique_id="unique_id + '_field_' + sub_field_name + '_' + matching_field_value.function_name"
                    :key="unique_id + '_field_' + sub_field_name + '_' + matching_field_value.function_name">
            </matching-field-value-component>
        </div>
    </div>
</template>

<script>
    export default {
        mounted() {
            let empty_matching_field_value = {
                'property': [this.resource_id, ''],
                'transformers': [],
                'value_type': '',
            };

            Object.keys(this.$parent.sql_value_functions).forEach(value_function_name => {
                if (typeof this.matching_field_value[value_function_name] === 'undefined') {
                    if (this.$parent.sql_value_functions[value_function_name].array_items) {
                        this.$set(this.matching_field_value, value_function_name, []);
                        this.$parent.addValueItem(value_function_name);
                        this.$parent.addValueItem(value_function_name);
                    } else {
                        this.$set(this.matching_field_value, value_function_name, JSON.parse(JSON.stringify(empty_matching_field_value)));
                    }
                }

                let sql_function_fields = this.$parent.sql_value_functions[value_function_name].fields;

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

            this.$set(this.matching_field_value, 'value_type', 'function');
        },
        name: 'matching-field-boolean-component',
        props: ['resources', 'matching_field_value', 'resource_id', 'unique_id', 'function_name', 'field_name', 'sql_boolean_functions'],
    }
</script>