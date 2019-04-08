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

        <div class="form-group col-1 text-right">
            <button-delete @click="$emit('remove')" :scale="2" title="Delete this Alignment"/>
        </div>
    </div>

    <b-collapse :id="'match_' + match.id" :ref="'match_' + match.id" accordion="matches-accordion" @shown="scrollTo('match_' + match.id)">
        <div class="bg-white border p-3 justify-content-around rounded mb-4">
            <div class="row justify-content-between">
                <div class="col-auto">
                    <div class="row">
                        <div class="col-auto pr-0">
                            <h3>Sources</h3>
                        </div>
                        <div class="col-auto pl-0">
                            <button type="button" class="btn"><octicon name="question" scale="1.3"></octicon></button>
                        </div>
                    </div>
                </div>

                <div class="form-group col-auto">
                    <button-add @click="addMatchResource('sources', $event)" title="Add a Collection as a Source"/>
                </div>
            </div>

            <div class="row pl-5">
                <div class="col">
                    <match-resource-component
                            v-for="(match_resource, index) in resources.sources"
                            :match_resource_id="'source_' + index"
                            :match="match"
                            :match_resource="match_resource"
                            @input="updateMatchResource('sources', index, $event)"
                            @remove="deleteMatchResource('sources', index)"
                    ></match-resource-component>
                </div>
            </div>
        </div>


        <div class="bg-white border p-3 justify-content-around rounded mb-4">
            <div class="row justify-content-between">
                <div class="col-auto">
                    <div class="row">
                        <div class="col-auto pr-0">
                            <h3>Targets</h3>
                        </div>
                        <div class="col-auto pl-0">
                            <button type="button" class="btn"><octicon name="question" scale="1.3"></octicon></button>
                        </div>
                    </div>
                </div>

                <div class="form-group col-auto">
                    <button-add @click="addMatchResource('targets', $event)" title="Add a Collection as a Target"/>
                </div>
            </div>

            <div class="row pl-5">
                <div class="col">
                    <match-resource-component
                            v-for="(match_resource, index) in resources.targets"
                            :match_resource_id="'target_' + index"
                            :match="match"
                            :match_resource="match_resource"
                            @input="updateMatchResource('targets', index, $event)"
                            @remove="deleteMatchResource('targets', index)"
                    ></match-resource-component>
                    <div v-if="resources.targets.length < 1" class="pl-5 text-secondary">
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
                        <button-add @click="addCondition($event)" title="Add a Matching Method"/>
                    </div>
                </div>
            </div>

            <div class="row pl-5">
                <div class="col">
                    <match-condition
                            v-for="(condition, index) in match.conditions.items"
                            :condition="condition"
                            :match_id="match.id"
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
            resources() {
                let resources = {
                    'sources': [],
                    'targets': [],
                };

                if (this.match.conditions.items.length < 1) {
                    resources.sources.push([]);
                    return resources
                }

                this.match.conditions.items[0].sources.forEach(property_path => {
                    resources.sources.push(this.$root.$children[0].getResourceById(property_path[0]));
                });
                this.match.conditions.items[0].targets.forEach(property_path => {
                    resources.targets.push(this.$root.$children[0].getResourceById(property_path[0]));
                });

                return resources
            },
        },
        props: ['match', 'matches'],
        methods: {
            addCondition(event) {
                if (event) {
                    event.target.blur();
                }

                function getEmptyResources(from_resources) {
                    let empty_resources = [];

                    from_resources.forEach(from_resource => {
                        empty_resources.push([from_resource[0], '']);
                    });

                    return empty_resources
                }

                let condition = {
                    'id': this.match.conditions.items.length,
                    'method': '',
                    'method_index': '',
                    'sources': this.match.conditions.items.length > 0 ? getEmptyResources(this.match.conditions.items[0].sources) : [],
                    'targets': this.match.conditions.items.length > 0 ? getEmptyResources(this.match.conditions.items[0].targets) : [],
                };

                this.match.conditions.items.push(condition);
            },
            addMatchResource(resources_key, event) {
                if (event) {
                    event.target.blur();
                }

                this.match.conditions.items.forEach(condition => {
                    condition[resources_key].push(['']);
                });
            },
            deleteMatchResource(resources_key, index) {
                this.match.conditions.items.forEach(condition => {
                    this.$delete(condition[resources_key], index);
                });
            },
            scrollTo(ref) {
                this.$refs[ref].$el.parentNode.scrollIntoView({'behavior':'smooth', 'block':'start'});
            },
            updateMatchResource(resources_key, index, value) {
                this.match.conditions.items.forEach(condition => {
                    this.$set(condition[resources_key], index, [value,'']);
                });
            },
        },
        mounted() {
            if (this.match.conditions.items.length < 1) {
                this.addCondition();
            }

            if (this.resources.sources.length < 1) {
                this.addMatchResource('sources');
            }
        }
    }
</script>
