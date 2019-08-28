<template>
  <div class="border p-3" v-bind:class="[{'mt-4': !isFirst}, ...bgColor]">
    <div class="row align-items-center flex-nowrap">
      <div class="col-auto d-flex flex-column align-items-center">
        <div class="col-auto">
          <span class="font-weight-bold font-italic"># {{ index + 1 }}</span>
        </div>

        <div class="col-auto">
          <div class="btn btn-sm bg-info-light border border-info text-info read-only m-1">
            <span class="font-weight-bold">Strength</span><br>
            {{ strength }}
          </div>
        </div>
      </div>

      <div class="col">
        <div class="row justify-content-center flex-nowrap">
          <div class="property-path btn-sm read-only">
            Source URI
          </div>

          <div class="property-value btn-sm read-only ml-2">
            {{ source }}
          </div>

          <button type="button" class="property-value btn-sm read-only ml-2" @click="copySourceUriToClipboard">
            <fa-icon :icon="['far', 'clipboard']"/>
          </button>
        </div>

        <div class="row justify-content-center flex-nowrap">
          <div class="property-path btn-sm read-only">
            Target URI
          </div>

          <div class="property-value btn-sm read-only ml-2">
            {{ target }}
          </div>

          <button type="button" class="property-value btn-sm read-only ml-2" @click="copyTargetUriToClipboard">
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
            state: String,
            source: String,
            sourceValues: Array,
            target: String,
            targetValues: Array,
            strength: String,
            isFirst: Boolean,
        },
        computed: {
            bgColor() {
                if (this.state === 'accepted')
                    return 'bg-success';

                if (this.state === 'declined')
                    return 'bg-danger';

                return 'bg-white';
            },

            sourceProperties() {
                return this.sourceValues.map(value => {
                    return {
                        property: [this.$root.getResourceByDatasetId(value.dataset).id, value.property],
                        values: value.values,
                    };
                });
            },

            targetProperties() {
                return this.targetValues.map(value => {
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
