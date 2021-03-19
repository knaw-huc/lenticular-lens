<template>
  <card :id="'lens_spec_' + lensSpec.id" type="lens-specs" :res-id="lensSpec.id" v-model="lensSpec.label"
        :has-error="errors.length > 0" :has-handle="true" :has-extra-row="!!lens"
        @show="onToggle(true)" @hide="onToggle(false)">
    <template v-slot:title-columns>
      <div v-if="!isOpen" class="col-auto">
        <button class="btn btn-secondary" @click="$emit('duplicate', lensSpec)">Duplicate</button>
      </div>

      <div v-if="lensStatus === 'downloading' || lensStatus === 'running'" class="col-auto">
        <button class="btn btn-danger" @click="killLens">
          Stop
        </button>
      </div>

      <div v-if="clusteringStatus === 'running'" class="col-auto">
        <button class="btn btn-danger" @click="killClustering">
          Stop
        </button>
      </div>

      <div v-if="!lens || lensStatus === 'failed'" class="col-auto">
        <button class="btn btn-secondary" @click="runLens()">
          Run
          <template v-if="lensStatus === 'failed'">again</template>
        </button>
      </div>

      <div
          v-if="lensStatus === 'done' && lens.distinct_links_count > 0 && (!clustering || clusteringStatus === 'failed')"
          class="col-auto">
        <button type="button" class="btn btn-secondary my-1" @click="runClustering($event)">
          Cluster
          <template v-if="clusteringStatus === 'failed'">again</template>
        </button>
      </div>

      <div v-if="!isOpen" class="col-auto">
        <button-delete @click="$emit('remove')" title="Delete this lens" :disabled="!allowDelete"/>
      </div>
    </template>

    <template v-slot:columns>
      <div v-if="lens" class="col">
        <status :lens-spec="lensSpec"/>
      </div>
    </template>

    <sub-card label="Description">
      <textarea class="form-control mt-3" :id="'description_' + lensSpec.id" v-model="lensSpec.description">
      </textarea>

      <small class="form-text text-muted mt-2">
        Provide a description for this lens
      </small>
    </sub-card>

    <fieldset :disabled="!!lens">
      <sub-card label="Operations" :has-columns="true" :hasError="errors.includes('elements')">
        <template v-slot:columns>
          <div class="col-auto">
            <div class="custom-control custom-switch">
              <input type="checkbox" class="custom-control-input" autocomplete="off"
                     :id="'fuzzy_lens_' + lensSpec.id" v-model="useFuzzyLogic"/>
              <label class="custom-control-label" :for="'fuzzy_lens_' + lensSpec.id">Use fuzzy logic</label>
            </div>
          </div>
        </template>

        <logic-box :element="lensSpec.specs" elements-name="elements" :is-root="true"
                   :should-have-elements="true" :controlled-elements="true" group="lens-elements"
                   :uid="'lens_' + lensSpec.id  + '_group_0'" validate-method-name="validateLensElement"
                   empty-elements-text="No lens elements"
                   validation-failed-text="Please provide at least one lens element"
                   :options="lensOptions" :option-groups="lensOptionGroups"
                   :option-descriptions="lensOptionDescriptions" :group-include="groupInclude"
                   @add="addLensElement($event)" @remove="removeLensElement($event)"
                   ref="lensGroupComponent">
          <template v-slot:box-slot="boxElement">
            <div v-if="useFuzzyLogic && !isOnlyLeft(boxElement.element.type)" class="col-auto">
              <select :id="'t_conorm_' + boxElement.index" class="form-control form-control-sm"
                      v-model="boxElement.element.t_conorm">
                <option v-for="(description, key) in tConorms" :value="key">
                  {{ description }}
                </option>
              </select>
            </div>

            <div v-if="useFuzzyLogic && !isOnlyLeft(boxElement.element.type)" class="col-auto">
              <range :id="'threshold_' + boxElement.index" v-model.number="boxElement.element.threshold"
                     label="Threshold" :allow-zero="false"/>
            </div>
          </template>

          <template v-slot="curElement">
            <lens-element :type="curElement.type" :element="curElement.element" :index="curElement.index"
                          :disabled="!!lens" @add="curElement.add()" @remove="curElement.remove()"
                          @update="updateView()"/>
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
    import LogicBox from "../../helpers/LogicBox";

    import Status from "./Status";
    import LensElement from "./LensElement";

    export default {
        name: "Lens",
        mixins: [ValidationMixin],
        components: {
            LogicBox,
            Status,
            LensElement
        },
        props: {
            lensSpec: Object,
            allowDelete: Boolean,
        },
        data() {
            return {
                isOpen: false,
                useFuzzyLogic: false,
                lensOptions: props.lensOptions,
                lensOptionGroups: props.lensOptionGroups,
                lensOptionDescriptions: props.lensOptionDescriptions,
                tConorms: props.tConorms,
            };
        },
        computed: {
            view() {
                return this.$root.getViewByIdAndType(this.lensSpec.id, 'lens');
            },

            lens() {
                return this.$root.lenses.find(lens => lens.spec_id === this.lensSpec.id);
            },

            clustering() {
                return this.$root.clusterings.find(clustering =>
                    clustering.spec_type === 'lens' && clustering.spec_id === this.lensSpec.id);
            },

            lensStatus() {
                return this.lens ? this.lens.status : null;
            },

            clusteringStatus() {
                return this.clustering ? this.clustering.status : null;
            },

            groupInclude() {
                return {t_conorm: this.useFuzzyLogic ? 'MAXIMUM_T_CONORM' : '', threshold: 0};
            },

            lensesInLens() {
                const lensesInSpec = lensSpec => this.$root
                    .getRecursiveElements(lensSpec.specs, 'elements')
                    .filter(elem => elem.type === 'lens')
                    .flatMap(elem => {
                        const elemLensSpec = this.$root.getLensSpecById(elem.id);
                        if (elemLensSpec)
                            return [elemLensSpec, ...lensesInSpec(elemLensSpec)];
                        return [];
                    });

                const lenses = lensesInSpec(this.lensSpec);
                return [...new Set(lenses)];
            },

            linksetsInLens() {
                const linksets = [this.lensSpec, ...this.lensesInLens].flatMap(lensSpec => {
                    return this.$root
                        .getRecursiveElements(lensSpec.specs, 'elements')
                        .filter(elem => elem.type === 'linkset')
                        .map(elem => this.$root.getLinksetSpecById(elem.id))
                        .filter(spec => spec !== undefined);
                });
                return [...new Set(linksets)];
            },
        },
        methods: {
            validateLens() {
                return this.$refs.lensGroupComponent.validateLogicBox();
            },

            isOnlyLeft(type) {
                return type === 'DIFFERENCE' || type.startsWith('IN_SET');
            },

            onToggle(isOpen) {
                this.isOpen = isOpen;
                isOpen ? this.$emit('show') : this.$emit('hide');
            },

            addLensElement(group) {
                if (group.elements.length < 2) {
                    group.elements.push({id: null, type: 'linkset'});
                    this.addLensElement(group);
                }
            },

            removeLensElement({group, index}) {
                const element = group.elements[index].elements[0];
                const elementCopy = JSON.parse(JSON.stringify(element));

                this.$set(group.elements, index, elementCopy);
            },

            updateView() {
                const entityTypeSelections = new Set(this.linksetsInLens.flatMap(
                    linksetSpec => [...linksetSpec.sources, ...linksetSpec.targets]
                ));

                if (this.view) {
                    const propertiesToRemove = JSON.parse(JSON.stringify(this.view.properties));
                    entityTypeSelections.forEach(etsId => {
                        const ets = this.$root.getEntityTypeSelectionById(etsId);
                        const propsIdx = propertiesToRemove.findIndex(prop =>
                            prop.timbuctoo_graphql === ets.dataset.timbuctoo_graphql &&
                            prop.dataset_id === ets.dataset.dataset_id &&
                            prop.collection_id === ets.dataset.collection_id
                        );

                        if (propsIdx > -1)
                            propertiesToRemove.splice(propsIdx, 1);
                    });

                    propertiesToRemove.forEach(toRemove => {
                        const propsIdx = this.view.properties.findIndex(prop =>
                            prop.timbuctoo_graphql === toRemove.timbuctoo_graphql &&
                            prop.dataset_id === toRemove.dataset_id &&
                            prop.collection_id === toRemove.collection_id
                        );

                        if (propsIdx > -1)
                            this.view.properties.splice(propsIdx, 1);
                    });
                }

                if (!this.view)
                    this.$root.addView(this.lensSpec.id, 'lens');

                entityTypeSelections.forEach(etsId => {
                    const ets = this.$root.getEntityTypeSelectionById(etsId);
                    const propsIdx = this.view.properties.findIndex(prop =>
                        prop.timbuctoo_graphql === ets.dataset.timbuctoo_graphql &&
                        prop.dataset_id === ets.dataset.dataset_id &&
                        prop.collection_id === ets.dataset.collection_id
                    );

                    if (propsIdx < 0)
                        this.view.properties.push({
                            timbuctoo_graphql: ets.dataset.timbuctoo_graphql,
                            dataset_id: ets.dataset.dataset_id,
                            collection_id: ets.dataset.collection_id,
                            properties: [['']]
                        });
                });
            },

            updateLogicBoxTypes(elements) {
                if (elements.hasOwnProperty('type')) {
                    if (this.useFuzzyLogic) {
                        this.$set(elements, 't_conorm', 'MAXIMUM_T_CONORM');
                        this.$set(elements, 'threshold', 0);
                    }
                    else {
                        this.$set(elements, 't_conorm', '');
                        this.$delete(elements, 'threshold');
                    }
                }

                if (elements.hasOwnProperty('elements'))
                    elements.elements.forEach(element => this.updateLogicBoxTypes(element));
            },

            async runLens(force = false) {
                if (this.validateLens()) {
                    const data = await this.$root.runLens(this.lensSpec.id, force);
                    if (data.result === 'exists' && confirm('This lens already exists.\nDo you want to overwrite it with the current configuration?'))
                        await this.runLens(true);

                    EventBus.$emit('refresh');
                }
            },

            async runClustering() {
                await this.$root.runClustering('lens', this.lensSpec.id);
                EventBus.$emit('refresh');
            },

            async killLens() {
                await this.$root.killLens(this.lensSpec.id);
                EventBus.$emit('refresh');
            },

            async killClustering() {
                await this.$root.killClustering('lens', this.lensSpec.id);
                EventBus.$emit('refresh');
            },
        },
        mounted() {
            this.useFuzzyLogic = !!this.lensSpec.specs.tConorm;
        },
        watch: {
            useFuzzyLogic() {
                this.updateLogicBoxTypes(this.lensSpec.specs);
            },
        },
    };
</script>
