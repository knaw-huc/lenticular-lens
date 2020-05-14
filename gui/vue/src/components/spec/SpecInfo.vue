<template>
  <sub-card v-if="type === 'linkset'" class="spec-info" label="Linkset specifications">
    <linkset-spec-group-info :method-group="spec.methods"/>
  </sub-card>

  <sub-card v-else class="spec-info" label="Lens specifications">
    <lens-spec-group-info :elements-group="spec.specs"/>
  </sub-card>
</template>

<script>
    import LinksetSpecGroupInfo from "./LinksetSpecGroupInfo";
    import LensSpecGroupInfo from "./LensSpecGroupInfo";

    export default {
        name: "SpecInfo",
        components: {
            LinksetSpecGroupInfo,
            LensSpecGroupInfo
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