<template>
  <card :id="'linkset_spec_' + linksetSpec.id" type="linkset_specs" v-model="linksetSpec.label"
        :has-error="errors.length > 0" :has-handle="true" :has-extra-row="!!linkset"
        @show="onToggle(true)" @hide="onToggle(false)">
    <template v-slot:title-columns>
      <div v-if="!isOpen" class="col-auto">
        <b-button variant="info" @click="$emit('duplicate', linksetSpec)">Duplicate</b-button>
      </div>

      <div v-if="linksetStatus === 'downloading' || linksetStatus === 'running'" class="col-auto">
        <b-button variant="danger" @click="killLinkset">
          Stop
        </b-button>
      </div>

      <div v-if="clusteringStatus === 'running'" class="col-auto">
        <b-button variant="danger" @click="killClustering">
          Stop
        </b-button>
      </div>

      <div v-if="!linkset || linksetStatus === 'failed'" class="col-auto">
        <b-button variant="info" @click="runLinkset()">
          Run
          <template v-if="linksetStatus === 'failed'">again</template>
        </b-button>
      </div>

      <div v-if="linksetStatus === 'done' && linkset.distinct_links_count > 0" class="col-auto">
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

      <div v-if="linksetStatus === 'done' && linkset.distinct_links_count > 0 && $root.associationFiles"
           class="col-auto">
        <select class="col-auto form-control association-select my-1" v-model="association"
                :id="'linkset_' + linksetSpec.id + '_association'">
          <option value="">No association</option>
          <option v-for="associationFileName in $root.associationFiles" :value="associationFileName">
            {{ associationFileName }}
          </option>
        </select>
      </div>

      <div v-if="!isOpen && !linkset" class="col-auto">
        <button-delete @click="$emit('remove')" title="Delete this linkset"/>
      </div>
    </template>

    <template v-slot:columns>
      <div v-if="linkset" class="col">
        <status :linkset-spec="linksetSpec"/>
      </div>
    </template>

    <sub-card label="Description">
      <textarea class="form-control mt-3" :id="'description_' + linksetSpec.id" v-model="linksetSpec.description">
      </textarea>

      <small class="form-text text-muted mt-2">
        Provide a description for this linkset
      </small>
    </sub-card>

    <fieldset :disabled="!!linkset">
      <sub-card label="Sources" :has-info="true" add-button="Add an Entity-type Selection as a Source"
                :hasError="errors.includes('sources') || errors.includes('sources_select')"
                @add="addEntityTypeSelection('sources')">
        <template v-slot:info>
          <linkset-spec-sources-info/>
        </template>

        <div class="row pl-5 mt-2">
          <div class="col">
            <entity-type-selection
                v-for="(source, index) in linksetSpec.sources"
                :key="index"
                :id="'source_' + index"
                :linkset-spec="linksetSpec"
                :entity-type-selection="$root.getEntityTypeSelectionById(source)"
                selection-key="sources"
                @input="updateEntityTypeSelection('sources', index, $event)"
                @remove="deleteEntityTypeSelection('sources', index)"
                ref="sourceComponents"/>

            <div class="invalid-feedback" v-bind:class="{'is-invalid': errors.includes('sources')}">
              Please provide at least one source
            </div>
          </div>
        </div>
      </sub-card>

      <sub-card label="Targets" :has-info="true" add-button="Add an Entity-type Selection as a Target"
                :hasError="errors.includes('targets') || errors.includes('targets_select')"
                @add="addEntityTypeSelection('targets', $event)">
        <template v-slot:info>
          <linkset-spec-targets-info/>
        </template>

        <div class="row pl-5 mt-2">
          <div class="col">
            <entity-type-selection
                v-for="(target, index) in linksetSpec.targets"
                :key="index"
                :id="'target_' + index"
                :linkset-spec="linksetSpec"
                :entity-type-selection="$root.getEntityTypeSelectionById(target)"
                selection-key="targets"
                @input="updateEntityTypeSelection('targets', index, $event)"
                @remove="deleteEntityTypeSelection('targets', index)"
                ref="targetComponents"/>

            <div class="invalid-feedback" v-bind:class="{'is-invalid': errors.includes('targets')}">
              Please provide at least one target
            </div>
          </div>
        </div>
      </sub-card>

      <sub-card label="Matching Methods" :has-info="true" :hasError="errors.includes('matching-methods')">
        <template v-slot:info>
          <matching-methods-info/>
        </template>

        <elements-group :elements-group="linksetSpec.methods" elements-group-name="conditions" :is-root="true"
                        :should-have-elements="true" group="linkset-filters"
                        :uid="'linkset_' + linksetSpec.id  + '_group_0'"
                        validate-method-name="validateCondition" empty-elements-text="No conditions"
                        validation-failed-text="Please provide at least one condition" v-slot="curCondition"
                        @add="addCondition($event)" ref="matchingMethodGroupComponent">
          <condition
              :condition="curCondition.element" :index="curCondition.index"
              @add="curCondition.add()" @remove="curCondition.remove()"/>
        </elements-group>
      </sub-card>
    </fieldset>
  </card>
</template>

