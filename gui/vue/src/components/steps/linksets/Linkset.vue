<template>
  <card :id="'linkset_spec_' + linksetSpec.id" type="linkset_specs" :res-id="linksetSpec.id" v-model="linksetSpec.label"
        :has-error="errors.length > 0" :has-handle="true" :has-extra-row="!!linkset"
        @show="onToggle(true)" @hide="onToggle(false)">
    <template v-slot:title-columns>
      <div v-if="!linkset" class="col-auto">
        <div class="custom-control custom-switch">
          <input type="checkbox" class="custom-control-input" autocomplete="off"
                 :id="'use_counter_' + linksetSpec.id" v-model="linksetSpec.use_counter"/>
          <label class="custom-control-label" :for="'use_counter_' + linksetSpec.id"
                 title="Matching could potentially run faster if progress tracking is disabled">
            Show matching progress
          </label>
        </div>
      </div>

      <div v-if="!isOpen" class="col-auto">
        <button class="btn btn-secondary" @click="$emit('duplicate', linksetSpec)">Duplicate</button>
      </div>

      <div v-if="linksetStatus === 'downloading' || linksetStatus === 'running'" class="col-auto">
        <button class="btn btn-danger" @click="killLinkset">Stop</button>
      </div>

      <div v-if="clusteringStatus === 'running'" class="col-auto">
        <button class="btn btn-danger" @click="killClustering">Stop</button>
      </div>

      <div v-if="!linkset || linksetStatus === 'failed'" class="col-auto">
        <button class="btn btn-secondary" @click="runLinkset()">
          Run
          <template v-if="linksetStatus === 'failed'">again</template>
        </button>
      </div>

      <div
          v-if="linksetStatus === 'done' && linkset.links_count > 0 && (!clustering || clusteringStatus === 'failed')"
          class="col-auto">
        <button type="button" class="btn btn-secondary my-1" @click="runClustering($event)">
          Cluster
          <template v-if="clusteringStatus === 'failed'">again</template>
        </button>
      </div>

      <div v-if="!isOpen" class="col-auto">
        <button-delete @click="$emit('remove')" title="Delete this linkset" :disabled="!allowDelete"/>
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
                @remove="updateEntityTypeSelection('sources', index)"
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
                @remove="updateEntityTypeSelection('targets', index)"
                ref="targetComponents"/>

            <div class="invalid-feedback" v-bind:class="{'is-invalid': errors.includes('targets')}">
              Please provide at least one target
            </div>
          </div>
        </div>
      </sub-card>

      <sub-card label="Matching Methods" :has-columns="true" :hasError="errors.includes('matching_methods')">
        <template v-slot:columns>
          <div class="col-auto">
            <div class="custom-control custom-switch">
              <input type="checkbox" class="custom-control-input" autocomplete="off"
                     :id="'fuzzy_linkset_' + linksetSpec.id" v-model="useFuzzyLogic"/>
              <label class="custom-control-label" :for="'fuzzy_linkset_' + linksetSpec.id">Use fuzzy logic</label>
            </div>
          </div>
        </template>

        <logic-box :element="linksetSpec.methods" elements-name="conditions" :is-root="true"
                   :should-have-elements="true" :group="'linkset-filters' + linksetSpec.id"
                   :uid="'linkset_' + linksetSpec.id  + '_0'"
                   :options="useFuzzyLogic ? fuzzyLogicOptions : undefined"
                   :option-groups="useFuzzyLogic ? fuzzyLogicOptionGroups : undefined"
                   validate-method-name="validateCondition" empty-elements-text="No conditions"
                   validation-failed-text="Please provide at least one condition"
                   @add="addCondition($event)" ref="matchingMethodGroupComponent">
          <template v-slot:box-slot="boxElement">
            <div v-if="useFuzzyLogic" class="col-auto">
              <range :id="'threshold_' + boxElement.index" v-model.number="boxElement.element.threshold"
                     label="Threshold" :allow-zero="false"/>
            </div>
          </template>

          <template v-slot="curCondition">
            <condition :condition="curCondition.element" :id="curCondition.uid"
                       :use-fuzzy-logic="useFuzzyLogic" @add="curCondition.add()" @remove="curCondition.remove()"/>
          </template>
        </logic-box>
      </sub-card>
    </fieldset>
  </card>
</template>

