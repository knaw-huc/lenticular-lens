<template>
  <div class="border p-3" v-bind:class="[{'mt-2': !isFirst}, ...bgColor]">
    <div class="row align-items-center">
      <div class="col-auto">
        <div class="btn btn-sm bg-info-light border border-info text-info read-only m-1">
          <span class="font-weight-bold">Strength</span><br>
          {{ strength }}
        </div>
      </div>

      <div class="col">
        <div class="row align-items-center m-0">
          <div class="property-path btn-sm read-only">
            Source URI
          </div>

          <button type="button" class="property-value btn-sm read-only ml-2" @click="copySourceUriToClipboard">
            <fa-icon :icon="['far', 'clipboard']"/>
            Copy to clipboard
          </button>

          <span class="badge badge-info ml-2" ref="sourceClipboardCopyMessage" hidden>
            Source URI copied to clipboard
          </span>
        </div>

        <properties :properties="sourceProperties" :show-resource-info="false"/>
      </div>

      <div class="col">
        <div class="row align-items-center m-0">
          <div class="property-path btn-sm read-only">
            Target URI
          </div>

          <button type="button" class="property-value btn-sm read-only ml-2" @click="copyTargetUriToClipboard">
            <fa-icon :icon="['far', 'clipboard']"/>
            Copy to clipboard
          </button>

          <span class="badge badge-info ml-2" ref="targetClipboardCopyMessage" hidden>
            Target URI copied to clipboard
          </span>
        </div>

        <properties :properties="targetProperties" :show-resource-info="false"/>
      </div>

      <div class="col-auto">
        <div class="row flex-column align-items-center">
          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-success m-1" :disabled="state"
                    @click="$emit('accepted')">
              <fa-icon icon="check"/>
              Accept
            </button>
          </div>

          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-danger m-1" :disabled="state"
                    @click="$emit('declined')">
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

                this.$refs.sourceClipboardCopyMessage.removeAttribute('hidden');
                setTimeout(() => this.$refs.sourceClipboardCopyMessage.setAttribute('hidden', 'hidden'), 2000);
            },

            async copyTargetUriToClipboard() {
                await navigator.clipboard.writeText(this.target);

                this.$refs.targetClipboardCopyMessage.removeAttribute('hidden');
                setTimeout(() => this.$refs.targetClipboardCopyMessage.setAttribute('hidden', 'hidden'), 2000);
            },
        },
    };
</script>