<script>
    import {EventBus} from "../../../eventbus";

    import LinksetSpecSourcesInfo from '../../info/LinksetSpecSourcesInfo';
    import LinksetSpecTargetsInfo from '../../info/LinksetSpecTargetsInfo';
    import MatchingMethodsInfo from '../../info/MatchingMethodsInfo';

    import Status from "./Status";
    import EntityTypeSelection from "./EntityTypeSelection";
    import Condition from "./Condition";

    import ElementsGroup from "../../helpers/ElementsGroup";
    import ValidationMixin from '../../../mixins/ValidationMixin';

    export default {
        name: "Linkset",
        mixins: [ValidationMixin],
        components: {
            LinksetSpecSourcesInfo,
            LinksetSpecTargetsInfo,
            MatchingMethodsInfo,
            Status,
            EntityTypeSelection,
            Condition,
            ElementsGroup
        },
        props: {
            linksetSpec: Object,
        },
        data() {
            return {
                association: '',
                isOpen: false,
            };
        },
        computed: {
            linkset() {
                return this.$root.linksets.find(linkset => linkset.spec_id === this.linksetSpec.id);
            },

            clustering() {
                return this.$root.clusterings.find(clustering =>
                    clustering.spec_type === 'linkset' && clustering.spec_id === this.linksetSpec.id);
            },

            linksetStatus() {
                return this.linkset ? this.linkset.status : null;
            },

            clusteringStatus() {
                return this.clustering ? this.clustering.status : null;
            },
        },
        methods: {
            validateLinkset() {
                const sourcesValid = this.validateField('sources', this.linksetSpec.sources.length > 0);
                const targetsValid = this.validateField('targets', this.linksetSpec.targets.length > 0);

                const sourcesSelectValid = this.validateField('sources_select',
                    !this.$refs.sourceComponents
                        .map(sourceComponent => sourceComponent.validateEntityTypeSelection())
                        .includes(false)
                );
                const targetsSelectValid = this.validateField('targets_select',
                    !this.$refs.targetComponents
                        .map(targetComponent => targetComponent.validateEntityTypeSelection())
                        .includes(false)
                );

                let matchingMethodGroupValid = true;
                if (this.$refs.matchingMethodGroupComponent)
                    matchingMethodGroupValid = this.$refs.matchingMethodGroupComponent.validateElementsGroup();
                matchingMethodGroupValid = this.validateField('matching-methods', matchingMethodGroupValid);

                return sourcesValid && targetsValid
                    && sourcesSelectValid && targetsSelectValid && matchingMethodGroupValid;
            },

            onToggle(isOpen) {
                this.isOpen = isOpen;
                isOpen ? this.$emit('show') : this.$emit('hide');
            },

            addCondition(group) {
                group.conditions.push({
                    method_name: '',
                    method_value: {},
                    sources: this.linksetSpec.sources
                        .filter(entityTypeSelection => entityTypeSelection !== '')
                        .map(entityTypeSelection => ({
                            entity_type_selection: entityTypeSelection,
                            property: [''],
                            transformers: []
                        })),
                    targets: this.linksetSpec.targets
                        .filter(entityTypeSelection => entityTypeSelection !== '')
                        .map(entityTypeSelection => ({
                            entity_type_selection: entityTypeSelection,
                            property: [''],
                            transformers: []
                        })),
                });
            },

            addEntityTypeSelection(key) {
                this.linksetSpec[key].push('');
            },

            updateEntityTypeSelection(key, index, id) {
                const oldId = this.linksetSpec[key][index];

                this.$set(this.linksetSpec[key], index, id);
                this.$root.getRecursiveElements(this.linksetSpec.methods, 'conditions').forEach(condition => {
                    condition[key].push({entityTypeSelection: id, property: [''], transformers: []});
                });

                this.updateProperties(oldId, id);
            },

            deleteEntityTypeSelection(key, index) {
                const id = this.linksetSpec[key][index];

                this.$root.getRecursiveElements(this.linksetSpec.methods, 'conditions').forEach(condition => {
                    condition[key]
                        .map((condition, idx) => condition.entityTypeSelection === id ? idx : null)
                        .filter(idx => idx !== null)
                        .sort((idxA, idxB) => idxA > idxB ? -1 : 1)
                        .forEach(idx => condition[key].splice(idx, 1));
                });
                this.$delete(this.linksetSpec[key], index);

                this.updateProperties(id);
            },

            updateProperties(oldEntityTypeSelection, newEntityTypeSelection) {
                const sourcesHasValue = this.linksetSpec.sources.find(source => source === oldEntityTypeSelection);
                const targetsHasValue = this.linksetSpec.targets.find(target => target === oldEntityTypeSelection);
                const oldValueIndex = this.linksetSpec.properties
                    .findIndex(prop => prop.entityTypeSelection === oldEntityTypeSelection);

                if ((oldValueIndex >= 0) && !sourcesHasValue && !targetsHasValue)
                    this.linksetSpec.properties.splice(oldValueIndex, 1);

                if ((newEntityTypeSelection !== undefined) &&
                    !this.linksetSpec.properties.find(prop => prop.entityTypeSelection === newEntityTypeSelection))
                    this.linksetSpec.properties.push({entityTypeSelection: newEntityTypeSelection, property: ['']});
            },

            async runLinkset(force = false) {
                const data = await this.$root.runLinkset(this.linksetSpec.id, force);
                if (data.result === 'exists' && confirm('This linkset already exists.\nDo you want to overwrite it with the current configuration?'))
                    await this.runLinkset(true);

                EventBus.$emit('refresh');
            },

            async runClustering() {
                const associationFile = this.association !== '' ? this.association : null;
                await this.$root.runClustering('linkset', this.linksetSpec.id, associationFile);
                EventBus.$emit('refresh');
            },

            async killLinkset() {
                await this.$root.killLinkset(this.linksetSpec.id);
                EventBus.$emit('refresh');
            },

            async killClustering() {
                await this.$root.killClustering('linkset', this.linksetSpec.id);
                EventBus.$emit('refresh');
            },
        },
        mounted() {
            if (this.linksetSpec.sources.length < 1)
                this.addEntityTypeSelection('sources');

            if (this.linksetSpec.targets.length < 1)
                this.addEntityTypeSelection('targets');
        },
    };
</script>
