<template>
  <div class="border p-2" v-bind:class="styleClass">
    <div class="row align-items-baseline justify-content-between">
      <div class="col-auto">
        <p class="font-italic smaller border rounded bg-opacity pointer m-0 px-2"
           v-bind:class="borderStyleClass" @click="visible = !visible">
          <fa-icon icon="chevron-down" size="xs" :class="visible ? null : 'collapsed'"></fa-icon>
          Open / close
        </p>
      </div>

      <div v-if="overrideFuzzyLogic" class="col-auto">
        <label class="font-weight-bold smaller m-0">
          Override t-conorm:

          <select class="font-italic smaller border rounded bg-opacity pl-1 ml-1"
                  v-bind:class="borderStyleClass">
            <option value="" selected>Do not override</option>
            <option v-for="(label, value) in tConorms" :value="value">{{ label }}</option>
          </select>
        </label>
      </div>
    </div>

    <b-collapse v-model="visible" class="mt-1">
      <lens-spec-group-info v-if="!specLeft" :elements-group="elementsGroupLeft"
                            :is-root="false" :override-fuzzy-logic="overrideFuzzyLogic"/>

      <lens-spec-group-info v-else-if="elementsGroupLeft.type === 'lens'" :elements-group="specLeft.specs"
                            :is-root="false" :override-fuzzy-logic="overrideFuzzyLogic"/>

      <linkset-spec-group-info v-else :method-group="specLeft.methods"
                               :is-root="false" :is-linkset-root="true" :override-fuzzy-logic="overrideFuzzyLogic"/>

      <p class="font-weight-bold my-2">
        using a lens type of
        <span class="text-secondary">{{ elementsGroup.type }}</span>
        against
      </p>

      <lens-spec-group-info v-if="!specRight" :elements-group="elementsGroupRight"
                            :is-root="false" :override-fuzzy-logic="overrideFuzzyLogic"/>

      <lens-spec-group-info v-else-if="elementsGroupRight.type === 'lens'" :elements-group="specRight.specs"
                            :is-root="false" :override-fuzzy-logic="overrideFuzzyLogic"/>

      <linkset-spec-group-info v-else :method-group="specRight.methods"
                               :is-root="false" :is-linkset-root="true" :override-fuzzy-logic="overrideFuzzyLogic"/>
    </b-collapse>
  </div>
</template>

<script>
    import props from '@/utils/props';
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
            addRootMargin: {
                type: Boolean,
                default: true,
            },
            overrideFuzzyLogic: {
                type: Boolean,
                default: false,
            },
            elementsGroup: Object,
        },
        data() {
            return {
                tConorms: props.tConorms,
                visible: true,
            };
        },
        computed: {
            styleClass() {
                const styleClass = [];

                if (this.isRoot && this.addRootMargin)
                    styleClass.push('mt-3');

                if (this.isRoot || this.$parent.$parent.styleClass.includes('bg-primary-light'))
                    styleClass.push('bg-secondary-light', 'border-secondary');
                else
                    styleClass.push('bg-primary-light', 'border-primary');

                return styleClass;
            },

            borderStyleClass() {
                return this.styleClass.filter(className => className.startsWith('border'));
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