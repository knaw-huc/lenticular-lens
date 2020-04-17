<template>
  <sub-card v-if="type === 'linkset'" class="spec-info" label="Linkset specifications">
    <linkset-spec-group-info :method-group="spec.methods" :is-root="true">
      <p class="font-weight-bold mb-1">Matching</p>
    </linkset-spec-group-info>
  </sub-card>

  <sub-card v-else class="spec-info" label="Lens specifications">

  </sub-card>
</template>

<script>
    import LinksetSpecGroupInfo from "./LinksetSpecGroupInfo";

    export default {
        name: "SpecInfo",
        components: {
            LinksetSpecGroupInfo
        },
        props: {
            type: String,
            spec: Object
        },
    };
</script>

<style>
  .spec-info {
    font-size: 0.875rem;
  }
</style>