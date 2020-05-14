<template>
  <div v-if="methodGroup.conditions" class="border p-2" v-bind:class="styleClass">
    <p v-if="isLinksetRoot" class="font-weight-bold mb-1">Matching</p>

    <template v-for="(condition, idx) in methodGroup.conditions">
      <linkset-spec-group-info :method-group="condition" :key="idx" :is-root="false" :is-linkset-root="false"/>

      <p class="font-weight-bold my-2 text-info" v-if="idx < (methodGroup.conditions.length - 1)">
        {{ methodGroup.type }}
      </p>
    </template>
  </div>

  <linkset-spec-condition-info v-else :condition="methodGroup" v-bind:class="styleClass"/>
</template>

<script>
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
            isLinksetRoot: {
                type: Boolean,
                default: true,
            },
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