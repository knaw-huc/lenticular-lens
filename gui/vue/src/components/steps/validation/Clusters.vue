<template>
  <b-modal ref="clusters" size="xl" body-class="bg-light" dialog-class="modal-full-height"
           scrollable hide-footer static @show="isOpen = true" @hide="isOpen = false">
    <template v-slot:modal-header="{close}">
      <h5 class="modal-title">Clusters</h5>

      <button type="button" aria-label="Close" class="close modal-header-close" @click="close()">×</button>
    </template>

    <cluster
        v-for="(cluster, idx) in clusters"
        :key="idx"
        :index="idx"
        :cluster="cluster"
        :selected="clusterSelected && clusterSelected.id === cluster.id"
        @select="$emit('select', cluster)"/>

    <infinite-loading v-if="isOpen" :identifier="clustersIdentifier" @infinite="getClusters">
      <template v-slot:spinner>
        <loading class="mt-4"/>
      </template>

      <template v-slot:no-more>
        No more clusters
      </template>

      <template v-slot:error="{trigger}">
        <div class="text-danger mb-2">
          Failed to obtain clusters
        </div>
        <button type="button" class="btn btn-sm btn-danger" @click="trigger">Retry</button>
      </template>
    </infinite-loading>
  </b-modal>
</template>

<script>
    import InfiniteLoading from 'vue-infinite-loading';

    import Cluster from "./Cluster";

    export default {
        name: "Clusters",
        components: {
            InfiniteLoading,
            Cluster
        },
        data() {
            return {
                isOpen: false,
                clusters: [],
                clustersIdentifier: +new Date(),
                loadingClusters: false,
            };
        },
        props: {
            type: String,
            specId: Number,
            clusterSelected: null,
        },
        computed: {
            clustering() {
                const clustering = this.$root.clusterings.find(clustering =>
                    clustering.spec_type === this.type && clustering.spec_id === this.specId);
                if (clustering && clustering.status === 'done')
                    return clustering;

                return null;
            },
        },
        methods: {
            show() {
                this.$refs.clusters.show();
            },

            async getClusters(state) {
                if (this.loadingClusters)
                    return;

                this.loadingClusters = true;

                const clusters = await this.$root.getClusters(this.type, this.specId,
                    {applyFilters: false}, 5, this.clusters.length);

                if (clusters !== null)
                    this.clusters.push(...clusters);

                if (state) {
                    if (clusters === null)
                        state.error();
                    else if (clusters.length > 0)
                        state.loaded();
                    else
                        state.complete();
                }

                this.loadingClusters = false;
            },

            resetClusters() {
                this.clusters = [];
                this.clustersIdentifier += 1;
            },
        },
    };
</script>
