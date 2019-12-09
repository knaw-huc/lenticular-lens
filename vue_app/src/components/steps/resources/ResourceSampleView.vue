<template>
  <b-modal id="resource-sample-view" ref="resourceSampleView" size="xl"
           body-class="bg-light" dialog-class="modal-full-height" scrollable hide-footer static>
    <template v-slot:modal-header="{close}">
      <h5 class="modal-title">Sample</h5>

      <span v-if="!total" class="badge badge-info align-self-center font-italic ml-4">Loading total size</span>
      <span v-else class="badge badge-info align-self-center ml-4">Total: {{ total }}</span>

      <button type="button" aria-label="Close" class="close" @click="close()">×</button>
    </template>

    <property-selection label="Property selection" @save="saveProperties" :is-first="true"
                        :resource="resource" :properties="resource.properties"/>

    <div class="mt-4">
      <resource-sample v-for="(sample, idx) in samples" :index="idx" :sample="sample"/>

      <infinite-loading :identifier="samplesIdentifier" @infinite="getSamples">
        <template v-slot:spinner>
          <loading class="mt-4"/>
        </template>

        <template v-slot:no-more>
          No more data
        </template>

        <template v-slot:no-results>
          <template v-if="total === 0">This resource has no data</template>
          <template v-else-if="!hasProperties">Please select a property</template>
          <template v-else>Save selected properties to load results</template>
        </template>
      </infinite-loading>
    </div>
  </b-modal>
</template>

<script>
    import InfiniteLoading from 'vue-infinite-loading';
    import PropertySelection from "../../helpers/PropertySelection";
    import ResourceSample from "./ResourceSample";

    export default {
        name: "ResourceSampleView",
        components: {
            InfiniteLoading,
            PropertySelection,
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
        computed: {
            hasProperties() {
                return !this.resource.properties.map(prop => prop[0] !== '').includes(false);
            },
        },
        methods: {
            resetSample() {
                this.total = null;
                this.samples = [];
                this.samplesIdentifier += 1;

                this.getTotal();
                this.$refs.resourceSampleView.show();
            },

            async saveProperties() {
                await this.$root.submit();
                this.resetSample();
            },

            async getTotal() {
                const total = await this.$root.getResourceSample(this.resource.label, true);
                this.total = total.total;
            },

            async getSamples(state) {
                const samples = await this.$root.getResourceSample(this.resource.label, false, 50, this.samples.length);
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
