<template>
  <card :id="'match_' + match.id" type="matches" v-model="match.label"
        :has-error="errors.length > 0" :has-handle="true" :has-extra-row="!!alignment">
    <template v-slot:title-columns>
      <div class="col-auto">
        <b-button variant="info" @click="$emit('duplicate', match)">Duplicate</b-button>
      </div>

      <div v-if="alignmentStatus === 'downloading' || alignmentStatus === 'running'" class="col-auto">
        <b-button variant="info" @click="killAlignment">
          Kill
        </b-button>
      </div>

      <div v-if="!alignment || alignmentStatus === 'failed'" class="col-auto">
        <b-button variant="info" @click="runAlignment">
          Run
          <template v-if="alignmentStatus === 'failed'">again</template>
        </b-button>
      </div>

      <div v-if="alignmentStatus === 'done'" class="col-auto">
        <button v-if="clustering && clustering !== 'running'" type="button" class="btn btn-info my-1"
                @click="runClustering($event)" :disabled="association === ''"
                :title="association === '' ? 'Choose an association first' : ''">
          Reconcile
        </button>

        <button v-else-if="!clustering && clustering !== 'running'" type="button" class="btn btn-info my-1"
                @click="runClustering($event)">
          Cluster
          <template v-if="association !== ''"> &amp; Reconcile</template>
        </button>
      </div>

      <div v-if="alignmentStatus === 'done' && associationFiles" class="col-auto">
        <select class="col-auto form-control association-select my-1" v-model="association"
                :id="'match_' + match.id + '_association'">
          <option value="">No association</option>
          <option v-for="association_file_name in associationFiles" :value="association_file_name">
            {{ association_file_name }}
          </option>
        </select>
      </div>

      <div v-if="!alignment" class="col-auto">
        <button-delete @click="$emit('remove')" title="Delete this Alignment"/>
      </div>
    </template>

    <template v-slot:columns>
      <div class="col">
        <sub-card v-if="alignment" :is-first="true" class="small">
          <div class="row align-items-center justify-content-center">
            <div v-if="running" class="col-auto">
              <loading :small="true"/>
            </div>

            <div class="col-auto">
              <div class="row justify-content-center">
                <div class="col-auto">
                  <div>
                    <strong>Status: </strong>
                    {{ status }}
                  </div>
                </div>
              </div>

              <div v-if="alignmentStatus === 'failed'" class="row justify-content-center">
                <div class="col-auto">
                  <div class="font-italic">{{ alignment.failed_message }}</div>
                </div>
              </div>

              <div class="row justify-content-center mt-1">
                <div class="col-auto">
                  <template v-if="alignmentStatus === 'waiting'">
                    <div>
                      <strong>Request: </strong>
                      {{ alignment.requested_at | moment("MMMM Do YYYY, hh:mm") }}

                      <span class="font-italic">
                        (<duration :from="alignment.requested_at"/>)
                      </span>
                    </div>
                  </template>

                  <template v-else-if="alignmentStatus === 'downloading' || alignmentStatus === 'running'">
                    <div>
                      <strong>Start: </strong>
                      {{ alignment.processing_at | moment("MMMM Do YYYY, hh:mm") }}

                      <span class="font-italic">
                        (<duration :from="alignment.processing_at"/>)
                      </span>
                    </div>
                  </template>

                  <template v-else>
                    <div>
                      <strong>Matching duration: </strong>
                      <duration class="font-italic" :from="alignment.processing_at" :until="alignment.finished_at"/>
                    </div>
                  </template>
                </div>
              </div>

              <div v-if="clustering" class="row justify-content-center">
                <div class="col-auto">
                  <template v-if="clusteringStatus === 'waiting'">
                    <div>
                      <strong>Request clustering: </strong>
                      {{ clustering.requested_at | moment("MMMM Do YYYY, hh:mm") }}

                      <span class="font-italic">
                        (<duration :from="clustering.requested_at"/>)
                      </span>
                    </div>
                  </template>

                  <template v-else-if="clusteringStatus === 'running'">
                    <div>
                      <strong>Start clustering: </strong>
                      {{ clustering.processing_at | moment("MMMM Do YYYY, hh:mm") }}

                      <span class="font-italic">
                        (<duration :from="clustering.processing_at"/>)
                      </span>
                    </div>
                  </template>

                  <template v-else>
                    <div>
                      <strong>Clustering duration: </strong>
                      <duration class="font-italic" :from="clustering.processing_at" :until="clustering.finished_at"/>
                    </div>
                  </template>
                </div>
              </div>

              <div class="row justify-content-center mt-1">
                <div class="col-auto">
                  <div v-if="clustering">
                    <strong>Clusters found: </strong>
                    {{ clustering.clusters_count ? clustering.clusters_count.toLocaleString('en') : 0 }}
                    <span v-if="clusteringStatus === 'running'" class="font-italic">so far</span>
                  </div>
                  <div>
                    <strong>Links found: </strong>
                    {{ alignment.links_count ? alignment.links_count.toLocaleString('en') : 0 }}

                    <span v-if="alignmentStatus === 'running' && !alignment.distinct_links_count" class="font-italic">
                      so far
                    </span>
                    <span v-else-if="alignment.links_count > alignment.distinct_links_count"
                          class="font-italic text-info">
                      ({{ alignment.distinct_links_count.toLocaleString('en') }} distinct links)
                    </span>
                  </div>
                </div>

                <div class="col-auto">
                  <div>
                    <strong>Resources in source: </strong>
                    {{ alignment.sources_count ? alignment.sources_count.toLocaleString('en') : 0 }}

                    <span v-if="alignmentStatus === 'running' && !alignment.distinct_sources_count" class="font-italic">
                      so far
                    </span>
                    <span v-else-if="alignment.sources_count > alignment.distinct_sources_count"
                          class="font-italic text-info">
                      ({{ alignment.distinct_sources_count.toLocaleString('en') }} distinct resources)
                    </span>
                  </div>
                  <div>
                    <strong>Resources in target: </strong>
                    {{ alignment.targets_count ? alignment.targets_count.toLocaleString('en') : 0 }}

                    <span v-if="alignmentStatus === 'running' && !alignment.distinct_targets_count" class="font-italic">
                      so far
                    </span>
                    <span v-else-if="alignment.targets_count > alignment.distinct_targets_count"
                          class="font-italic text-info">
                      ({{ alignment.distinct_targets_count.toLocaleString('en') }} distinct resources)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </sub-card>
      </div>
    </template>

    <fieldset :disabled="!!alignment">
      <sub-card>
        <div class="row">
          <div class="col form-check">
            <b-form-checkbox
                :id="'match_' + match.id + '_is_association'"
                v-model.boolean="match.is_association"
                title="Check this box if this Alignment is intended for creating associations">
              Association
            </b-form-checkbox>
          </div>
        </div>
      </sub-card>

      <sub-card label="Sources" :has-info="true" add-button="Add a Collection as a Source"
                :hasError="errors.includes('sources') || errors.includes('sources_select')"
                @add="addMatchResource('sources', $event)">
        <template v-slot:info>
          <match-sources-info/>
        </template>

        <div class="row pl-5 mt-2">
          <div class="col">
            <match-resource
                v-for="(matchResource, index) in match.sources"
                :key="index"
                :match-resource-id="'source_' + index"
                :match="match"
                :match-resource="$root.getResourceById(matchResource)"
                resources-key="sources"
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
                :hasError="errors.includes('targets') || errors.includes('targets_select')"
                @add="addMatchResource('targets', $event)">
        <template v-slot:info>
          <match-targets-info/>
        </template>

        <div class="row pl-5 mt-2">
          <div class="col">
            <match-resource
                v-for="(matchResource, index) in match.targets"
                :key="index"
                :match-resource-id="'target_' + index"
                :match="match"
                :match-resource="$root.getResourceById(matchResource)"
                resources-key="targets"
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
                :hasError="errors.includes('matching-methods') || errors.includes('match-against')">
        <template v-slot:info>
          <match-matching-methods-info/>
        </template>

        <div class="row mt-3">
          <div class="form-group col">
            <label :for="'match_against_' + match.id">Match results should match results in set:</label>

            <select class="form-control h-auto mr-2" v-model="match.match_against" :id="'match_against_' + match.id"
                    v-bind:class="{'is-invalid': errors.includes('match-against')}">
              <option disabled selected value="">Select an alignment</option>
              <option v-for="m in $root.matches" v-if="match.id !== m.id" :value="m.id">{{ m.label }}</option>
            </select>

            <small class="form-text text-muted mt-2">
              When an alignment is selected, it plays the role of a filter by removing all matched pairs found
              that are not in the selected alignment set.
            </small>

            <div class="invalid-feedback" v-show="errors.includes('match-against')">
              You have to run the selected alignment first, before you can run this alignment
            </div>
          </div>
        </div>

        <conditions-group :conditions-group="match.methods"
                          :is-root="true"
                          :should-have-conditions="true"
                          group="matches-filters"
                          :uid="'match_' + match.id  + '_group_0'"
                          validate-method-name="validateMatchCondition"
                          v-slot="curCondition"
                          @add="addMatchCondition($event)"
                          ref="matchingMethodGroupComponent">
          <match-condition
              :condition="curCondition.condition" :index="curCondition.index"
              @add="curCondition.add()" @remove="curCondition.remove()"/>
        </conditions-group>
      </sub-card>
    </fieldset>
  </card>
