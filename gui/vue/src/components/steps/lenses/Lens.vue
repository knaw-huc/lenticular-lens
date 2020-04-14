<template>
  <card :id="'lens_spec_' + lensSpec.id" type="lens-specs" v-model="lensSpec.label"
        :has-error="errors.length > 0" :has-handle="true"
        @show="onToggle(true)" @hide="onToggle(false)">
    <template v-slot:title-columns>
      <div v-if="!isOpen" class="col-auto">
        <b-button variant="info" @click="$emit('duplicate', lensSpec)">Duplicate</b-button>
      </div>

      <div v-if="!isOpen" class="col-auto">
        <button-delete @click="$emit('remove')" title="Delete this Lens"/>
      </div>
    </template>

    <sub-card label="Description">
      <textarea class="form-control mt-3" :id="'description_' + lensSpec.id" v-model="lensSpec.description">
      </textarea>

      <small class="form-text text-muted mt-2">
        Provide a description for this lens
      </small>
    </sub-card>

    <sub-card :hasError="errors.includes('elements')">
      <elements-group :elements-group="lensSpec.specs" elements-group-name="elements" :is-root="true"
                      :should-have-elements="true" :controlled-elements="true" group="lens-elements"
                      :uid="'lens_' + lensSpec.id  + '_group_0'" validate-method-name="validateLensElement"
                      empty-elements-text="No linksets"
                      validation-failed-text="Please provide at least one linkset"
                      :options="lensOptions" v-slot="curElement"
                      @add="addLensElement($event)" @remove="removeLensElement($event)"
                      ref="lensGroupComponent">
        <lens-element :element="curElement.element" :index="curElement.index"
                      @add="curElement.add()" @remove="curElement.remove()" @linkset="updateProperties()"/>
      </elements-group>
    </sub-card>
  </card>
</template>

<script>
    import ElementsGroup from "../../helpers/ElementsGroup";
    import ValidationMixin from '../../../mixins/ValidationMixin';
    import LensElement from "./LensElement";

    export default {
        name: "Lens",
        mixins: [ValidationMixin],
        components: {
            ElementsGroup,
            LensElement
        },
        props: {
            lensSpec: Object,
        },
        data() {
            return {
                isOpen: false,
            };
        },
        computed: {
            lensOptions() {
                return {
                    UNION: "Union (A ∪ B) All links of both linksets",
                    INTERSECTION: "Intersection (A ∩ B) Only links that appear in both linksets",
                    DIFFERENCE: "Difference (A - B) Only links from the first linkset, not from the second linkset",
                    SYM_DIFFERENCE: "Symmetric difference (A ∆ B) Only links which appear in either one linkset, but not both"
                };
            },

            linksetsInLens() {
                return this.$root
                    .getRecursiveElements(this.lensSpec.elements, 'elements')
                    .map(elem => this.$root.getLinksetSpecById(elem.id));
            },

            entityTypeSelectionsInLensElements() {
                const entityTypeSelections = this.linksetsInLens
                    .flatMap(linksetSpec => linksetSpec.properties)
                    .flatMap(prop => prop.entityTypeSelection);
                return [...new Set(entityTypeSelections)];
            },

            entityTypeSelectionsInLensProperties() {
                const entityTypeSelections = this.lensSpec.properties.flatMap(prop => prop.entityTypeSelection);
                return [...new Set(entityTypeSelections)];
            },
        },
        methods: {
            validateLens() {
                return this.$refs.lensGroupComponent.validateElementsGroup();
            },

            onToggle(isOpen) {
                this.isOpen = isOpen;
                isOpen ? this.$emit('show') : this.$emit('hide');
            },

            addLensElement(group) {
                if (group.specs.length < 2) {
                    group.specs.push({id: null, type: 'linkset'});
                    this.addLensElement(group);
                }
            },

            removeLensElement({group, index}) {
                const element = group.specs[index].specs[0];
                const elementCopy = JSON.parse(JSON.stringify(element));

                this.$set(group.specs, index, elementCopy);
            },

            updateProperties() {
                const entityTypeSelectionsToRemove = this.entityTypeSelectionsInLensProperties
                    .filter(res => !this.entityTypeSelectionsInLensElements.includes(res));

                if (entityTypeSelectionsToRemove.length > 0) {
                    const propIdxToRemove = this.properties.reduce((indexes, prop, idx) => {
                        if (entityTypeSelectionsToRemove.includes(prop.entityTypeSelection))
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
                            if (entityTypeSelectionsToAdd.includes(prop.entityTypeSelection))
                                this.lensSpec.properties.push(prop);
                        });
                }
            },
        },
    };
</script>
