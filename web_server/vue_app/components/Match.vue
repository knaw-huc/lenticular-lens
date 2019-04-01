<template>
<div class="border p-4 mt-4 bg-light">
    <div class="row">
        <div class="col-auto">
            <octicon name="chevron-down" scale="3" v-b-toggle="'match_' + match.id"></octicon>
        </div>

        <div class="col" v-b-toggle="'match_' + match.id">
            <div class="row">
                <edit-label-component v-model="match.label"/>
            </div>
            <div class="row">
                <div class="col form-group form-check mb-1">
                    <input type="checkbox" class="form-check-input" :id="'match_' + match.id + '_is_association'" v-model.boolean="match.is_association">
                    <label class="form-check-label" :for="'match_' + match.id + '_is_association'">Association</label>
                </div>
            </div>
        </div>

        <div class="form-group col-1">
            <button v-on:click="$emit('remove')" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
        </div>
    </div>

    <b-collapse :id="'match_' + match.id" :ref="'match_' + match.id" accordion="matches-accordion" @shown="scrollTo('match_' + match.id)">
        <div class="bg-white border p-3 justify-content-around rounded mb-4">
            <div class="row">
                <div class="col">
                    <h3>Sources</h3>
                </div>
                <div class="form-group col-auto">
                    <button type="button" class="btn btn-info w-auto font-weight-bold rounded-circle" @click="addMatchResource(match.sources, $event)">+</button>
                </div>
            </div>

            <div class="row pl-5">
                <div class="col">
                    <match-resource-component
                            v-for="(match_resource, index) in match.sources"
                            :match_resource_id="'source_' + index"
                            :match="match"
                            :match_resource="match_resource"
                            :datasets="datasets"
                            :resources="resources"
                            @remove="match.sources.splice(index, 1)"
                    ></match-resource-component>
                </div>
            </div>
        </div>


        <div class="bg-white border p-3 rounded mb-4">
            <div class="row">
                <div class="col">
                    <h3>Targets</h3>
                </div>
                <div class="form-group col-auto">
                    <button type="button" class="btn btn-info w-auto font-weight-bold rounded-circle" @click="addMatchResource(match.targets, $event)">+</button>
                </div>
            </div>

            <div class="row pl-5">
                <div class="col">
                    <match-resource-component
                            v-for="(match_resource, index) in match.targets"
                            :match_resource_id="'target_' + index"
                            :match="match"
                            :match_resource="match_resource"
                            :datasets="datasets"
                            :resources="resources"
                            @remove="match.targets.splice(index, 1)"
                    ></match-resource-component>
                    <div v-if="match.targets.length < 1" class="pl-5 text-secondary">
                        No targets specified. The sources will be used as targets.
                    </div>
                </div>
            </div>
        </div>


        <div class="bg-white border p-3 rounded mb-4">
            <div class="row justify-content-between">
                <div class="col-auto">
                    <div class="row">
                        <div class="col">
                            <h3>Matching Methods</h3>
                        </div>

                        <div class="form-group col-auto">
                            <select class="border-0 btn-outline-info col-auto form-control h-auto shadow" v-model="match.conditions.type">
                                <option value="AND">All conditions must be met (AND)</option>
                                <option value="OR">At least one of the conditions must be met (OR)</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div class="col-auto">
                    <div class="form-group">
                        <button type="button" class="btn btn-info w-auto font-weight-bold rounded-circle" @click="addCondition($event)">+</button>
                    </div>
                </div>
            </div>

            <div class="row pl-5">
                <div class="col">
                    <match-condition
                            v-for="(condition, index) in match.conditions.items"
                            :condition="condition"
                            :matching_field_labels="matching_field_labels"
                            :match_id="match.id"
                            :parent_sources="getResources(match.sources)"
                            :parent_targets="getResources(match.targets)"
                            @remove="match.conditions.items.splice(index, 1)"
                    ></match-condition>
                </div>
            </div>
        </div>
    </b-collapse>
</div>
</template>

<script>
    import MatchResource from './MatchResource'
    import MatchCondition from './MatchCondition'

    export default {
        components: {
            'match-resource-component': MatchResource,
            'match-condition': MatchCondition,
        },
        computed: {
            matching_field_labels() {
                let labels = [];

                this.match.sources[0].matching_fields.forEach(matching_field => {
                    labels.push(matching_field.label);
                });

                this.match.matching_field_labels = labels;

                return labels;
            },
        },
        data() {
            return {
                conditions_count: 0,
            }
        },
        props: ['match', 'matches', 'datasets', 'resources'],
        methods: {
            addCondition(event) {
                if (event) {
                    event.target.blur();
                }

                this.conditions_count++;

                let condition = {
                    'id': this.conditions_count,
                    'matching_field': '',
                    'method': '',
                    'method_index': '',
                    'matching_fields': [],
                };

                this.match.conditions.items.push(condition);
            },
            addMatchResource(match_resources, event) {
                if (event) {
                    event.target.blur();
                }

                let match_resource = {
                    'matching_fields': [],
                    'resource': '',
                };

                match_resources.push(match_resource);
            },
            getResourceById(id) {
                let found_resource = null;

                this.resources.forEach(resource => {
                    if (resource.id === id) {
                        found_resource = resource;
                        return false
                    }
                });

                return found_resource
            },
            getResources(resource_refs) {
                let resources = [];
                resource_refs.forEach(resource_ref => {
                    let resource = this.getResourceById(resource_ref.resource);
                    if (resource) {
                        resources.push(resource);
                    }
                });

                return resources;
            },
            scrollTo(ref) {
                this.$refs[ref].$el.parentNode.scrollIntoView({'behavior':'smooth', 'block':'start'});
            }
        },
        mounted() {
            if (this.match.sources.length < 1) {
                this.addMatchResource(this.match.sources);
            }

            this.conditions_count = this.match.conditions.items.length;
            if (this.conditions_count < 1) {
                this.addCondition();
            }

            if (!this.match.label) {
                this.$set(this.match, 'label', 'Mapping ' + this.match.id);
            }
        }
    }
</script>
