<template>
  <b-modal id="sample-view" ref="sampleView" size="xl" header-class="flex-column align-items-stretch"
           body-class="bg-light" dialog-class="modal-full-height" scrollable hide-footer static>
    <template v-slot:modal-header="{close}">
      <div class="d-flex">
        <h5 class="modal-title">Sample</h5>

        <span class="align-self-center small ml-auto mr-4" v-bind:class="{'font-italic': !total}">
          <template v-if="!total">Loading total size</template>
          <template v-else>
            <span class="font-weight-bold">Total:</span>
            {{ total.toLocaleString('en') }} / {{ totalEntities.toLocaleString('en') }}
          </template>
        </span>

        <div class="btn-toolbar" role="toolbar">
          <div class="btn-group btn-group-toggle mr-2" data-toggle="buttons">
            <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showPropertySelection}">
              <input type="checkbox" autocomplete="off" v-model="showPropertySelection"/>
              <fa-icon icon="cog"/>
              Show property config
            </label>

            <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showFilteredOut}">
              <input type="checkbox" autocomplete="off" v-model="showFilteredOut" @change="resetSample(false)"/>
              <fa-icon icon="filter"/>
              Show filtered out
            </label>
          </div>
        </div>

        <button class="btn btn-secondary btn-sm" @click="saveProperties">
          Save and reload
        </button>

        <button type="button" aria-label="Close" class="close modal-header-close" @click="close()">×</button>
      </div>

      <property-selection v-if="showPropertySelection" class="mt-2"
                          :entity-type-selection="entityTypeSelection" :properties="entityTypeSelection.properties"/>
    </template>

    <sample v-for="(sample, idx) in samples" :key="idx" :index="idx" :sample="sample"/>

    <infinite-loading :identifier="samplesIdentifier" @infinite="getSamples">
      <template v-slot:spinner>
        <loading class="mt-4"/>
      </template>

      <template v-slot:no-more>
        No more data
      </template>

      <template v-slot:no-results>
        <template v-if="(!showFilteredOut && total === 0) || (showFilteredOut && total === total)">
          This entity-type selection has no data
        </template>
        <template v-else-if="!hasProperties">Please select a property</template>
        <template v-else>Save selected properties to load results</template>
      </template>

      <template v-slot:error="{trigger}">
        <div class="text-danger mb-2">
          Failed to obtain samples
        </div>
        <button type="button" class="btn btn-sm btn-danger" @click="trigger">Retry</button>
      </template>
    </infinite-loading>
  </b-modal>
</template>

<script>
    import InfiniteLoading from 'vue-infinite-loading';
    import PropertySelection from "../../helpers/PropertySelection";
    import Sample from "./Sample";

    export default {
        name: "SampleView",
        components: {
            InfiniteLoading,
            PropertySelection,
            Sample,
        },
        data() {
            return {
                total: null,
                samples: [],
                samplesIdentifier: +new Date(),
                showPropertySelection: false,
                showFilteredOut: false,
            };
        },
        props: {
            entityTypeSelection: Object,
        },
        computed: {
            totalEntities() {
                const datasets = this.$root.getDatasets(
                    this.entityTypeSelection.dataset.timbuctoo_graphql, this.entityTypeSelection.dataset.timbuctoo_hsid);

                return datasets[this.entityTypeSelection.dataset.dataset_id]
                    .collections[this.entityTypeSelection.dataset.collection_id]
                    .total;
            },

            hasProperties() {
                return this.entityTypeSelection.properties.length > 0 &&
                    !this.entityTypeSelection.properties.find(prop => prop[0] === '');
            },
        },
        methods: {
            resetSample(resetTotal = true) {
                this.samples = [];
                this.samplesIdentifier += 1;

                if (resetTotal) {
                    this.total = null;
                    this.getTotal();
                }

                this.$refs.sampleView.show();
            },

            async saveProperties() {
                await this.$root.submit();
                this.resetSample();
            },

            async getTotal() {
                const total = await this.$root.getEntityTypeSelectionSampleTotal(this.entityTypeSelection.id);
                this.total = total !== null ? total.total : null;
            },

            async getSamples(state) {
                const samples = await this.$root.getEntityTypeSelectionSample(
                    this.entityTypeSelection.id, this.showFilteredOut, 50, this.samples.length);

                if (samples !== null)
                    this.samples.push(...samples);

                if (state) {
                    if (samples === null)
                        state.error();
                    else if (samples.length > 0)
                        state.loaded();
                    else
                        state.complete();
                }
            },
        },
    };
</script>
