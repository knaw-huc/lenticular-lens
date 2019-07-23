<template>
  <div v-if="matching_method_group.conditions" v-bind:class="!is_root ? 'border shadow p-1' : {}">
    <template v-for="(condition, idx) in matching_method_group.conditions">
      <matching-method-group-info :matching_method_group="condition" :key="idx"/>

      <p class="font-weight-bold my-2 text-info" v-if="idx < (matching_method_group.conditions.length - 1)">
        {{ matching_method_group.type }}
      </p>
    </template>
  </div>

  <match-condition-info v-else-if="!matching_method_group.conditions" :condition="matching_method_group"/>
</template>

<script>
    import MatchConditionInfo from './MatchConditionInfo';

    export default {
        name: "MatchingMethodGroupInfo",
        components: {
            MatchConditionInfo
        },
        props: {
            is_root: {
                type: Boolean,
                default: false,
            },
            matching_method_group: {},
        },
    }
</script>