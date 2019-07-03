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
            <button-delete v-on:click="$emit('remove')"
                           :disabled="isUsedInAlignmentResults()" title="Delete Collection"/>
        </div>
    </div>

    <b-collapse :id="'resource_' + resource.id" accordion="resources-accordion" :ref="'resource_' + resource.id">
        <fieldset :disabled="isUsedInAlignmentResults()">
            <div class="row">
                <div class="form-group col-8">
                    <label :for="'dataset_' + resource.id">Dataset</label>
                    <v-select v-model="resource.dataset_id" :id="'dataset_' + resource.id" v-on:change="resource.collection_id = ''"
                              v-bind:class="{'is-invalid': errors.includes('dataset')}">
                        <option value="" selected disabled>Choose a dataset</option>
                        <option v-for="(data, dataset) in datasets" v-bind:value="dataset">{{ data.title }}</option>
                    </v-select>
                    <div class="invalid-feedback" v-show="errors.includes('dataset')">
                        Please select a dataset
                    </div>
                </div>

                <div v-if="resource.dataset_id != ''" class="form-group collection-input col-4">
                    <label :for="'collection_' + resource.id">Subset</label>
                    <v-select v-model="resource.collection_id" :id="'collection_' + resource.id"
                              v-bind:class="{'is-invalid': errors.includes('collection')}">
                        <option value="" selected disabled>Choose a subset</option>
                        <option v-for="(data, collection) in datasets[resource.dataset_id].collections" v-bind:value="collection">{{ collection }}</option>
                    </v-select>
                    <div class="invalid-feedback" v-show="errors.includes('collection')">
                        Please select a subset
                    </div>
                </div>
            </div>

            <template v-if="resource.collection_id != ''">
                <div class="pb-3 pt-5 row">
                    <div class="h3 col-auto">Filter</div>
                    <div class="col-auto pl-0">
                        <button-add @click="addRootFilterCondition" title="Add Filter Condition"/>
                    </div>
                </div>

                <resource-filter-group-component
                        :datasets="datasets"
                        :filter_object="resource.filter"
                        :index="0"
                        :is_root="true"
                        :uid="'resource_' + resource.id + '_filter_group_0'"
                        ref="filterGroupComponents"
                        :resource="resource"
                        :resources="resources"
                        @promote-condition="promoteCondition($event)"
                        @demote-filter-group="demoteFilterGroup($event)"
                />

                <h3>Sample</h3>
                <div class="form-group row align-items-end">
                    <label class="col-auto" :for="'resource_' + resource.id + '_limit'">Only use a sample of this amount of records (-1 is no limit):</label>
                    <input type="number" min="-1" v-model.number="resource.limit" class="form-control col-1" :id="'resource_' + resource.id + '_limit'"
                           v-bind:class="{'is-invalid': errors.includes('limit')}">
                    <div class="invalid-feedback" v-show="errors.includes('limit')">
                        Please provide a limit, or -1 if there is no limit
                    </div>
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
                <b-collapse :id="'resource_' + resource.id + '_relations'" :ref="'resource_' + resource.id + '_relations'">
                    <div v-if="resource.related.length > 0" class="form-group form-check">
                        <input :id="resource.label + 'related_array'" class="form-check-input" type="checkbox" v-model="resource.related_array">
                        <label :for="resource.label + 'related_array'" class="form-check-label">Use relations as combined source</label>
                    </div>

                    <div v-for="(relation, index) in resource.related" class="row">
                        <div class="form-group col-4">
                            <label :for="'resource_' + resource.id + '_related_' + relation.id + '_resource'">Related collection</label>
                            <v-select v-model="relation.resource" :id="'resource_' + resource.id + '_related_' + relation.id + '_resource'"
                                      v-bind:class="{'is-invalid': errors.includes(`resource_${index}`)}">
                                <option disabled selected value="">Choose a collection</option>
                                <option v-for="(root_resource, index) in resources" :value="root_resource.id" v-if="root_resource.id != resource.id">{{ root_resource.label }}</option>
                            </v-select>
                            <div class="invalid-feedback" v-show="errors.includes(`resource_${index}`)">
                                Please provide a related collection
                            </div>
                        </div>

                        <div v-if="relation.resource > 0" class="form-group col-4">
                            <label :for="'resource_' + resource.id + '_related_' + relation.id + '_local_property'">Local property</label>
                            <v-select v-model="relation.local_property" v-bind:class="{'is-invalid': errors.includes(`local_prop_${index}`)}">
                                <option value="" selected disabled>Select local property</option>
                                <option v-for="(property_info, property) in datasets[resource.dataset_id]['collections'][resource.collection_id]" :value="property">{{ property }}</option>
                            </v-select>
                            <div class="invalid-feedback" v-show="errors.includes(`local_prop_${index}`)">
                                Please provide a local property
                            </div>
                        </div>

                        <div v-if="relation.resource > 0" class="form-group col-3">
                            <label :for="'resource_' + resource.id + '_related_' + relation.id + '_remote_property'">Remote property</label>
                            <v-select v-model="relation.remote_property" v-bind:class="{'is-invalid': errors.includes(`remote_prop_${index}`)}">
                                <option value="" selected disabled>Select remote property</option>
                                <option v-for="(property_info, property) in get_properties_for_resource(relation.resource)" :value="property">{{ property }}</option>
                            </v-select>
                            <div class="invalid-feedback" v-show="errors.includes(`remote_prop_${index}`)">
                                Please provide a remote property
                            </div>
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
        </fieldset>
    </b-collapse>
