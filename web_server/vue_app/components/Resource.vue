<template>
<div class="border p-4 mt-4 bg-light">
    <div class="row justify-content-between">
        <div class="col-auto">
            <octicon name="chevron-down" scale="3" v-b-toggle="'resource_' + resource.id"></octicon>
        </div>

        <div class="col" v-b-toggle="'resource_' + resource.id">
            <div class="h2">{{ resource_label }}</div>
        </div>

        <div class="form-group col-1">
            <button v-on:click="$emit('remove')" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
        </div>
    </div>

    <b-collapse :id="'resource_' + resource.id" accordion="resources-accordion">
        <div class="row">
            <div class="form-group col-8">
                <label :for="'dataset_' + resource.id">Dataset</label>
                <select v-model="resource.dataset_id" :id="'dataset_' + resource.id" class="form-control" v-on:change="resource.collection_id = ''">
                    <option value="" selected disabled>Choose a dataset</option>
                    <option v-for="(data, dataset) in datasets" v-bind:value="dataset">{{ data.title }}</option>
                </select>
            </div>

            <div v-if="resource.dataset_id != ''" class="form-group collection-input col-4">
                <label :for="'collection_' + resource.id">Subset</label>
                <select v-model="resource.collection_id" :id="'collection_' + resource.id" class="form-control">
                    <option value="" selected disabled>Choose a subset</option>
                    <option v-for="(data, collection) in datasets[resource.dataset_id].collections" v-bind:value="collection">{{ collection }}</option>
                </select>
            </div>
        </div>
            <div class="form-group col-3">
                <label :for="'resource_label_' + resource.id">Collection label</label>
                <input v-model="label_input" class="form-control" :id="'resource_label_' + resource.id" :placeholder="resource_label">
            </div>

        <div v-if="resource.collection_id != ''">
            <h3>Relations</h3>

            <div v-if="resource.related.length > 0" class="form-group form-check">
                <input :id="resource.label + 'related_array'" class="form-check-input" type="checkbox" v-model="resource.related_array">
                <label :for="resource.label + 'related_array'" class="form-check-label">Use relations as combined source</label>
            </div>

            <div v-for="(relation, index) in resource.related" class="row">
                <div class="form-group col-4">
                    <label :for="'resource_' + resource.id + '_related_' + relation.id + '_resource'">Related collection</label>
                    <select class="form-control" v-model="relation.resource" :id="'resource_' + resource.id + '_related_' + relation.id + '_resource'">
                        <option disabled selected value="">Choose a collection</option>
                        <option v-for="(root_resource, index) in resources" :value="root_resource.id" v-if="root_resource.id != resource.id">{{ root_resource.label }}</option>
                    </select>
                </div>

                <div v-if="relation.resource > 0" class="form-group col-4">
                    <label :for="'resource_' + resource.id + '_related_' + relation.id + '_local_property'">Local property</label>
                    <select class="form-control" v-model="relation.local_property">
                        <option value="" selected disabled>Select local property</option>
                        <option v-for="(property_info, property) in datasets[resource.dataset_id]['collections'][resource.collection_id]" :value="property">{{ property }}</option>
                    </select>
                </div>

                <div v-if="relation.resource > 0" class="form-group col-3">
                    <label :for="'resource_' + resource.id + '_related_' + relation.id + '_remote_property'">Remote property</label>
                    <select class="form-control" v-model="relation.remote_property">
                        <option value="" selected disabled>Select remote property</option>
                        <option v-for="(property_info, property) in get_properties_for_resource(relation.resource)" :value="property">{{ property }}</option>
                    </select>
                </div>

                <div class="form-group col-1 align-self-end">
                    <button v-on:click="resource.related.splice(index, 1)" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
                </div>
            </div>

            <div class="form-group">
                <button v-on:click="addRelation($event)" type="button" class="form-control btn btn-primary w-25">+ Add relation</button>
            </div>
        </div>

        <h3>Filter</h3>
        <resource-filter-group-component
                v-if="resource.collection_id != ''"
                :datasets="datasets"
                :filter_object="resource.filter"
                :is_root="true"
                :resource="resource"
                :resources="resources"
        />

        <h3>Sample</h3>
        <div class="form-group row align-items-end">
            <label class="col-auto" :for="'resource_' + resource.id + '_limit'">Only use a sample of this amount of records (-1 is no limit):</label>
            <input type="number" min="-1" v-model.number="resource.limit" class="form-control col-1" :id="'resource_' + resource.id + '_limit'">
        </div>
        <div class="form-check">
            <input v-model.boolean="resource.random" type="checkbox" class="form-check-input" :id="'resource_' + resource.id + '_random'">
            <label class="form-check-label" :for="'resource_' + resource.id + '_random'">Randomize order</label>
        </div>
    </b-collapse>
</div>
</template>

<script>
    import ResourceFilterGroupComponent from "./ResourceFilterGroup";

    export default {
        components: {
            ResourceFilterGroupComponent,
            },
        computed: {
            resource_label() {
                if (typeof this.label_input === 'undefined' || this.label_input == '') {
                    this.label_input = this.resource.label;
                }

                if (typeof this.label_input === 'undefined' || this.label_input == '') {
                    return 'Collection ' + this.resource.id;
                } else {
                    return this.label_input;
                }
            }
        },
        data() {
            return {
                label_input: '',
            }
        },
        props: ['resource', 'datasets', 'resources'],
        methods: {
            addRelation(event) {
                if (event) {
                    event.target.blur();
                }
                let relation = {
                    'resource': '',
                    'local_property': '',
                    'remote_property': '',
                };
                this.resource.related.push(relation);
            },
            get_properties_for_resource(resource_id) {
                let resource;

                for (let i = 0; i < this.resources.length; i++) {
                    if (this.resources[i].id == resource_id)
                        resource = this.resources[i];
                }

                return this.datasets[resource.dataset_id]['collections'][resource.collection_id];
            },
        },
        mounted() {
            this.label_input = this.resource.label = this.resource_label;
        },
        watch: {
            label_input() {
                this.$set(this.resource, 'label', this.resource_label);
                this.resources.reverse();
                this.resources.reverse();
            }
        }
    }
</script>
