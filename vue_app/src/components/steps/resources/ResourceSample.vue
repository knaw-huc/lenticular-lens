<template>
  <div class="border p-3 mb-4 bg-primary-very-light">
    <div class="row align-items-baseline flex-nowrap">
      <div class="col-auto">
        <span class="font-weight-bold font-italic"># {{ index + 1 }}</span>
      </div>

      <div class="col text-break-all">
        <span class="font-weight-bold">URI: </span>

        <span class="text-info">
          {{ sample.uri }}
        </span>

        <button type="button" class="btn btn-sm ml-2" @click="copyUri">
          <fa-icon icon="copy"/>
        </button>
      </div>
    </div>

    <div class="row flex-nowrap border-top mt-2 pt-2">
      <div class="col">
        <properties :properties="properties"/>
      </div>
    </div>
  </div>
</template>

<script>
    import Properties from "../../helpers/Properties";

    export default {
        name: "ResourceSample",
        components: {
            Properties
        },
        props: {
            index: Number,
            sample: Object,
        },
        computed: {
            properties() {
                return Object.keys(this.sample)
                    .filter(property => property !== 'uri')
                    .map(property => ({
                        property: property,
                        values: Array.isArray(this.sample[property]) ? this.sample[property] : [this.sample[property]]
                    }));
            },
        },
        methods: {
            async copyUri() {
                await navigator.clipboard.writeText(this.sample.uri);
            },
        }
    };
</script>