<script>
    import {EventBus} from "@/eventbus";
    import props from "@/utils/props";
    import ValidationMixin from '@/mixins/ValidationMixin';

    import LinksetSpecSourcesInfo from '../../info/LinksetSpecSourcesInfo';
    import LinksetSpecTargetsInfo from '../../info/LinksetSpecTargetsInfo';
    import MatchingMethodsInfo from '../../info/MatchingMethodsInfo';

    import Status from "./Status";
    import Condition from "./Condition";
    import EntityTypeSelection from "./EntityTypeSelection";

    import LogicBox from "../../helpers/LogicBox";

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
            LogicBox
        },
        props: {
            linksetSpec: Object,
            allowDelete: Boolean,
        },
        data() {
            return {
                isOpen: false,
                useFuzzyLogic: false,
                tNorms: Object.keys(props.tNorms),
                tConorms: Object.keys(props.tConorms),
                fuzzyLogicOptions: {...props.tNorms, ...props.tConorms},
                fuzzyLogicOptionGroups: props.fuzzyLogicOptionGroups,
            };
        },
        computed: {
            view() {
                return this.$root.getViewByIdAndType(this.linksetSpec.id, 'linkset');
            },

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
                    matchingMethodGroupValid = this.$refs.matchingMethodGroupComponent.validateLogicBox();
                matchingMethodGroupValid = this.validateField('matching_methods', matchingMethodGroupValid);

                return sourcesValid && targetsValid
                    && sourcesSelectValid && targetsSelectValid && matchingMethodGroupValid;
            },

            onToggle(isOpen) {
                this.isOpen = isOpen;
                isOpen ? this.$emit('show') : this.$emit('hide');
            },

            addCondition(group) {
                group.conditions.push({
                    method: {
                        name: '',
                        config: {},
                    },
                    sim_method: {
                        name: null,
                        config: {},
                        normalized: false,
                    },
                    fuzzy: {
                        t_norm: 'MINIMUM_T_NORM',
                        t_conorm: 'MAXIMUM_T_CONORM',
                        threshold: 0,
                    },
                    list_matching: {
                        threshold: 0,
                        is_percentage: false,
                    },
                    sources: {
                        properties: this.linksetSpec.sources
                            .filter(entityTypeSelection => entityTypeSelection !== '')
                            .reduce((acc, entityTypeSelection) => ({
                                ...acc,
                                [entityTypeSelection]: [{
                                    property: [''],
                                    transformers: []
                                }]
                            }), {}),
                        transformers: [],
                    },
                    targets: {
                        properties: this.linksetSpec.targets
                            .filter(entityTypeSelection => entityTypeSelection !== '')
                            .reduce((acc, entityTypeSelection) => ({
                                ...acc,
                                [entityTypeSelection]: [{
                                    property: [''],
                                    transformers: []
                                }]
                            }), {}),
                        transformers: [],
                    },
                });
            },

            addEntityTypeSelection(key) {
                this.linksetSpec[key].push('');
            },

            updateEntityTypeSelection(key, index, id) {
                const oldId = this.linksetSpec[key][index];

                if (id !== undefined)
                    this.$set(this.linksetSpec[key], index, id);
                else
                    this.$delete(this.linksetSpec[key], index);

                if (!this.linksetSpec[key].find(etsId => etsId === oldId))
                    this.$root.getRecursiveElements(this.linksetSpec.methods, 'conditions').forEach(condition => {
                        if (condition[key].properties.hasOwnProperty(oldId))
                            this.$delete(condition[key].properties, oldId);
                    });

                if (id !== undefined)
                    this.$root.getRecursiveElements(this.linksetSpec.methods, 'conditions').forEach(condition => {
                        if (!condition[key].properties.hasOwnProperty(id))
                            this.$set(condition[key].properties, id, [{
                                property: [''],
                                transformers: [],
                            }]);
                    });

                this.$root.updateView(this.linksetSpec.id, 'linkset',
                    new Set([...this.linksetSpec.sources, ...this.linksetSpec.targets]));
            },

            updateLogicBoxTypes(conditions) {
                if (conditions.hasOwnProperty('type')) {
                    if (this.useFuzzyLogic) {
                        if (conditions.type === 'AND')
                            conditions.type = 'MINIMUM_T_NORM';
                        if (conditions.type === 'OR')
                            conditions.type = 'MAXIMUM_T_CONORM';

                        this.$set(conditions, 'threshold', 0);
                    }
                    else {
                        if (this.tNorms.includes(conditions.type))
                            conditions.type = 'AND';
                        if (this.tConorms.includes(conditions.type))
                            conditions.type = 'OR';

                        this.$delete(conditions, 'threshold');
                    }
                }

                if (conditions.hasOwnProperty('conditions'))
                    conditions.conditions.forEach(condition => this.updateLogicBoxTypes(condition));
            },

            async runLinkset(force = false) {
                if (this.validateLinkset()) {
                    const data = await this.$root.runLinkset(this.linksetSpec.id, force);
                    if (data.result === 'exists' && confirm('This linkset already exists.\nDo you want to overwrite it with the current configuration?'))
                        await this.runLinkset(true);

                    EventBus.$emit('refresh');
                }
            },

            async runClustering() {
                await this.$root.runClustering('linkset', this.linksetSpec.id);
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
            if (this.linksetSpec.sources.length === 0)
                this.addEntityTypeSelection('sources');

            if (this.linksetSpec.targets.length === 0)
                this.addEntityTypeSelection('targets');

            this.useFuzzyLogic = !['AND', 'OR'].includes(this.linksetSpec.methods.type);
        },
        watch: {
            useFuzzyLogic() {
                this.updateLogicBoxTypes(this.linksetSpec.methods);
            },
        },
    };
</script>
