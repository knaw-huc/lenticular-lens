<template>
    <div class="border-top pb-3 pt-3">
        <div class="row justify-content-between">
            <div class="form-group col-2">
                <label :for="unique_id + '_label'">Field label</label>
                <input type="text" class="form-control" v-model="matching_field.label" :id="unique_id + '_label'">
            </div>

            <div class="form-group col-1">
                <button @click="$emit('remove')" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
            </div>
        </div>

        <matching-field-value-component :matching_field_value="matching_field.value" :datasets="datasets" :resources="resources" :resource_id="resource_id" :unique_id="unique_id"  :key="unique_id"/>

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
            <button type="button" class="btn btn-success w-25 form-control" @click="addTransformer($event)">+ Add Transformer</button>
        </div>
    </div>
</template>

<script>
    export default {
        data() {
            return {
                'transformers': ['ecartico_full_name', 'to_date_immutable'],
                'unique_id': 'match_' + this.match_id + '_resource_' + this.resource_id + '_field_' + this.matching_field.id,
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
                this.matching_field.value.property[0] = this.resource_id;
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
            'datasets': {},
            'resources': {},
            'match_id': '',
            'resource_id': ''
        },
    }
</script>