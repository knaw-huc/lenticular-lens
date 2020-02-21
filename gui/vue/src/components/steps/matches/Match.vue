<template>
  <card :id="'match_' + match.id" type="matches" v-model="match.label"
        :has-error="errors.length > 0" :has-handle="true" :has-extra-row="!!alignment"
        @show="onToggle(true)" @hide="onToggle(false)">
    <template v-slot:title-columns>
      <div v-if="!isOpen" class="col-auto">
        <b-button variant="info" @click="$emit('duplicate', match)">Duplicate</b-button>
      </div>

      <div v-if="alignmentStatus === 'downloading' || alignmentStatus === 'running'" class="col-auto">
        <b-button variant="danger" @click="killAlignment">
          Stop
        </b-button>
      </div>

      <div v-if="clusteringStatus === 'running'" class="col-auto">
        <b-button variant="danger" @click="killClustering">
          Stop
        </b-button>
      </div>

      <div v-if="!alignment || alignmentStatus === 'failed'" class="col-auto">
        <b-button variant="info" @click="runAlignment()">
          Run
          <template v-if="alignmentStatus === 'failed'">again</template>
        </b-button>
      </div>

      <div v-if="alignmentStatus === 'done' && alignment.distinct_links_count > 0" class="col-auto">
        <button v-if="clustering && clustering !== 'running'" type="button" class="btn btn-info my-1"
                @click="runClustering($event)" :disabled="association === ''"
                :title="association === '' ? 'Choose an association first' : ''">
          Reconcile
          <template v-if="clusteringStatus === 'failed'">again</template>
        </button>

        <button v-else-if="!clustering" type="button" class="btn btn-info my-1" @click="runClustering($event)">
          Cluster
          <template v-if="association !== ''"> &amp; Reconcile</template>
          <template v-if="clusteringStatus === 'failed'">again</template>
        </button>
      </div>

      <div v-if="alignmentStatus === 'done' && alignment.distinct_links_count > 0 && $root.associationFiles"
           class="col-auto">
        <select class="col-auto form-control association-select my-1" v-model="association"
                :id="'match_' + match.id + '_association'">
          <option value="">No association</option>
          <option v-for="associationFileName in $root.associationFiles" :value="associationFileName">
            {{ associationFileName }}
          </option>
        </select>
      </div>

      <div v-if="!isOpen && !alignment" class="col-auto">
        <button-delete @click="$emit('remove')" title="Delete this Alignment"/>
      </div>
    </template>

    <template v-slot:columns>
      <div v-if="alignment" class="col">
        <match-status :match="match"/>
      </div>
    </template>

    <sub-card label="Description">
      <textarea class="form-control mt-3" :id="'description_' + match.id" v-model="match.description">
      </textarea>

      <small class="form-text text-muted mt-2">
        Provide a description for this alignment
      </small>
    </sub-card>

    <fieldset :disabled="!!alignment">
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
                ref="sourceResourceComponents"/>

            <div class="invalid-feedback" v-bind:class="{'is-invalid': errors.includes('sources')}">
              Please provide at least one source
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
                ref="targetResourceComponents"/>

            <div class="invalid-feedback" v-bind:class="{'is-invalid': errors.includes('targets')}">
              Please provide at least one target
            </div>
          </div>
        </div>
      </sub-card>

      <sub-card label="Matching Methods" :has-info="true"
                :hasError="errors.includes('matching-methods') || errors.includes('match-against')">
        <template v-slot:info>
          <match-matching-methods-info/>
        </template>

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
    import {EventBus} from "../../../eventbus";

    import MatchSourcesInfo from '../../info/MatchSourcesInfo';
    import MatchTargetsInfo from '../../info/MatchTargetsInfo';
    import MatchMatchingMethodsInfo from '../../info/MatchMatchingMethodsInfo';

    import MatchStatus from "./MatchStatus";
    import MatchResource from "./MatchResource";
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
            MatchStatus,
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
                isOpen: false,
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
                return this.alignment ? this.alignment.status : null;
            },

            clusteringStatus() {
                return this.clustering ? this.clustering.status : null;
            },
        },
        methods: {
            validateMatch(matchAgainstValidation = false) {
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
                if (matchAgainstValidation && this.match.match_against) {
                    const alignment = this.$root.alignments
                        .find(alignment => alignment.alignment === this.match.match_against);
                    matchAgainstValid = this.validateField('match-against', alignment && alignment.status === 'done');
                }

                return sourcesValid && targetsValid
                    && sourcesSelectValid && targetsSelectValid && matchingMethodGroupValid && matchAgainstValid;
            },

            onToggle(isOpen) {
                this.isOpen = isOpen;
                isOpen ? this.$emit('show') : this.$emit('hide');
            },

            addMatchCondition(group) {
                group.conditions.push({
                    method_name: '',
                    method_value: {},
                    sources: this.match.sources
                        .filter(resource => resource !== '')
                        .map(resource => ({resource, property: [''], transformers: []})),
                    targets: this.match.targets
                        .filter(resource => resource !== '')
                        .map(resource => ({resource, property: [''], transformers: []})),
                });
            },

            addMatchResource(resourcesKey, event) {
                this.match[resourcesKey].push('');
            },

            updateMatchResource(resourcesKey, resourceIndex, resourceId) {
                const oldResourceId = this.match[resourcesKey][resourceIndex];

                this.$set(this.match[resourcesKey], resourceIndex, resourceId);
                this.$root.getRecursiveConditions(this.match.methods).forEach(condition => {
                    condition[resourcesKey].push({resource: resourceId, property: [''], transformers: []});
                });

                this.updateProperties(oldResourceId, resourceId);
            },

            deleteMatchResource(resourcesKey, resourceIndex) {
                const resourceId = this.match[resourcesKey][resourceIndex];

                this.$root.getRecursiveConditions(this.match.methods).forEach(condition => {
                    condition[resourcesKey]
                        .map((resourceCondition, idx) => resourceCondition.resource === resourceId ? idx : null)
                        .filter(idx => idx !== null)
                        .sort((idxA, idxB) => idxA > idxB ? -1 : 1)
                        .forEach(idx => condition[resourcesKey].splice(idx, 1));
                });
                this.$delete(this.match[resourcesKey], resourceIndex);

                this.updateProperties(resourceId);
            },

            updateProperties(oldResource, newResource) {
                const sourcesHasValue = this.match.sources.find(res => res === oldResource);
                const targetsHasValue = this.match.targets.find(res => res === oldResource);
                const oldValueIndex = this.match.properties.findIndex(prop => prop.resource === oldResource);

                if ((oldValueIndex >= 0) && !sourcesHasValue && !targetsHasValue)
                    this.match.properties.splice(oldValueIndex, 1);

                if ((newResource !== undefined) &&
                    !this.match.properties.find(prop => prop.resource === newResource))
                    this.match.properties.push({resource: newResource, property: ['']});
            },

            async runAlignment(force = false) {
                if (!this.validateMatch(true))
                    return;
                const data = await this.$root.runAlignment(this.match.id, force);
                if (data.result === 'exists' && confirm('This Alignment job already exists.\nDo you want to overwrite it with the current configuration?'))
                    await this.runAlignment(true);

                EventBus.$emit('refresh');
            },

            async runClustering() {
                const associationFile = this.association !== '' ? this.association : null;
                await this.$root.runClustering(this.match.id, associationFile);
                EventBus.$emit('refresh');
            },

            async killAlignment() {
                await this.$root.killAlignment(this.match.id);
                EventBus.$emit('refresh');
            },

            async killClustering() {
                await this.$root.killClustering(this.match.id);
                EventBus.$emit('refresh');
            },
        },
        mounted() {
            if (this.match.sources.length < 1)
                this.addMatchResource('sources');

            if (this.match.targets.length < 1)
                this.addMatchResource('targets');
        },
    };
</script>

<style>
  .association-select {
    width: 160px !important;
  }
</style>
