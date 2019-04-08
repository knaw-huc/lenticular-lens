<template>
    <div class="border-top pb-3 pt-3">
        <matching-field-value-component :matching_field_value="matching_field.value" :resource_id="resource_id" :unique_id="unique_id"  :key="unique_id"/>

        <div v-for="(transformer, index) in matching_field.value.transformers" class="col-4">
            <div class="row">
                <div class="form-group col-8">
                    <select class="form-control" v-model="matching_field.value.transformers[index]">
                        <option value="" selected disabled>Select a function</option>
                        <option v-for="av_transformer in transformers" :value="av_transformer">{{ av_transformer }}</option>
                    </select>
                </div>

                <div class="form-group">
                    <button @click="matching_field.value.transformers.splice(index, 1)" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
                </div>
            </div>
        </div>

        <div class="form-group">
            <button-add @click="addTransformer($event)" title="Add transformer"/>
        </div>
    </div>
</template>

<script>
    export default {
        data() {
            return {
                'transformers': ['ecartico_full_name', 'to_date_immutable'],
                'unique_id': 'blah',
            }
        },
        methods: {
            addTransformer(event) {
                if (event) {
                    event.target.blur();
                }

                this.matching_field.value.transformers.push('');
            }
        },
        mounted() {
            if (typeof this.matching_field.value.property[0] !== 'number') {
                this.matching_field.value.property[0] = this.$parent.match_resource.resource;
            }
        },
        props: {
            'matching_field': {
                'value': {
                    'property': ['', ''],
                    'transformers': [],
                    'value_type': '',
                    'function_name': '',
                },
            },
            'resources': {},
            'match_id': '',
            'resource_id': ''
        },
    }
</script>