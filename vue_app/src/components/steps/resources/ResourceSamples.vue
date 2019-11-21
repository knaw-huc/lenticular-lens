<template>
  <b-modal id="resource-samples" ref="resourceSamples" size="xl" dialog-class="modal-full-size"
           scrollable hide-footer static>
    <template v-slot:modal-header="{close}">
      <h5 class="modal-title">Sample</h5>

      <span v-if="!total" class="badge badge-info align-self-center font-italic ml-4">Loading total size</span>
      <span v-else class="badge badge-info align-self-center ml-4">Total: {{ total }}</span>

      <button type="button" aria-label="Close" class="close" @click="close()">×</button>
    </template>

    <div class="p-4">
      <resource-sample v-for="(sample, idx) in samples" :index="idx" :sample="sample"/>

      <infinite-loading :identifier="samplesIdentifier" @infinite="getSamples">
        <template v-slot:spinner>
          <loading class="mt-4"/>
        </template>

        <template v-slot:no-more>
          No more data
        </template>
      </infinite-loading>
    </div>
  </b-modal>
</template>

<script>
    import InfiniteLoading from 'vue-infinite-loading';
    import ResourceSample from "./ResourceSample";

    export default {
        name: "ResourceSamples",
        components: {
            InfiniteLoading,
            ResourceSample,
        },
        data() {
            return {
                total: null,
                samples: [],
                samplesIdentifier: +new Date(),
            };
        },
        props: {
            'resource': Object,
        },
        methods: {
            resetSample() {
                this.total = null;
                this.samples = [];
                this.samplesIdentifier += 1;

                this.getTotal();
                this.$refs.resourceSamples.show();
            },

            async getTotal() {
                const total = await this.$root.getResourceSamples(this.resource.label, true);
                this.total = total.total;
            },

            async getSamples(state) {
                const samples = await this.$root.getResourceSamples(this.resource.label, false, 50, this.samples.length);
                this.samples.push(...samples);

                if (state) {
                    if (samples.length > 0)
                        state.loaded();
                    else
                        state.complete();
                }
            },
        },
    };
</script>
