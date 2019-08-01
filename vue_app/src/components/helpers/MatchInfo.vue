<template>
  <sub-card class="match-info">
    <p class="font-weight-bold mb-2">Matching</p>
    <matching-method-group-info :matching_method_group="match" :is_root="true"/>
  </sub-card>
</template>

<script>
    import SubCard from "../structural/SubCard";
    import MatchingMethodGroupInfo from "./MatchingMethodGroupInfo";

    export default {
        name: "MatchInfo",
        components: {
            SubCard,
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