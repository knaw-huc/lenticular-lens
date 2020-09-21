<template>
  <div class="border p-3 mb-4" v-bind:class="[bgColor]">
    <div class="row align-items-center flex-nowrap">
      <div class="col-auto d-flex flex-column align-items-center">
        <div class="col-auto">
          <span class="font-weight-bold font-italic"># {{ index + 1 }}</span>
        </div>

        <div class="col-auto">
          <div class="btn btn-sm bg-info-light border border-info text-info read-only m-1">
            <span class="font-weight-bold">Similarity</span><br>
            {{ similarity }}
          </div>
        </div>
      </div>

      <div class="col">
        <div class="text-break-all">
          <span class="font-weight-bold">Source URI:</span>

          <span class="text-info">
            {{ switchSourceAndTarget ? link.target : link.source }}
          </span>

          <button type="button" class="btn btn-sm ml-2" @click="copySourceUriToClipboard">
            <fa-icon icon="copy"/>
          </button>
        </div>

        <div class="text-break-all">
          <span class="font-weight-bold">Target URI:</span>

          <span class="text-info">
            {{ switchSourceAndTarget ? link.source : link.target }}
          </span>

          <button type="button" class="btn btn-sm ml-2" @click="copyTargetUriToClipboard">
            <fa-icon icon="copy"/>
          </button>
        </div>

        <div v-if="sourceValues.length > 0 || targetValues.length > 0" class="row flex-nowrap border-top mt-2 pt-2">
          <div class="col">
            <div class="font-weight-bold mb-2">Source properties:</div>

            <properties :properties="switchSourceAndTarget ? targetValues : sourceValues"/>
          </div>

          <div class="col">
            <div class="font-weight-bold mb-2">Target properties:</div>

            <properties :properties="switchSourceAndTarget ? sourceValues : targetValues"/>
          </div>
        </div>
      </div>

      <div class="col-auto">
        <div class="row flex-column align-items-center">
          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-success m-1" :disabled="isUpdating"
                    @click="$emit('accepted')">
              <fa-icon icon="check"/>
              Accept
            </button>
          </div>

          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-danger m-1" :disabled="isUpdating"
                    @click="$emit('rejected')">
              <fa-icon icon="times"/>
              Reject
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
        name: "Link",
        components: {
            Properties
        },
        props: {
            index: Number,
            link: Object,
        },
        computed: {
            similarity() {
                if (isNaN(this.link.similarity)) {
                    const similarityValues = Object.values(this.link.similarity);
                    return similarityValues.length > 0 ? Math.max(...similarityValues).toFixed(3) : '1.000';
                }

                return this.link.similarity.toFixed(3);
            },

            switchSourceAndTarget() {
                return this.link.link_order === 'target_source';
            },

            sourceValues() {
                return this.link.source_values || [];
            },

            targetValues() {
                return this.link.target_values || [];
            },

            isUpdating() {
                return this.link.updating;
            },

            bgColor() {
                if (this.link.valid === 'accepted')
                    return 'bg-success';

                if (this.link.valid === 'rejected')
                    return 'bg-danger';

                if (this.link.valid === 'mixed')
                    return 'bg-warning';

                return 'bg-white';
            },
        },
        methods: {
            async copySourceUriToClipboard() {
                await navigator.clipboard.writeText(
                    this.switchSourceAndTarget ? this.link.target : this.link.source);
            },

            async copyTargetUriToClipboard() {
                await navigator.clipboard.writeText(
                    this.switchSourceAndTarget ? this.link.source : this.link.target);
            },
        },
    };
</script>
