<template>
    <div class="bg-white pt-3 pb-3 row border-top mb-3">
        <div class="col">
            <div class="row justify-content-between">
                <div class="form-group col-3">
                    <label :for="'match_' + match.id + '_resource_label_' + match_resource.id">Collection to use</label>
                    <select class="form-control" v-model="match_resource.resource" @change="handleResourceChange" :id="'match_' + match.id + '_resource_label_' + match_resource.id">
                        <option disabled selected value="">Choose a collection</option>
                        <option v-for="(root_resource, index) in resources" :value="root_resource.id" v-if="match.sources.indexOf(root_resource.id) === -1">{{ root_resource.label }}</option>
                    </select>
                </div>

                <div class="form-group col-1">
                    <button @click="$emit('remove')" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
                </div>
            </div>

            <matching-field-component v-for="(matching_field, index) in match_resource.matching_fields"
                                      :matching_field="matching_field"
                                      :datasets="datasets"
                                      :resources="resources"
                                      :match_id="match.id"
                                      :resource_id="match_resource.resource"
                                      @remove="match_resource.matching_fields.splice(index, 1)"
            ></matching-field-component>

            <div class="form-group">
                <button type="button" class="btn btn-primary w-25 form-control" @click="addMatchingField($event)">+ Add Matching Field</button>
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
        data() {
            return {
                'matching_fields': [],
                'matching_fields_count': 0,
            }
        },
        methods: {
            addMatchingField(event) {
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

                this.match_resource.matching_fields.push(matching_field);
            },
            handleResourceChange() {
                if (this.matching_fields_count == 0) {
                    this.addMatchingField();
                }
            },
        },
        mounted() {
            this.matching_fields_count = this.matching_fields.length;
        },
        props: ['match', 'match_resource', 'datasets', 'resources'],
    }
</script>