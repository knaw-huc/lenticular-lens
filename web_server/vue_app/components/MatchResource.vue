<template>
    <div class="bg-white row">
        <div class="col">
            <div class="row justify-content-between">
                <div class="form-group col-auto">
                    <select class="border-0 btn-outline-info col-auto form-control h-auto shadow" v-model="match_resource.resource" @change="handleResourceChange" :id="'match_' + match.id + '_resource_label_' + match_resource_id">
                        <option disabled selected value="">Choose a collection</option>
                        <option v-for="(root_resource, index) in resources" :value="root_resource.id" v-if="match.sources.indexOf(root_resource.id) === -1">{{ root_resource.label }}</option>
                    </select>
                </div>

                <div class="form-group col-auto">
                    <button @click="$emit('remove')" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        data() {
            return {
                'matching_fields_count': 0,
            }
        },
        methods: {
            handleResourceChange() {
                if (this.matching_fields_count == 0) {

                }
            },
        },
        mounted() {
            this.matching_fields_count = this.match_resource.matching_fields.length;
        },
        props: ['match', 'match_resource', 'match_resource_id', 'datasets', 'resources'],
    }
</script>