<template>
<div class="border p-4 mt-4 bg-light">
    <div class="row justify-content-between">
        <div class="col-auto">
            <octicon name="chevron-down" scale="3" v-b-toggle="'resource_' + resource.id"></octicon>
        </div>

        <div class="col" v-b-toggle="'resource_' + resource.id">
            <edit-label-component v-model="resource.label" :required="true"/>
        </div>

        <div class="form-group col-1">
            <button-delete v-on:click="$emit('remove')" title="Delete Collection"/>
        </div>
    </div>

    <b-collapse :id="'resource_' + resource.id" accordion="resources-accordion">
        <div class="row">
            <div class="form-group col-8">
                <label :for="'dataset_' + resource.id">Dataset</label>
                <v-select v-model="resource.dataset_id" :id="'dataset_' + resource.id" v-on:change="resource.collection_id = ''">
                    <option value="" selected disabled>Choose a dataset</option>
                    <option v-for="(data, dataset) in datasets" v-bind:value="dataset">{{ data.title }}</option>
                </v-select>
            </div>

            <div v-if="resource.dataset_id != ''" class="form-group collection-input col-4">
                <label :for="'collection_' + resource.id">Subset</label>
                <v-select v-model="resource.collection_id" :id="'collection_' + resource.id">
                    <option value="" selected disabled>Choose a subset</option>
                    <option v-for="(data, collection) in datasets[resource.dataset_id].collections" v-bind:value="collection">{{ collection }}</option>
                </v-select>
            </div>
        </div>

        <template v-if="resource.collection_id != ''">
            <h3>Filter</h3>
            <resource-filter-group-component
                    :datasets="datasets"
                    :filter_object="resource.filter"
                    :index="0"
                    :is_root="true"
                    :uid="'resource_' + resource.id + '_filter_group_0'"
                    :resource="resource"
                    :resources="resources"
                    @promote-condition="promoteCondition($event)"
                    @demote-filter-group="demoteFilterGroup($event)"
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

            <div class="row mt-3">
                <div class="col-auto pr-0 pt-1">
                    <octicon name="chevron-down" v-b-toggle="'resource_' + resource.id + '_relations'"/>
                </div>
                <div class="col" v-b-toggle="'resource_' + resource.id + '_relations'">
                    <h3>Relations</h3>
                </div>
            </div>
            <b-collapse :id="'resource_' + resource.id + '_relations'">
                <div v-if="resource.related.length > 0" class="form-group form-check">
                    <input :id="resource.label + 'related_array'" class="form-check-input" type="checkbox" v-model="resource.related_array">
                    <label :for="resource.label + 'related_array'" class="form-check-label">Use relations as combined source</label>
                </div>

                <div v-for="(relation, index) in resource.related" class="row">
                    <div class="form-group col-4">
                        <label :for="'resource_' + resource.id + '_related_' + relation.id + '_resource'">Related collection</label>
                        <v-select v-model="relation.resource" :id="'resource_' + resource.id + '_related_' + relation.id + '_resource'">
                            <option disabled selected value="">Choose a collection</option>
                            <option v-for="(root_resource, index) in resources" :value="root_resource.id" v-if="root_resource.id != resource.id">{{ root_resource.label }}</option>
                        </v-select>
                    </div>

                    <div v-if="relation.resource > 0" class="form-group col-4">
                        <label :for="'resource_' + resource.id + '_related_' + relation.id + '_local_property'">Local property</label>
                        <v-select v-model="relation.local_property">
                            <option value="" selected disabled>Select local property</option>
                            <option v-for="(property_info, property) in datasets[resource.dataset_id]['collections'][resource.collection_id]" :value="property">{{ property }}</option>
                        </v-select>
                    </div>

                    <div v-if="relation.resource > 0" class="form-group col-3">
                        <label :for="'resource_' + resource.id + '_related_' + relation.id + '_remote_property'">Remote property</label>
                        <v-select v-model="relation.remote_property">
                            <option value="" selected disabled>Select remote property</option>
                            <option v-for="(property_info, property) in get_properties_for_resource(relation.resource)" :value="property">{{ property }}</option>
                        </v-select>
                    </div>

                    <div class="form-group col-1 align-self-end">
                        <button-delete v-on:click="resource.related.splice(index, 1)"/>
                    </div>
                </div>

                <div class="form-group">
                    <button-add v-on:click="addRelation($event)" title="Add relation"/>
                </div>
            </b-collapse>
        </template>
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
                if (typeof this.label_input !== 'undefined' && this.label_input !== '') {
                    this.$emit('update:label', this.label_input);
                    return this.label_input;
                }

                if (this.resource.dataset_id && this.resource.collection_id) {
                    let label = this.datasets[this.resource.dataset_id].title + ' --> ' + this.resource.collection_id;
                    this.$emit('update:label', label);
                    return label;
                }

                return 'Collection ' + this.resource.id;
            }
        },
        props: {
            'resource': Object,
            'datasets': Object,
            'resources': Array,
            initial_label: String,
        },
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
            demoteFilterGroup(group_info) {
                let condition = group_info.filter_object.conditions[group_info.index].conditions[0];
                let condition_copy = JSON.parse(JSON.stringify(condition));

                this.$set(group_info.filter_object.conditions, group_info.index, condition_copy);
            },
            get_properties_for_resource(resource_id) {
                let resource;

                for (let i = 0; i < this.resources.length; i++) {
                    if (this.resources[i].id == resource_id)
                        resource = this.resources[i];
                }

                return this.datasets[resource.dataset_id]['collections'][resource.collection_id];
            },
            promoteCondition(condition_info) {
                let condition = condition_info.filter_object.conditions[condition_info.index];
                let condition_copy = JSON.parse(JSON.stringify(condition));

                let filter_group = {
                    'type': 'AND',
                    'conditions': [
                        condition_copy,
                        {
                            'type': '',
                            'property': [this.resource.id, ''],
                        },
                    ],
                };

                this.$set(condition_info.filter_object.conditions, condition_info.index, filter_group)
            },
        },
        mounted() {
            if (!this.resource.label) {
                this.$set(this.resource, 'label', this.initial_label)
            }
        },
        updated() {
            if ((!this.resource.label || this.resource_label === this.initial_label) && this.resource.dataset_id && this.resource.collection_id) {
                this.$set(this.resource, 'label', this.datasets[this.resource.dataset_id].title + ' --> ' + this.resource.collection_id)
            }
        },
    }
</script>
