<template>
  <div v-if="methodGroup.conditions" class="border p-2" v-bind:class="styleClass">
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
          Override {{ isConjunction ? 't-norm' : 't-conorm' }}:

          <select class="font-italic smaller border rounded bg-opacity pl-1 ml-1"
                  v-bind:class="borderStyleClass">
            <option value="" selected>Do not override</option>
            <template v-if="isConjunction">
              <option v-for="(label, value) in tNorms" :value="value">{{ label }}</option>
            </template>
            <template v-else>
              <option v-for="(label, value) in tConorms" :value="value">{{ label }}</option>
            </template>
          </select>
        </label>
      </div>
    </div>

    <b-collapse v-model="visible" class="mt-1">
      <p v-if="isLinksetRoot" class="font-weight-bold mb-1">Matching</p>

      <template v-for="(condition, idx) in methodGroup.conditions">
        <linkset-spec-group-info :method-group="condition" :key="idx"
                                 :is-root="false" :is-linkset-root="false" :override-fuzzy-logic="overrideFuzzyLogic"/>

        <p v-if="idx < (methodGroup.conditions.length - 1) && usingFuzzyLogic" class="font-weight-bold my-2">
          <span class="text-secondary">
            {{ isConjunction ? 'AND' : 'OR' }}
          </span>
          using
          <span class="text-secondary">
            {{ {...tNorms, ...tConorms}[methodGroup.type] }}
          </span>
        </p>

        <p v-else-if="idx < (methodGroup.conditions.length - 1)" class="font-weight-bold my-2 text-secondary">
          {{ methodGroup.type }}
        </p>
      </template>
    </b-collapse>
  </div>

  <linkset-spec-condition-info v-else :condition="methodGroup" v-bind:class="styleClass"
                               :override-fuzzy-logic="overrideFuzzyLogic"/>
</template>

<script>
    import props from "@/utils/props";
    import LinksetSpecConditionInfo from './LinksetSpecConditionInfo';

    export default {
        name: "LinksetSpecGroupInfo",
        components: {
            LinksetSpecConditionInfo
        },
        props: {
            methodGroup: Object,
            isRoot: {
                type: Boolean,
                default: true,
            },
            addRootMargin: {
                type: Boolean,
                default: true,
            },
            isLinksetRoot: {
                type: Boolean,
                default: true,
            },
            overrideFuzzyLogic: {
                type: Boolean,
                default: false,
            },
        },
        data() {
            return {
                tNorms: props.tNorms,
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

            usingFuzzyLogic() {
                return !['AND', 'OR'].includes(this.methodGroup.type);
            },

            isConjunction() {
                return this.methodGroup.type === 'AND' || Object.keys(this.tNorms).includes(this.methodGroup.type);
            },
        },
    }
</script>