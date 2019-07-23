<template>
  <div class="border p-4 mt-4 bg-light" v-bind:class="{'is-invalid': errors.length > 0}">
    <div class="row align-items-top justify-content-between">
      <div class="col-auto" title="Expand / Collapse">
        <octicon name="chevron-down" scale="3" v-b-toggle="'match_' + match.id"></octicon>
      </div>

      <div class="col-auto">
        <div class="row">
          <edit-label v-model="match.label"/>
        </div>
        <div class="form-row">
          <div class="col form-check mb-1 pl-0">
            <b-form-checkbox
                :id="'match_' + match.id + '_is_association'"
                :disabled="!!jobResults"
                v-model.boolean="match.is_association"
                title="Check this box if this Alignment is intended for creating associations">
              Association
            </b-form-checkbox>
          </div>
        </div>
      </div>

      <div class="col">
        <div v-if="jobResults">
          <div>
            <strong>Request received at: </strong>{{ jobResults.requested_at }}
          </div>
          <div v-if="jobResults.processing_at">
            <strong>Processing started at: </strong>{{ jobResults.processing_at }}
          </div>
          <div v-if="jobResults.finished_at">
            <strong>Processing finished at: </strong>{{ jobResults.finished_at }}
          </div>
          <div>
            <strong>Status: </strong>
            <pre class="d-inline">{{ jobResults.status }}</pre>
          </div>
          <div v-if="jobResults.status === 'Finished'">
            <strong>Links found:</strong> {{ jobResults.links_count || 0 }}
          </div>
        </div>
      </div>

      <div class="col-auto">
        <b-button variant="info" @click="$emit('duplicate', match)">Duplicate</b-button>
      </div>

      <div class="col-auto">
        <b-button variant="info" @click="runAlignment">
          Run <template v-if="jobResults">again</template>
        </b-button>
      </div>

      <div class="col-auto">
        <button-delete @click="$emit('remove')" :scale="2" :disabled="!!jobResults" title="Delete this Alignment"/>
      </div>
    </div>

    <b-collapse :id="'match_' + match.id" :ref="'match_' + match.id" class="pt-4"
                accordion="matches-accordion" @shown="scrollTo('match_' + match.id)">
      <fieldset :disabled="!!jobResults">
        <div class="bg-white border p-3 justify-content-around rounded mb-4">
          <div class="row align-items-center justify-content-between mb-2">
            <div class="col-auto">
              <div class="row">
                <div class="col-auto pr-0">
                  <h3>Sources</h3>
                </div>
                <div class="col-auto pl-0">
                  <button-info popup_title="SOURCES">
                    <div class="h2">COMPOSING VIRTUAL SOURCE FROM COLLECTIONS</div>

                    <img width="700px" src="/static/images/VirtualCollection.png"/>

                    <p class="h5 text-left pt-4 pb-4">All collections of interest selected as sources are combined into
                      a <strong>SINGLE VIRTUAL COLLECTION</strong>> with the resource's id and the value of the selected
                      properties. For a single dataset, multiple <strong>SEMANTICALLY SIMILAR PROPERTIES</strong> can be
                      selected.</p>

                    <hr>

                    <img class="pb-4" width="1000px" src="/static/images/Documentation.png"/>
                  </button-info>
                </div>
              </div>
            </div>

            <div class="col-auto">
              <button-add @click="addMatchResource('sources', $event)" title="Add a Collection as a Source"/>
            </div>
          </div>

          <div class="row pl-5">
            <div class="col">
              <match-resource
                  v-for="(match_resource, index) in match.sources"
                  :match_resource_id="'source_' + index"
                  :match="match"
                  :match_resource="$root.getResourceById(match_resource)"
                  resources_key="sources"
                  @input="updateMatchResource('sources', index, $event)"
                  @remove="deleteMatchResource('sources', index)"
                  ref="sourceResourceComponents"
              ></match-resource>

              <div class="invalid-feedback d-block">
                <template v-if="errors.includes('sources')">
                  Please provide at least one source
                </template>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white border p-3 justify-content-around rounded mb-4">
          <div class="row align-items-center justify-content-between mb-2">
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

                      <li>For each collection, be it the <span class="text-info">TARGET</span> or the <span
                          class="text-info">SOURCE</span> several properties can be selected.
                      </li>

                      <li>Overall, <strong>ALL</strong> selected properties <strong>MUST</strong> be concistent for a
                        particuilar the type of <span class="text-info">MATCHING METHOD</span> in mind.
                      </li>

                      <!--                    <li>When both <span class="text-info">SOURCE</span> and <span class="text-info">TARGET</span> collections are selected, links are discovered <span class="text-info">ONLY</span> accross <span class="text-info">SOURCE'S VRTUAL COLLECTIONS</span> and <span class="text-info">TARGET'S VRTUAL COLLECTIONS</span> contrarily to selecting only <span class="text-info">SOURCE</span> colections where links are be discovered <span class="text-info">WITHIN</span> and <span class="text-info">ACCROSS</span> collections ,</li>-->
                    </ul>

                    <hr>
                  </button-info>
                </div>
              </div>
            </div>

            <div class="col-auto">
              <button-add @click="addMatchResource('targets', $event)" title="Add a Collection as a Target"/>
            </div>
          </div>

          <div class="row pl-5">
            <div class="col">
              <match-resource
                  v-for="(match_resource, index) in match.targets"
                  :match_resource_id="'target_' + index"
                  :match="match"
                  :match_resource="$root.getResourceById(match_resource)"
                  resources_key="targets"
                  @input="updateMatchResource('targets', index, $event)"
                  @remove="deleteMatchResource('targets', index)"
                  ref="targetResourceComponents"
              ></match-resource>

              <div class="invalid-feedback d-block">
                <template v-if="errors.includes('targets')">
                  Please provide at least one target
                </template>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white border p-3 rounded mb-4">
          <div class="row align-items-center justify-content-between mb-2">
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
                      More than one dataset is allowed for a <span class="text-info">SOURCE</span> or a <span
                        class="text-info">TARGET</span>.<br>
                      Only, all aligned property should be semantically similar.<br>
                      The logical expression provide a human readable of how it is implemented.
                    </div>

                    <div class="h3 pt-5 text-info">Complex Matching Scenario</div>
                    <img width="700px" src="/static/images/7_MethodFull.png">

                    <div class="h5">
                      More than one method is allowed.<br>
                      Within each method, a <strong>DISJUNCTION</strong> (<span class="text-info">OR</span>) operator is
                      applied over each pair of properties <strong>across</strong> two datasets.<br>
                      A <strong>DISJUNCTION</strong> (<span class="text-info">OR</span>) OR <strong>CONJUNCTION</strong>
                      (<span class="text-info">AND</span>) operator is necessary whenever more than one methods is
                      required.<br>
                    </div>
                  </button-info>
                </div>
              </div>
            </div>

            <div class="col-auto">
              <button-add @click="addRootCondition" title="Add a Matching Method"/>
            </div>
          </div>

          <matching-method-group
              :matching_method_group="match"
              :sources="match.sources"
              :targets="match.targets"
              :is_root="true"
              :uid="'match_' + match.id  + '_group_0'"
              :index="0"
              @promote-matching-method="promoteMatchingMethod($event)"
              @demote-matching-method-group="demoteGroup($event)"
              ref="matchingMethodGroupComponent"
          ></matching-method-group>
        </div>
      </fieldset>
    </b-collapse>
  </div>
