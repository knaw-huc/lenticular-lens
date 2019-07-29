<template>
  <card :id="'match_' + match.id" type="matches" :label="match.label"
        :hasError="errors.length > 0" :editableLabel="true" :fillLabel="false">
    <template v-slot:title-extra>
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
    </template>

    <template v-slot:columns>
      <div class="col-auto flex-fill">
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
          Run
          <template v-if="jobResults">again</template>
        </b-button>
      </div>

      <div class="col-auto">
        <button-delete @click="$emit('remove')" :scale="2" :disabled="!!jobResults" title="Delete this Alignment"/>
      </div>
    </template>

    <fieldset :disabled="!!jobResults">
      <sub-card label="Sources" :has-info="true" add-button="Add a Collection as a Source"
                @add="addMatchResource('sources', $event)">
        <template v-slot:info>
          <match-sources-info/>
        </template>

        <div class="row pl-5">
          <div class="col">
            <match-resource
                v-for="(match_resource, index) in match.sources"
                :key="index"
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
      </sub-card>

      <sub-card label="Targets" :has-info="true" add-button="Add a Collection as a Target"
               @add="addMatchResource('targets', $event)">
        <template v-slot:info>
          <match-targets-info/>
        </template>

        <div class="row pl-5">
          <div class="col">
            <match-resource
                v-for="(match_resource, index) in match.targets"
                :key="index"
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
      </sub-card>

      <sub-card label="Matching Methods" :has-info="true"
                :add-button="match.conditions.length === 0 ? 'Add a Matching Method' : ''"
                @add="addMatchCondition(match)">
        <template v-slot:info>
          <match-matching-methods-info/>
        </template>

        <conditions-group :conditions-group="match"
                          :is-root="true"
                          :uid="'match_' + match.id  + '_group_0'"
                          v-slot="curCondition"
                          @add="addMatchCondition($event)"
                          ref="matchingMethodGroupComponent">
          <match-condition
              :condition="curCondition.condition"
              :index="curCondition.index"
              ref="matchConditionComponent"
              @add="curCondition.add()"
              @remove="curCondition.remove()"/>
        </conditions-group>
      </sub-card>
    </fieldset>
  </card>
</template>

<script>
    import Card from '../../structural/Card';
    import SubCard from '../../structural/SubCard';

    import MatchSourcesInfo from '../../info/MatchSourcesInfo';
    import MatchTargetsInfo from '../../info/MatchTargetsInfo';
    import MatchMatchingMethodsInfo from '../../info/MatchMatchingMethodsInfo';

    import MatchResource from './MatchResource'
    import MatchCondition from "./MatchCondition";

    import ConditionsGroup from "../../helpers/ConditionsGroup";
    import ValidationMixin from '../../../mixins/ValidationMixin';

    export default {
        name: "Match",
        mixins: [ValidationMixin],
        components: {
            Card,
            SubCard,
            MatchSourcesInfo,
            MatchTargetsInfo,
            MatchMatchingMethodsInfo,
            MatchResource,
            MatchCondition,
            ConditionsGroup
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

            addMatchCondition(group) {
                group.conditions.push({
                    method_name: '',
                    method_value: {},
                    sources: this.match.sources.reduce((acc, from_resource) => {
                        acc[from_resource] = [{'property': [from_resource, '']}];
                        return acc;
                    }, {}),
                    targets: this.match.targets.reduce((acc, from_resource) => {
                        acc[from_resource] = [{'property': [from_resource, '']}];
                        return acc;
                    }, {}),
                });
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
            if (this.match.sources.length < 1)
                this.addMatchResource('sources');

            if (this.match.targets.length < 1)
                this.addMatchResource('targets');
        }
    }
</script>
