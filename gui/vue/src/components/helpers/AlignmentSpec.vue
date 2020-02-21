<template>
  <sub-card class="match-info" label="Alignment specifications">
    <alignment-spec-group-info :matching-method-group="match.methods" :is-root="true">
      <p class="font-weight-bold mb-1">
        Matching
        <template v-if="match.match_against">
          against alignment
          <span class="text-info">{{ matchAgainstLabel }}</span>
        </template>
      </p>
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
        computed: {
            matchAgainstLabel() {
                if (this.match.match_against)
                    return this.$root.getMatchById(this.match.match_against).label;

                return null;
            },
        },
    };
</script>

<style>
  .match-info {
    font-size: 0.875rem;
  }
</style>