</template>

<script>
    import MatchSourcesInfo from '../../info/MatchSourcesInfo';
    import MatchTargetsInfo from '../../info/MatchTargetsInfo';
    import MatchMatchingMethodsInfo from '../../info/MatchMatchingMethodsInfo';

    import MatchResource from './MatchResource';
    import MatchCondition from "./MatchCondition";

    import ConditionsGroup from "../../helpers/ConditionsGroup";
    import ValidationMixin from '../../../mixins/ValidationMixin';

    export default {
        name: "Match",
        mixins: [ValidationMixin],
        components: {
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
        data() {
            return {
                association: '',
                associationFiles: [],
            };
        },
        computed: {
            alignment() {
                return this.$root.alignments.find(alignment => alignment.alignment === this.match.id);
            },

            clustering() {
                return this.$root.clusterings.find(clustering => clustering.alignment === this.match.id);
            },

            alignmentStatus() {
                if (!this.alignment)
                    return null;

                return this.alignment.status;
            },

            clusteringStatus() {
                if (!this.clustering)
                    return null;

                return this.clustering.status;
            },

            running() {
                return this.alignmentStatus === 'downloading' ||
                    this.alignmentStatus === 'running' ||
                    this.clusteringStatus === 'running';
            },

            status() {
                let alignmentStatus = null;
                if (this.alignment) {
                    switch (this.alignmentStatus) {
                        case 'done':
                            alignmentStatus = 'Matched';
                            break;
                        case 'failed':
                        case 'waiting':
                        case 'downloading':
                        case 'running':
                        default:
                            alignmentStatus = `Matching ${this.alignmentStatus}`;
                    }
                }

                let clusteringStatus = null;
                let reconciliationStatus = null;
                if (this.clustering) {
                    switch (this.clusteringStatus) {
                        case 'done':
                            clusteringStatus = 'Clustered';
                            if (this.clustering.association)
                                reconciliationStatus = 'Reconciled';
                            break;
                        case 'failed':
                        case 'waiting':
                        case 'running':
                        default:
                            if (this.clustering.association)
                                reconciliationStatus = `Reconciliation ${this.clusteringStatus}`;
                            if (this.clustering.clusters_count)
                                clusteringStatus = 'Clustered';
                    }
                }

                return [alignmentStatus, clusteringStatus, reconciliationStatus]
                    .filter(status => status !== null)
                    .join(' - ');
            },
        },
        methods: {
            validateMatch(matchAgainstValidiation = false) {
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
                    matchingMethodGroupValid = this.$refs.matchingMethodGroupComponent.validateConditionsGroup();
                matchingMethodGroupValid = this.validateField('matching-methods', matchingMethodGroupValid);

                let matchAgainstValid = true;
                if (matchAgainstValidiation && this.match.match_against) {
                    const alignment = this.$root.alignments
                        .find(alignment => alignment.alignment === this.match.match_against);
                    matchAgainstValid = this.validateField('match-against', alignment && alignment.status === 'done');
                }

                return sourcesValid && targetsValid
                    && sourcesSelectValid && targetsSelectValid && matchingMethodGroupValid && matchAgainstValid;
            },

            addMatchCondition(group) {
                group.conditions.push({
                    method_name: '',
                    method_value: {},
                    sources: this.match.sources.reduce((acc, resource) => {
                        acc[resource] = [{'property': [resource, '']}];
                        return acc;
                    }, {}),
                    targets: this.match.targets.reduce((acc, resource) => {
                        acc[resource] = [{'property': [resource, '']}];
                        return acc;
                    }, {}),
                });
            },

            addMatchResource(resourcesKey, event) {
                if (event) event.target.blur();
                this.match[resourcesKey].push('');
            },

            updateConditions(group, resourcesKey, value, isInsert) {
                group.conditions.forEach(condition => {
                    if (isInsert)
                        this.$set(condition[resourcesKey], value, [{'property': [value, '']}]);
                    else
                        this.$delete(condition[resourcesKey], value);

                    if (condition.conditions)
                        this.updateConditions(condition, resourcesKey, value, isInsert);
                });
            },

            updateMatchResource(resourcesKey, resourceIndex, value) {
                const resourceId = this.match[resourcesKey][resourceIndex];

                this.$set(this.match[resourcesKey], resourceIndex, value);
                this.updateConditions(this.match.methods, resourcesKey, value, true);

                this.updateProperties(resourceId, value);
            },

            deleteMatchResource(resourcesKey, resourceIndex) {
                const resourceId = this.match[resourcesKey][resourceIndex];
                if (this.match[resourcesKey].length < 1)
                    this.addMatchResource(resourcesKey);

                this.updateConditions(this.match.methods, resourcesKey, resourceIndex, false);
                this.$delete(this.match[resourcesKey], resourceIndex);

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

            async runAlignment(force = false) {
                if (!this.validateMatch(true))
                    return;

                const data = await this.$root.runAlignment(this.match.id, force);
                if (data.result === 'exists' && confirm('This Alignment job already exists.\nDo you want to overwrite it with the current configuration?'))
                    await this.runAlignment(true);

                this.$emit('refresh');
            },

            async killAlignment() {
                await this.$root.killAlignment(this.match.id);
                this.$emit('refresh');
            },

            async runClustering() {
                const associationFile = this.association !== '' ? this.association : null;
                await this.$root.runClustering(this.match.id, associationFile);
                this.$emit('refresh');
            },
        },
        async mounted() {
            if (this.match.sources.length < 1)
                this.addMatchResource('sources');

            if (this.match.targets.length < 1)
                this.addMatchResource('targets');

            this.associationFiles = await this.$root.getAssociationFiles();
        }
    };
</script>

<style>
  .association-select {
    width: 160px !important;
  }
</style>