</template>

<script>
    import MatchResource from './MatchResource'
    import MatchingMethodGroup from './MatchingMethodGroup'
    import ValidationMixin from '../mixins/ValidationMixin';

    export default {
        name: "Match",
        mixins: [ValidationMixin],
        components: {
            MatchResource,
            MatchingMethodGroup
        },
        props: {
            match: Object,
        },
        computed: {
            jobResults() {
                return this.$root.job.results.alignments[this.match.id];
            },
        },
        methods: {
            validateMatch() {
                const sourcesValid = this.validateField('sources', this.match.sources.length > 0);
                const targetsValid = this.validateField('targets', this.match.targets.length > 0);

                const sourcesSelectValid = this.validateField('sources_select',
                    !this.$refs.sourceResourceComponents
                        .map(sourceResourceComponent => sourceResourceComponent.validateResource())
                        .includes(false)
                );
                const targetsSelectValid = this.validateField('targets_select',
                    !this.$refs.targetResourceComponents
                        .map(targetResourceComponent => targetResourceComponent.validateResource())
                        .includes(false)
                );

                let matchingMethodGroupValid = true;
                if (this.$refs.matchingMethodGroupComponent)
                    matchingMethodGroupValid = this.$refs.matchingMethodGroupComponent.validateMatchingGroup();

                return sourcesValid && targetsValid && sourcesSelectValid
                    && targetsSelectValid && matchingMethodGroupValid;
            },

            addRootCondition() {
                this.$refs['matchingMethodGroupComponent'].addCondition();
            },

            demoteGroup(group_info) {
                let condition = group_info.group.conditions[group_info.index].conditions[0];
                let condition_copy = JSON.parse(JSON.stringify(condition));

                this.$set(group_info.group.conditions, group_info.index, condition_copy);
            },

            promoteMatchingMethod(matching_method_info) {
                let condition = matching_method_info.group.conditions[matching_method_info.index];
                let condition_copy = JSON.parse(JSON.stringify(condition));

                let matchingMethodGroup = {
                    'type': 'AND',
                    'conditions': [
                        condition_copy,
                        {
                            'method_name': '',
                            'method_value': {},
                            'sources': this.match.sources.reduce((acc, from_resource) => {
                                acc[from_resource] = [{'property': [from_resource, '']}];
                                return acc;
                            }, {}),
                            'targets': this.match.targets.reduce((acc, from_resource) => {
                                acc[from_resource] = [{'property': [from_resource, '']}];
                                return acc;
                            }, {}),
                        },
                    ],
                };

                this.$set(matching_method_info.group.conditions, matching_method_info.index, matchingMethodGroup);
            },

            addMatchResource(resources_key, event) {
                if (event) event.target.blur();
                this.match[resources_key].push('');
            },

            updateMatchResource(resources_key, resource_index, value) {
                const updateConditions = (group) => {
                    group.conditions.forEach(condition => {
                        this.$set(condition[resources_key], value, [{'property': [value, '']}]);
                        if (condition.conditions) {
                            updateConditions(condition);
                        }
                    });
                };

                const resourceId = this.match[resources_key][resource_index];
                this.$set(this.match[resources_key], resource_index, value);

                updateConditions(this.match);
                this.updateProperties(resourceId, value);
            },

            deleteMatchResource(resources_key, resource_index) {
                const updateConditions = (group) => {
                    group.conditions.forEach(condition => {
                        this.$delete(condition[resources_key], resourceId);
                        if (condition.conditions) {
                            updateConditions(condition);
                        }
                    });
                };

                const resourceId = this.match[resources_key][resource_index];
                if (this.match[resources_key].length < 1)
                    this.addMatchResource(resources_key);

                updateConditions(this.match);
                this.$delete(this.match[resources_key], resource_index);

                this.updateProperties(resourceId);
            },

            updateProperties(oldValue, newValue) {
                const sourcesHasValue = this.match.sources.find(res => res === oldValue);
                const targetsHasValue = this.match.targets.find(res => res === oldValue);
                const oldValueIndex = this.match.properties.findIndex(prop => prop[0] === oldValue);

                if ((oldValueIndex >= 0) && !sourcesHasValue && !targetsHasValue)
                    this.match.properties.splice(oldValueIndex, 1);

                if (newValue && !this.match.properties.find(prop => prop[0] === newValue))
                    this.match.properties.push([newValue, '']);
            },

            scrollTo(ref) {
                this.$refs[ref].$el.parentNode.scrollIntoView({'behavior': 'smooth', 'block': 'start'});
            },

            async runAlignment(force = false) {
                if (!this.validateMatch())
                    return;

                const data = await this.$root.runAlignment(this.match.id, force);
                if (data.result === 'exists' && confirm('This Alignment job already exists.\nDo you want to overwrite it with the current configuration?'))
                    await this.runAlignment(true);
            },
        },
        mounted() {
            if (this.match.conditions.length < 1)
                this.addRootCondition();

            if (this.match.sources.length < 1)
                this.addMatchResource('sources');

            if (this.match.targets.length < 1)
                this.addMatchResource('targets');
        }
    }
</script>
