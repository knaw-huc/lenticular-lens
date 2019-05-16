<template>
<div class="border p-4 mt-4 bg-light">
    <div class="row">
        <div class="col-auto">
            <octicon name="chevron-down" scale="3" v-b-toggle="'match_' + match.id"></octicon>
        </div>

        <div class="col-5" v-b-toggle="'match_' + match.id">
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
                            <button-info popup_title="SOURCES">
                                <div class="h2">COMPOSING VIRTUAL SOURCE FROM COLLECTIONS</div>

                                <img width="700px" src="/static/images/VirtualCollection.png"/>

                                <p class="h5 text-left pt-4 pb-4">All collections of interest selected as sources are combined into a <strong>SINGLE VIRTUAL COLLECTION</strong>> with the resource's id and the value of the selected properties. For a single dataset, multiple <strong>SEMANTICALLY SIMILAR PROPERTIES</strong> can be selected.</p>

                                <hr>

                                <img class="pb-4" width="1000px" src="/static/images/Documentation.png"/>
                            </button-info>
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
                            v-for="(match_resource, index) in match.sources"
                            :match_resource_id="'source_' + index"
                            :match="match"
                            :match_resource="$root.$children[0].getResourceById(match_resource)"
                            resources_key="sources"
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
                            <button-info popup_title="TARGETS">
                                <div class="h2">MATCHING SOURCE AGAINST TARGET</div>

                                <img src="/static/images/Source_Target.png" width="800px">

                                <ul class="text-left pt-5">
                                    <li>Several collections can be selected as <span class="text-info">SOURCE</span>.</li>

                                    <li>Several collections can be selected as <span class="text-info">TARGET</span>.</li>

                                    <li>For each collection, be it the <span class="text-info">TARGET</span> or the <span class="text-info">SOURCE</span> several properties can be selected.</li>

                                    <li>Overall, <strong>ALL</strong> selected properties <strong>MUST</strong> be concistent for a particuilar the type of <span class="text-info">MATCHING METHOD</span> in mind.</li>

            <!--                    <li>When both <span class="text-info">SOURCE</span> and <span class="text-info">TARGET</span> collections are selected, links are discovered <span class="text-info">ONLY</span> accross <span class="text-info">SOURCE'S VRTUAL COLLECTIONS</span> and <span class="text-info">TARGET'S VRTUAL COLLECTIONS</span> contrarily to selecting only <span class="text-info">SOURCE</span> colections where links are be discovered <span class="text-info">WITHIN</span> and <span class="text-info">ACCROSS</span> collections ,</li>-->
                                </ul>

                                <hr>
                            </button-info>
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
                            v-for="(match_resource, index) in match.targets"
                            :match_resource_id="'target_' + index"
                            :match="match"
                            :match_resource="$root.$children[0].getResourceById(match_resource)"
                            resources_key="targets"
                            @input="updateMatchResource('targets', index, $event)"
                            @remove="deleteMatchResource('targets', index)"
                    ></match-resource-component>
                </div>
            </div>
        </div>


        <div class="bg-white border p-3 rounded mb-4">
            <div class="row justify-content-between">
                <div class="col-auto">
                    <div class="row">
                        <div class="col-auto pr-0">
                            <h3>Matching Methods</h3>
                        </div>
                        <div class="col-auto pl-0">
                            <button-info popup_title="MATCHING METHODS AND LOGICAL OPERATOR">
                                <div class="h3 pt-5 text-info">Simple Matching Scenario-1</div>
                                <img width="700px" src="/static/images/4_MethodSimple.png">

                                <div class="h5">Matching two datasets using <strong>one</strong> property per dataset</div>

                                <div class="h3 pt-5 text-info">Simple Matching Scenario-2</div>
                                <img width="700px" src="/static/images/5_MethodProp.png">

                                <div class="h5">
                                    More than one property per dataset is allowed.<br>
                                    Only, all aligned property should be semantically similar.
                                </div>

                                <div class="h3 pt-5 text-info">
                                    Simple Matching Scenario-3
                                </div>
                                <img width="700px" src="/static/images/6_MethodDs.png">

                                <div class="h5">
                                    More than one dataset is allowed for a <span class="text-info">SOURCE</span> or a <span class="text-info">TARGET</span>.<br>
                                    Only, all aligned property should be semantically similar.<br>
                                    The logical expression provide a human readable of how it is implemented.
                                </div>

                                <div class="h3 pt-5 text-info">Complex Matching Scenario</div>
                                <img width="700px" src="/static/images/7_MethodFull.png">

                                <div class="h5">
                                    More than one method is allowed.<br>
                                    Within each method, a <strong>DISJUNCTION</strong> (<span class="text-info">OR</span>) operator is applied over each pair of properties <strong>across</strong> two datasets.<br>
                                    A <strong>DISJUNCTION</strong> (<span class="text-info">OR</span>) OR <strong>CONJUNCTION</strong> (<span class="text-info">AND</span>) operator is necessary whenever more than one methods is required.<br>
                                </div>
                            </button-info>
                        </div>
                    </div>
                </div>

                <div class="col-auto">
                    <div class="form-group">
                        <button-add @click="addCondition" title="Add a Matching Method"/>
                    </div>
                </div>
            </div>

            <div class="row pl-5">
                <div class="col">
                    <div class="mb-3 p-3">
                        <div class="row justify-content-between">
                            <div class="col-auto">
                                <div class="row">
                                    <label class="h4 col-auto align-self-center">Logical Operator</label>
                                    <div class="col-auto form-group">
                                        <v-select v-model="match.conditions.type">
                                            <option value="AND">All conditions must be met (AND)</option>
                                            <option value="OR">At least one of the conditions must be met (OR)</option>
                                        </v-select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row pl-5">
                <div class="col">
                    <match-condition
                            v-for="(condition, index) in match.conditions.items"
                            :condition="condition"
                            :match_id="match.id"
                            :resources="match"
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
        props: ['match', 'matches'],
        methods: {
            addCondition() {
                function getEmptyResources(from_resources) {
                    let empty_resources = {};

                    from_resources.forEach(from_resource => {
                        empty_resources[from_resource] = [{'property': [from_resource, '']}];
                    });

                    return empty_resources
                }

                let condition = {
                    'id': this.match.conditions.items.length,
                    'method': '',
                    'method_index': '',
                    'sources': getEmptyResources(this.match.sources),
                    'targets': getEmptyResources(this.match.targets),
                };

                this.match.conditions.items.push(condition);
            },
            addMatchResource(resources_key, event) {
                if (event) {
                    event.target.blur();
                }

                this.match[resources_key].push('');
            },
            deleteMatchResource(resources_key, resource_index) {
                let resource_id = this.match[resources_key][resource_index];

                this.match.conditions.items.forEach(condition => {
                    this.$delete(condition[resources_key], resource_id);
                });

                this.$delete(this.match[resources_key], resource_index);

                if (this.match[resources_key].length < 1) {
                this.addMatchResource(resources_key);
            }
            },
            scrollTo(ref) {
                this.$refs[ref].$el.parentNode.scrollIntoView({'behavior':'smooth', 'block':'start'});
            },
            updateMatchResource(resources_key, index, value) {
                this.$set(this.match[resources_key], index, value);

                this.match.conditions.items.forEach(condition => {
                    this.$set(condition[resources_key], value, [{'property': [value, '']}]);
                });
            },
        },
        mounted() {
            if (this.match.conditions.items.length < 1) {
                this.addCondition();
            }

            if (this.match.sources.length < 1) {
                this.addMatchResource('sources');
            }

            if (this.match.targets.length < 1) {
                this.addMatchResource('targets');
            }
        }
    }
</script>
