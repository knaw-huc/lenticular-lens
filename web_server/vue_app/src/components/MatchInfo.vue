<template>
  <div class="match-info bg-white border shadow px-4 py-2 mt-3">
    <p class="font-weight-bold m-0">Matching</p>

    <matching-method-group-info :matching_method_group="match" :is_root="true"/>
  </div>
</template>

<script>
    import MatchingMethodGroupInfo from "./MatchingMethodGroupInfo";

    export default {
        name: "MatchInfo",
        components: {
            MatchingMethodGroupInfo
        },
        props: {
            'match': Object,
        }
    }
</script>

<style>
  .match-info {
    font-size: 0.875rem;
  }
</style>