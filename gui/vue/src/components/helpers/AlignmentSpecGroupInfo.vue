<template>
  <div v-if="matchingMethodGroup.conditions" class="border p-2" v-bind:class="styleClass">
    <slot></slot>

    <template v-for="(condition, idx) in matchingMethodGroup.conditions">
      <alignment-spec-group-info :matching-method-group="condition" :key="idx"/>

      <p class="font-weight-bold my-2 text-info" v-if="idx < (matchingMethodGroup.conditions.length - 1)">
        {{ matchingMethodGroup.type }}
      </p>
    </template>
  </div>

  <alignment-spec-condition-info v-else :condition="matchingMethodGroup" v-bind:class="styleClass"/>
</template>

<script>
    import AlignmentSpecConditionInfo from './AlignmentSpecConditionInfo';

    export default {
        name: "AlignmentSpecGroupInfo",
        components: {
            AlignmentSpecConditionInfo
        },
        props: {
            isRoot: {
                type: Boolean,
                default: false,
            },
            matchingMethodGroup: Object,
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
        },
    }
</script>