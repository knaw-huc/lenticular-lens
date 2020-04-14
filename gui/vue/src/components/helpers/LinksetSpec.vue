<template>
  <sub-card class="linkset-spec-info" label="Linkset specifications">
    <linkset-spec-group-info :method-group="linksetSpec.methods" :is-root="true">
      <p class="font-weight-bold mb-1">Matching</p>
    </linkset-spec-group-info>
  </sub-card>
</template>

<script>
    import LinksetSpecGroupInfo from "./LinksetSpecGroupInfo";

    export default {
        name: "LinksetSpec",
        components: {
            LinksetSpecGroupInfo
        },
        props: {
            linksetSpec: Object,
        },
    };
</script>

<style>
  .linkset-spec-info {
    font-size: 0.875rem;
  }
</style>