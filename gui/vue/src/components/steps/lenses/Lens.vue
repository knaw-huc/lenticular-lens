<template>
  <card :id="'lens_spec_' + lensSpec.id" type="lens-specs" :res-id="lensSpec.id" v-model="lensSpec.label"
        :has-error="errors.length > 0" :has-handle="true" :has-extra-row="!!lens"
        @show="onToggle(true)" @hide="onToggle(false)">
    <template v-slot:title-columns>
      <div v-if="!isOpen" class="col-auto">
        <b-button variant="info" @click="$emit('duplicate', lensSpec)">Duplicate</b-button>
      </div>

      <div v-if="lensStatus === 'downloading' || lensStatus === 'running'" class="col-auto">
        <b-button variant="danger" @click="killLens">
          Stop
        </b-button>
      </div>

      <div v-if="clusteringStatus === 'running'" class="col-auto">
        <b-button variant="danger" @click="killClustering">
          Stop
        </b-button>
      </div>

      <div v-if="!lens || lensStatus === 'failed'" class="col-auto">
        <b-button variant="info" @click="runLens()">
          Run
          <template v-if="lensStatus === 'failed'">again</template>
        </b-button>
      </div>

      <div v-if="lensStatus === 'done' && lens.links_count > 0" class="col-auto">
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

      <div v-if="lensStatus === 'done' && lens.links_count > 0 && $root.associationFiles"
           class="col-auto">
        <select class="col-auto form-control association-select my-1" v-model="association"
                :id="'lens_' + lensSpec.id + '_association'">
          <option value="">No association</option>
          <option v-for="associationFileName in $root.associationFiles" :value="associationFileName">
            {{ associationFileName }}
          </option>
        </select>
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
      <sub-card :hasError="errors.includes('elements')">
        <logic-box :element="lensSpec.specs" elements-name="elements" :is-root="true"
                   :should-have-elements="true" :controlled-elements="true" group="lens-elements"
                   :uid="'lens_' + lensSpec.id  + '_group_0'" validate-method-name="validateLensElement"
                   empty-elements-text="No lens elements"
                   validation-failed-text="Please provide at least one lens element"
                   :options="lensOptions" :option-groups="lensOptionGroups"
                   :option-descriptions="lensOptionDescriptions" v-slot="curElement"
                   @add="addLensElement($event)" @remove="removeLensElement($event)"
                   ref="lensGroupComponent">
          <lens-element :type="curElement.type" :element="curElement.element" :index="curElement.index"
                        :disabled="!!lens" @add="curElement.add()" @remove="curElement.remove()"
                        @update="updateProperties()"/>
        </logic-box>
      </sub-card>
    </fieldset>
  </card>
</template>

<script>
    import LogicBox from "../../helpers/LogicBox";
    import ValidationMixin from '../../../mixins/ValidationMixin';

    import Status from "./Status";
    import LensElement from "./LensElement";
    import {EventBus} from "../../../eventbus";
    import props from "../../../utils/props";

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
                association: '',
                isOpen: false,
                lensOptions: props.lensOptions,
                lensOptionGroups: props.lensOptionGroups,
                lensOptionDescriptions: props.lensOptionDescriptions,
            };
        },
        computed: {
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

            entityTypeSelectionsInLensElements() {
                const entityTypeSelections = this.linksetsInLens
                    .flatMap(linksetSpec => linksetSpec.properties)
                    .flatMap(prop => prop.entity_type_selection);
                return [...new Set(entityTypeSelections)];
            },

            entityTypeSelectionsInLensProperties() {
                const entityTypeSelections = this.lensSpec.properties.flatMap(prop => prop.entity_type_selection);
                return [...new Set(entityTypeSelections)];
            },
        },
        methods: {
            validateLens() {
                return this.$refs.lensGroupComponent.validateLogicBox();
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

            updateProperties() {
                const entityTypeSelectionsToRemove = this.entityTypeSelectionsInLensProperties
                    .filter(res => !this.entityTypeSelectionsInLensElements.includes(res));

                if (entityTypeSelectionsToRemove.length > 0) {
                    const propIdxToRemove = this.properties.reduce((indexes, prop, idx) => {
                        if (entityTypeSelectionsToRemove.includes(prop.entity_type_selection))
                            indexes.push(idx);
                        return indexes;
                    }, []);
                    propIdxToRemove.reverse().forEach(idx => this.lensSpec.properties.splice(idx, 1));
                }

                const entityTypeSelectionsToAdd = this.entityTypeSelectionsInLensElements
                    .filter(res => !this.entityTypeSelectionsInLensProperties.includes(res));

                if (entityTypeSelectionsToAdd.length > 0) {
                    this.linksetsInLens
                        .flatMap(linksetSpec => linksetSpec.properties)
                        .forEach(prop => {
                            if (entityTypeSelectionsToAdd.includes(prop.entity_type_selection))
                                this.lensSpec.properties.push(prop);
                        });
                }
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
                const associationFile = this.association !== '' ? this.association : null;
                await this.$root.runClustering('lens', this.lensSpec.id, associationFile);
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
    };
</script>
