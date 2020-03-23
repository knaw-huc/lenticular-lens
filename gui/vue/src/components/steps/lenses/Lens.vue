<template>
  <card :id="'lens_' + lens.id" type="lenses" v-model="lens.label"
        :has-error="errors.length > 0" :has-handle="true"
        @show="onToggle(true)" @hide="onToggle(false)">
    <template v-slot:title-columns>
      <div v-if="!isOpen" class="col-auto">
        <b-button variant="info" @click="$emit('duplicate', lens)">Duplicate</b-button>
      </div>

      <div v-if="!isOpen" class="col-auto">
        <button-delete @click="$emit('remove')" title="Delete this Lens"/>
      </div>
    </template>

    <sub-card label="Description">
      <textarea class="form-control mt-3" :id="'description_' + lens.id" v-model="lens.description">
      </textarea>

      <small class="form-text text-muted mt-2">
        Provide a description for this lens
      </small>
    </sub-card>

    <sub-card :hasError="errors.includes('elements')">
      <elements-group :elements-group="lens.elements" elements-group-name="alignments" :is-root="true"
                      :should-have-elements="true" :controlled-elements="true" group="lens-elements"
                      :uid="'lens_' + lens.id  + '_group_0'" validate-method-name="validateLensElement"
                      empty-elements-text="No alignments"
                      validation-failed-text="Please provide at least one alignment configuration"
                      :options="lensOptions" v-slot="curElement"
                      @add="addLensElement($event)" @remove="removeLensElement($event)" ref="lensGroupComponent">
        <lens-element :element="curElement.element" :index="curElement.index"
                      @add="curElement.add()" @remove="curElement.remove()" @alignment="updateProperties()"/>
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
            lens: Object,
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

            alignmentsInLens() {
                return this.$root
                    .getRecursiveElements(this.lens.elements, 'alignments')
                    .map(elem => this.$root.getMatchById(elem.alignment));
            },

            resourcesInLensAlignments() {
                const resources = this.alignmentsInLens
                    .flatMap(alignment => alignment.properties)
                    .flatMap(prop => prop.resource);
                return [...new Set(resources)];
            },

            resourcesInLensProperties() {
                const resources = this.lens.properties.flatMap(prop => prop.resource);
                return [...new Set(resources)];
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
                if (group.alignments.length < 2) {
                    group.alignments.push({alignment: null});
                    this.addLensElement(group);
                }
            },

            removeLensElement({group, index}) {
                const element = group.alignments[index].alignments[0];
                const elementCopy = JSON.parse(JSON.stringify(element));

                this.$set(group.alignments, index, elementCopy);
            },

            updateProperties() {
                const resourcesToRemove = this.resourcesInLensProperties
                    .filter(res => !this.resourcesInLensAlignments.includes(res));

                if (resourcesToRemove.length > 0) {
                    const propIdxToRemove = this.properties.reduce((indexes, prop, idx) => {
                        if (resourcesToRemove.includes(prop.resource))
                            indexes.push(idx);
                        return indexes;
                    }, []);
                    propIdxToRemove.reverse().forEach(idx => this.lens.properties.splice(idx, 1));
                }

                const resourcesToAdd = this.resourcesInLensAlignments
                    .filter(res => !this.resourcesInLensProperties.includes(res));

                if (resourcesToAdd.length > 0) {
                    this.alignmentsInLens
                        .flatMap(alignment => alignment.properties)
                        .forEach(prop => {
                            if (resourcesToAdd.includes(prop.resource))
                                this.lens.properties.push(prop);
                        });
                }
            },
        },
    };
</script>
