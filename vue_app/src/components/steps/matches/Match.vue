<template>
  <card :id="'match_' + match.id" type="matches" v-model="match.label"
        :has-error="errors.length > 0" :has-handle="true" :has-extra-row="!!alignment">
    <template v-slot:title-columns>
      <div class="col-auto">
        <b-button variant="info" @click="$emit('duplicate', match)">Duplicate</b-button>
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
        <button-delete @click="$emit('remove')" size="2x" title="Delete this Alignment"/>
      </div>
    </template>

    <template v-slot:columns>
      <div class="col">
        <sub-card v-if="alignment" :is-first="true" class="small">
          <div class="row align-items-center justify-content-center">
            <div class="col-auto" v-if="alignmentStatus === 'running' || clusteringStatus === 'running'">
              <loading :small="true"/>
            </div>

            <div class="col-auto">
              <div class="row justify-content-center">
                <div class="col-auto">
                  <div v-if="clustering && clusteringStatus !== 'failed'">
                    <strong>Status: </strong>
                    Clustering {{ clusteringStatus }}
                  </div>
                  <div v-else-if="clusteringStatus === 'failed'">
                    <strong>Status: </strong>
                    {{ clustering.status }}
                  </div>
                  <div v-else-if="alignmentStatus !== 'failed'">
                    <strong>Status: </strong>
                    Alignment {{ alignmentStatus }}
                  </div>
                  <div v-else>
                    <strong>Status: </strong>
                    Alignment {{ alignment.status }}
                  </div>
                </div>
              </div>

              <div class="row justify-content-center mt-1">
                <div class="col-auto">
                  <template v-if="alignmentStatus === 'waiting'">
                    <div>
                      <strong>Request: </strong>
                      {{ alignment.requested_at }}

                      <span class="font-italic">
                        (<timeago :datetime="alignment.requested_at" :auto-update="1"/>)
                      </span>
                    </div>
                  </template>

                  <template v-else-if="alignmentStatus === 'running'">
                    <div>
                      <strong>Start: </strong>
                      {{ alignment.processing_at }}

                      <span class="font-italic">
                        (<timeago :datetime="alignment.processing_at" :auto-update="1"/>)
                      </span>
                    </div>
                  </template>

                  <template v-else>
                    <div>
                      <strong>Start alignment: </strong>
                      {{ alignment.processing_at }}

                      <span class="font-italic">
                        (<timeago :datetime="alignment.processing_at"/>)
                      </span>
                    </div>
                  </template>
                </div>
              </div>

              <div class="row justify-content-center">
                <div class="col-auto">
                  <template v-if="clustering && clusteringStatus === 'waiting'">
                    <div>
                      <strong>Request clustering: </strong>
                      {{ clustering.requested_at }}

                      <span class="font-italic">
                        (<timeago :datetime="clustering.requested_at" :auto-update="1"/>)
                      </span>
                    </div>
                  </template>

                  <template v-else-if="clustering && clusteringStatus === 'running'">
                    <div>
                      <strong>Start clustering: </strong>
                      {{ clustering.processing_at }}

                      <span class="font-italic">
                        (<timeago :datetime="clustering.processing_at" :auto-update="1"/>)
                      </span>
                    </div>
                  </template>

                  <template v-else-if="clustering">
                    <div>
                      <strong>Start clustering: </strong>
                      {{ clustering.processing_at }}

                      <span class="font-italic">
                        (<timeago :datetime="clustering.processing_at"/>)
                      </span>
                    </div>
                  </template>
                </div>
              </div>

              <div class="row justify-content-center mt-1">
                <div class="col-auto">
                  <div v-if="clustering">
                    <strong>Clusters found: </strong>
                    {{ clustering.clusters_count || 0 }}
                    <span v-if="clusteringStatus === 'running'" class="font-italic">so far</span>
                  </div>
                  <div>
                    <strong>Links found: </strong>
                    {{ alignment.links_count || 0 }}
                    <span v-if="alignmentStatus === 'running'" class="font-italic">so far</span>
                  </div>
                </div>

                <div class="col-auto">
                  <div>
                    <strong>Resources in source: </strong>
                    {{ alignment.sources_count || 0 }}
                    <span v-if="alignmentStatus === 'running'" class="font-italic">so far</span>
                  </div>
                  <div>
                    <strong>Resources in target: </strong>
                    {{ alignment.targets_count || 0 }}
                    <span v-if="alignmentStatus === 'running'" class="font-italic">so far</span>
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

      <sub-card label="Matching Methods" :has-info="true" :hasError="errors.includes('matching-methods')">
        <template v-slot:info>
          <match-matching-methods-info/>
        </template>

        <div class="row mt-3">
          <div class="form-group col">
            <label :for="'match_against_' + match.id">Match results should match results in set:</label>

            <select class="form-control h-auto mr-2" v-model="match.match_against" :id="'match_against_' + match.id">
              <option disabled selected value="">Select an alignment</option>
              <option v-for="m in $root.matches" v-if="match.id !== m.id" :value="m.id">{{ m.label }}</option>
            </select>

            <small class="form-text text-muted mt-2">
              When an alignment is selected, it plays the role of a filter by removing all matched pairs found
              that are not in the selected alignment set.
            </small>
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
                    return 'waiting';

                if (this.alignment.status === 'Finished')
                    return 'done';

                if (this.alignment.status.startsWith('FAILED'))
                    return 'failed';

                return 'running';
            },

            clusteringStatus() {
                if (!this.clustering)
                    return 'waiting';

                if (this.clustering.status === 'Finished')
                    return 'done';

                if (this.clustering.status.startsWith('FAILED'))
                    return 'failed';

                return 'running';
            },
        },
        methods: {
            async runClustering() {
                const associationFile = this.association !== '' ? this.association : null;
                await this.$root.runClustering(this.match.id, associationFile);
                this.$emit('refresh');
            },

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
                    matchingMethodGroupValid = this.$refs.matchingMethodGroupComponent.validateConditionsGroup();
                matchingMethodGroupValid = this.validateField('matching-methods', matchingMethodGroupValid);

                return sourcesValid && targetsValid
                    && sourcesSelectValid && targetsSelectValid && matchingMethodGroupValid;
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

            updateMatchResource(resourcesKey, resourceIndex, value) {
                const updateConditions = (group) => {
                    group.conditions.forEach(condition => {
                        this.$set(condition[resourcesKey], value, [{'property': [value, '']}]);
                        if (condition.conditions)
                            updateConditions(condition);
                    });
                };

                const resourceId = this.match[resourcesKey][resourceIndex];
                this.$set(this.match[resourcesKey], resourceIndex, value);

                updateConditions(this.match);
                this.updateProperties(resourceId, value);
            },

            deleteMatchResource(resourcesKey, resourceIndex) {
                const updateConditions = (group) => {
                    group.conditions.forEach(condition => {
                        this.$delete(condition[resourcesKey], resourceId);
                        if (condition.conditions)
                            updateConditions(condition);
                    });
                };

                const resourceId = this.match[resourcesKey][resourceIndex];
                if (this.match[resourcesKey].length < 1)
                    this.addMatchResource(resourcesKey);

                updateConditions(this.match);
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
                if (!this.validateMatch())
                    return;

                const data = await this.$root.runAlignment(this.match.id, force);
                if (data.result === 'exists' && confirm('This Alignment job already exists.\nDo you want to overwrite it with the current configuration?'))
                    await this.runAlignment(true);

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
