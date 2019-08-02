<template>
  <sub-card :small-spacing="true" :is-first="isFirst">
    <div class="row align-items-center">
      <div class="col-auto">
        <div class="text-center bg-info-light text-info border border-info rounded p-2">
          <span class="font-weight-bold">Strength</span>
          <br/>
          <span class="font-italic">{{ strength }}</span>
        </div>
      </div>

      <div class="col">
        <div class="row">
          <div class="col">
            <span class="font-weight-bold pr-1">Source:</span>
            <span class="font-italic">{{ source }}</span>
          </div>

          <div class="col">
            <span class="font-weight-bold pr-1">Target:</span>
            <span class="font-italic">{{ target }}</span>
          </div>
        </div>

        <div class="row">
          <div class="col">
            <property
                v-for="(prop, idx) in sourceProperties"
                :key="idx"
                :property="prop.property"
                :values="prop.values"
                :read-only="true"/>
          </div>

          <div class="col">
            <property
                v-for="(prop, idx) in targetProperties"
                :key="idx"
                :property="prop.property"
                :values="prop.values"
                :read-only="true"/>
          </div>
        </div>
      </div>
    </div>
  </sub-card>
</template>

<script>
    import SubCard from '../../structural/SubCard';

    export default {
        name: "MatchLink",
        components: {
            SubCard
        },
        props: {
            source: String,
            sourceValues: Array,
            target: String,
            targetValues: Array,
            strength: String,
            isFirst: Boolean
        },
        computed: {
            sourceProperties() {
                return this.sourceValues.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    }
                });
            },

            targetProperties() {
                return this.sourceValues.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    }
                });
            },
        },
    }
</script>
