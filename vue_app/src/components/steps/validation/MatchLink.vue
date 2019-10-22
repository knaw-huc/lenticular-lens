<template>
  <div class="border p-3 mb-4" v-bind:class="[bgColor]">
    <div class="row align-items-center flex-nowrap">
      <div class="col-auto d-flex flex-column align-items-center">
        <div class="col-auto">
          <span class="font-weight-bold font-italic"># {{ index + 1 }}</span>
        </div>

        <div class="col-auto">
          <div class="btn btn-sm bg-info-light border border-info text-info read-only m-1">
            <span class="font-weight-bold">Max strength</span><br>
            {{ Math.max(...link.strengths).toFixed(3) }}
          </div>
        </div>
      </div>

      <div class="col">
        <div class="text-break-all">
          <span class="font-weight-bold">Source URI:</span>

          <span class="text-info">
            {{ link.source }}
          </span>

          <button type="button" class="btn btn-sm ml-2" @click="copySourceUriToClipboard">
            <fa-icon :icon="['far', 'clipboard']"/>
          </button>
        </div>

        <div class="text-break-all">
          <span class="font-weight-bold">Target URI:</span>

          <span class="text-info">
            {{ link.target }}
          </span>

          <button type="button" class="btn btn-sm ml-2" @click="copyTargetUriToClipboard">
            <fa-icon :icon="['far', 'clipboard']"/>
          </button>
        </div>

        <div v-if="sourceProperties.length > 0 || targetProperties.length > 0"
             class="row flex-nowrap border-top mt-2 pt-2">
          <div class="col">
            <div class="font-weight-bold mb-2">Source properties:</div>

            <properties :properties="sourceProperties" :show-resource-info="false"/>
          </div>

          <div class="col">
            <div class="font-weight-bold mb-2">Target properties:</div>

            <properties :properties="targetProperties" :show-resource-info="false"/>
          </div>
        </div>
      </div>

      <div class="col-auto">
        <div class="row flex-column align-items-center">
          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-success m-1" @click="$emit('accepted')">
              <fa-icon icon="check"/>
              Accept
            </button>
          </div>

          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-danger m-1" @click="$emit('declined')">
              <fa-icon icon="times"/>
              Decline
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import Properties from "../../helpers/Properties";

    export default {
        name: "MatchLink",
        components: {
            Properties
        },
        props: {
            index: Number,
            link: Object,
        },
        computed: {
            bgColor() {
                if (this.link.valid === true)
                    return 'bg-success';

                if (this.link.valid === false)
                    return 'bg-danger';

                return 'bg-white';
            },

            sourceProperties() {
                if (!this.link.source_values)
                    return [];

                return this.link.source_values.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    };
                });
            },

            targetProperties() {
                if (!this.link.target_values)
                    return [];

                return this.link.target_values.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    };
                });
            },
        },
        methods: {
            async copySourceUriToClipboard() {
                await navigator.clipboard.writeText(this.source);
            },

            async copyTargetUriToClipboard() {
                await navigator.clipboard.writeText(this.target);
            },
        },
    };
</script>
