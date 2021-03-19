<template>
  <div class="border p-3 mb-4 bg-white">
    <div class="row align-items-baseline flex-nowrap">
      <div class="col-auto">
        <span class="font-weight-bold font-italic"># {{ index + 1 }}</span>
      </div>

      <div class="col text-break-all">
        <span class="font-weight-bold">URI: </span>

        <span class="text-secondary">
          {{ sample.uri }}
        </span>

        <button type="button" class="btn btn-sm ml-2" @click="copyUri">
          <fa-icon icon="copy"/>
        </button>
      </div>
    </div>

    <div class="row flex-nowrap border-top mt-2 pt-2">
      <div class="col">
        <property-values v-for="(prop, idx) in sample.properties"
                         :key="idx" v-if="prop.values.length > 0"
                         :graphql-endpoint="prop.graphql_endpoint" :dataset-id="prop.dataset_id"
                         :collection-id="prop.collection_id" :property="prop.property" :values="prop.values"/>
      </div>
    </div>
  </div>
</template>

<script>
    import PropertyValues from "../../helpers/PropertyValues";

    export default {
        name: "Sample",
        components: {
            PropertyValues
        },
        props: {
            index: Number,
            sample: Object,
        },
        methods: {
            async copyUri() {
                await navigator.clipboard.writeText(this.sample.uri);
            },
        }
    };
</script>