</div>
</template>

<script>
    import ResourceFilterGroupComponent from "./ResourceFilterGroup";
    import ValidationMixin from "../mixins/ValidationMixin";

    export default {
        mixins: [ValidationMixin],
        components: {
            ResourceFilterGroupComponent,
        },
        data() {
            return {
                app: this.$root.$children[0],
            }
        },
        computed: {
            resource_label() {
                if (typeof this.label_input !== 'undefined' && this.label_input !== '') {
                    this.$emit('update:label', this.label_input);
                    return this.label_input;
                }

                if (this.resource.dataset_id && this.resource.collection_id) {
                    let label = this.datasets[this.resource.dataset_id].title + ' [type: ' + this.resource.collection_id + ']';
                    this.$emit('update:label', label);
                    return label;
                }

                return 'Collection ' + this.resource.id;
            },
        },
        props: {
            'resource': Object,
            'datasets': Object,
            'resources': Array,
            initial_label: String,
        },
        methods: {
            validateResource() {
                const datasetValid = this.validateField('dataset',
                    this.resource.dataset_id && this.datasets.hasOwnProperty(this.resource.dataset_id));

                const datasets = this.datasets[this.resource.dataset_id];
                const collectionValid = this.validateField('collection',
                    this.resource.collection_id &&
                    datasets && datasets.collections.hasOwnProperty(this.resource.collection_id));

                const limit = parseInt(this.resource.limit);
                const limitValid = this.validateField('limit', !isNaN(limit) && (limit === -1 || limit > 0));

                let relatedValid = true;
                this.resource.related.forEach((related, idx) => {
                    const remoteResource = this.resources.find(res => res.id === parseInt(related.resource));
                    const resourceValid = this.validateField(`resource_${idx}`,
                        related.resource && remoteResource);

                    const localProperties = datasets && datasets.collections[this.resource.collection_id];
                    const localPropValid = this.validateField(`local_prop_${idx}`,
                        related.local_property && localProperties && localProperties.hasOwnProperty(related.local_property));

                    const remoteDatasets = remoteResource && this.datasets[remoteResource.dataset_id];
                    const remoteProperties = remoteDatasets && remoteDatasets.collections[remoteResource.collection_id];
                    const remotePropValid = this.validateField(`remote_prop_${idx}`,
                        related.remote_property && remoteProperties && remoteProperties.hasOwnProperty(related.remote_property));

                    if (!(resourceValid && localPropValid && remotePropValid))
                        relatedValid = false;
                });

                if (this.$refs[`resource_${this.resource.id}_relations`]) {
                    const relationsAreShown = this.$refs[`resource_${this.resource.id}_relations`].show;
                    if (!relatedValid && !relationsAreShown)
                        this.$root.$emit('bv::toggle::collapse', `resource_${rhis.resource.id}_relations`);
                }

                let filtersGroupsValid = true;
                if (this.$refs.filterGroupComponents)
                    filtersGroupsValid = this.$refs.filterGroupComponents.validateFilterGroup();

                const valid = collectionValid && datasetValid && limitValid && relatedValid && filtersGroupsValid;
                const isShown = this.$refs[`resource_${this.resource.id}`].show;
                if (!valid && !isShown)
                    this.$root.$emit('bv::toggle::collapse', `resource_${this.resource.id}`);

                return valid;
            },

            isUsedInAlignmentResults() {
                const alignmentsInResults = Object.keys(this.app.job_data.results.alignments);

                for (let i = 0; i < this.app.matches.length; i++) {
                    const match = this.app.matches[i];

                    if (alignmentsInResults.includes(match.id.toString()) &&
                        (match.sources.includes(this.resource.id.toString())
                            || match.targets.includes(this.resource.id.toString()))) {
                        return true;
                    }
                }

                return false;
            },

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
            addRootFilterCondition() {
                this.$refs['filterGroupComponents'].addFilterCondition();
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

                this.$set(condition_info.filter_object.conditions, condition_info.index, filter_group);
            },
        },
        mounted() {
            if (!this.resource.label) {
                this.$set(this.resource, 'label', this.initial_label)
            }
        },
        updated() {
            if ((!this.resource.label || this.resource_label === this.initial_label) && this.resource.dataset_id && this.resource.collection_id) {
                this.$set(this.resource, 'label', this.datasets[this.resource.dataset_id].title + ' [type: ' + this.resource.collection_id + ']')
            }
        },
    }
</script>
