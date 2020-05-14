<template>
  <div class="border p-2" v-bind:class="styleClass">
    <lens-spec-group-info v-if="!specLeft" :elements-group="elementsGroupLeft" :is-root="false"/>

    <lens-spec-group-info v-else-if="elementsGroupLeft.type === 'lens'" :elements-group="specLeft.specs"
                          :is-root="false"/>

    <linkset-spec-group-info v-else :method-group="specLeft.methods"
                             :is-root="false" :is-linkset-root="true"/>

    <p class="font-weight-bold my-2">
      using a lens type of
      <span class="text-info">{{ elementsGroup.type }}</span>
      against
    </p>

    <lens-spec-group-info v-if="!specRight" :elements-group="elementsGroupRight" :is-root="false"/>

    <lens-spec-group-info v-else-if="elementsGroupRight.type === 'lens'" :elements-group="specRight.specs"
                          :is-root="false"/>

    <linkset-spec-group-info v-else :method-group="specRight.methods"
                             :is-root="false" :is-linkset-root="true"/>
  </div>
</template>

<script>
    import LinksetSpecGroupInfo from './LinksetSpecGroupInfo';

    export default {
        name: "LensSpecGroupInfo",
        components: {
            LinksetSpecGroupInfo
        },
        props: {
            isRoot: {
                type: Boolean,
                default: true,
            },
            elementsGroup: Object,
        },
        computed: {
            styleClass() {
                const styleClass = [];

                if (this.isRoot)
                    styleClass.push('mt-3');

                if (this.isRoot || this.$parent.styleClass.includes('bg-primary-light'))
                    styleClass.push('bg-info-light', 'border-info');
                else
                    styleClass.push('bg-primary-light', 'border-primary');

                return styleClass;
            },

            elementsGroupLeft() {
                return this.getElementsGroup(0);
            },

            elementsGroupRight() {
                return this.getElementsGroup(1);
            },

            specLeft() {
                return this.getSpec(0);
            },

            specRight() {
                return this.getSpec(1);
            },
        },
        methods: {
            getElementsGroup(index) {
                return this.elementsGroup.elements[index];
            },

            getSpec(index) {
                const elementsGroup = this.getElementsGroup(index);
                if (elementsGroup.hasOwnProperty('id') && elementsGroup.hasOwnProperty('type')) {
                    if (elementsGroup.type === 'linkset')
                        return this.$root.getLinksetSpecById(elementsGroup.id);

                    return this.$root.getLensSpecById(elementsGroup.id);
                }

                return null;
            },
        },
    }
</script>