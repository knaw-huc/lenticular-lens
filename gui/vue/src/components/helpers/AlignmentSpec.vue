<template>
  <sub-card class="match-info" label="Alignment specifications">
    <alignment-spec-group-info :matching-method-group="match.methods" :is-root="true">
      <p class="font-weight-bold mb-1">Matching</p>
    </alignment-spec-group-info>
  </sub-card>
</template>

<script>
    import AlignmentSpecGroupInfo from "./AlignmentSpecGroupInfo";

    export default {
        name: "AlignmentSpec",
        components: {
            AlignmentSpecGroupInfo
        },
        props: {
            'match': Object,
        },
    };
</script>

<style>
  .match-info {
    font-size: 0.875rem;
  }
</style>