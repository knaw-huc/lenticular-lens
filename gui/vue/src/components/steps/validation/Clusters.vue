<template>
  <b-modal ref="clusters" size="xl" header-class="flex-column align-items-stretch" body-class="bg-light"
           dialog-class="modal-full-height" scrollable hide-footer static
           @show="onOpenClose(true)" @hide="onOpenClose(false)">
    <template v-slot:modal-header="{close}">
      <div class="d-flex align-items-center">
        <h5 class="modal-title">Clusters</h5>

        <div class="small ml-auto mr-5" v-bind:class="{'font-italic': !total}">
          <template v-if="!total">Loading total clusters</template>
          <template v-else>
            <span class="col-auto font-weight-bold">Total clusters:</span>
            {{ total.toLocaleString('en') }} / {{ clustering['clusters_count'].toLocaleString('en') }}
          </template>
        </div>

        <div v-if="hasSizeRange && hasLinksRange"
             class="btn-toolbar align-items-baseline" role="toolbar" aria-label="Toolbar">
          <div v-if="hasSizeRange"
               class="btn-group btn-group-sm btn-group-toggle input-group input-group-sm align-items-baseline mr-4">
            <div class="input-group-prepend">
              <div class="input-group-text bg-white">Size</div>

              <div class="input-group-text">
                <vue-slider v-model="sizeRange" class="mx-5 p-0" :width="100" :interval="1" :lazy="true"
                            :min="clustering['smallest_size']" :max="clustering['largest_size']"
                            :tooltip-placement="['left', 'right']" tooltip="always" @change="resetClusters"/>
              </div>
            </div>

            <label class="btn btn-secondary" v-bind:class="{'active': sort === 'size_desc'}">
              <input type="radio" autocomplete="off" v-model="sort" value="size_desc" @change="resetClusters"/>
              <fa-icon icon="sort-numeric-up"/>
            </label>

            <label class="btn btn-secondary" v-bind:class="{'active': sort === 'size_asc'}">
              <input type="radio" autocomplete="off" v-model="sort" value="size_asc" @change="resetClusters"/>
              <fa-icon icon="sort-numeric-down"/>
            </label>
          </div>

          <div v-if="hasLinksRange"
               class="btn-group btn-group-sm btn-group-toggle input-group input-group-sm align-items-baseline">
            <div class="input-group-prepend">
              <div class="input-group-text bg-white">Links</div>

              <div class="input-group-text">
                <vue-slider v-model="linksRange" class="mx-5 p-0" :width="100" :interval="1" :lazy="true"
                            :min="clustering['smallest_count']" :max="clustering['largest_count']"
                            :tooltip-placement="['left', 'right']" tooltip="always" @change="resetClusters"/>
              </div>
            </div>

            <label class="btn btn-secondary" v-bind:class="{'active': sort === 'count_desc'}">
              <input type="radio" autocomplete="off" v-model="sort" value="count_desc" @change="resetClusters"/>
              <fa-icon icon="sort-numeric-up"/>
            </label>

            <label class="btn btn-secondary" v-bind:class="{'active': sort === 'count_asc'}">
              <input type="radio" autocomplete="off" v-model="sort" value="count_asc" @change="resetClusters"/>
              <fa-icon icon="sort-numeric-down"/>
            </label>
          </div>
        </div>

        <button type="button" aria-label="Close" class="close modal-header-close" @click="close()">×</button>
      </div>
    </template>

    <cluster
        v-for="(clusterData, idx) in clusters"
        :key="idx"
        :index="idx"
        :cluster="clusterData.cluster"
        :selected="selectedClusters.includes(clusterData.cluster)"
        :is-lens="type === 'lens'"
        @mounted="observer.observe($event)"
        @select="$emit('select', clusterData.cluster)"/>

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
    import VueSlider from 'vue-slider-component';
    import InfiniteLoading from 'vue-infinite-loading';

    import Cluster from "./Cluster";

    export default {
        name: "Clusters",
        components: {
            VueSlider,
            InfiniteLoading,
            Cluster
        },
        data() {
            return {
                isOpen: false,
                total: null,

                sizeRange: [],
                linksRange: [],
                sort: 'size_desc',

                clusters: [],
                clustersIdentifier: +new Date(),

                loadingTotals: false,
                loadingClusters: false,

                observer: null,
            };
        },
        props: {
            type: String,
            specId: Number,
            selectedClusters: Array,
            similarityRange: Array,
        },
        computed: {
            clustering() {
                const clustering = this.$root.clusterings.find(clustering =>
                    clustering.spec_type === this.type && clustering.spec_id === this.specId);
                if (clustering && clustering.status === 'done')
                    return clustering;

                return null;
            },

            hasSizeRange() {
                return this.clustering['smallest_size'] < this.clustering['largest_size'];
            },

            hasLinksRange() {
                return this.clustering['smallest_count'] < this.clustering['largest_count'];
            },
        },
        methods: {
            show() {
                this.$refs.clusters.show();
            },

            onOpenClose(isOpen) {
                this.isOpen = isOpen;

                if (isOpen) {
                    if (this.total === null)
                        this.getClustersTotals();
                }
                else
                    this.$emit('closed');
            },

            async getClustersTotals() {
                if (this.loadingTotals)
                    return;

                this.loadingTotals = true;

                const totals = await this.$root.getClustersTotals(this.type, this.specId, {
                    applyFilters: false, minSize: this.sizeRange[0], maxSize: this.sizeRange[1],
                    minCount: this.linksRange[0], maxCount: this.linksRange[1]
                });

                if (totals)
                    this.total = totals.total || 0;

                this.loadingTotals = false;
            },

            async getClusters(state) {
                if (this.loadingClusters)
                    return;

                this.loadingClusters = true;

                const clusters = await this.$root.getClusters(this.type, this.specId, {
                    applyFilters: false, minSize: this.sizeRange[0], maxSize: this.sizeRange[1],
                    minCount: this.linksRange[0], maxCount: this.linksRange[1], sort: this.sort
                }, 5, this.clusters.length);

                if (clusters !== null)
                    this.clusters.push(...clusters.map(cluster => ({
                        cluster: {...cluster, linksFiltered: cluster.links, sizeFiltered: cluster.size},
                        updateProperties: false, updateFiltering: true
                    })));

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

            async resetClusters() {
                this.clusters = [];
                this.clustersIdentifier += 1;

                await this.getClustersTotals();
            },

            onObserved(entries) {
                const propertiesUpdateClusterIds = [];
                const filteringUpdateClusterIds = [];

                entries.forEach(({target, isIntersecting}) => {
                    if (!isIntersecting) return;

                    const idx = target.getAttribute('data-index');
                    if (this.clusters[idx].updateProperties)
                        propertiesUpdateClusterIds.push(this.clusters[idx].cluster.id);
                    if (this.clusters[idx].updateFiltering)
                        filteringUpdateClusterIds.push(this.clusters[idx].cluster.id);
                });

                if (propertiesUpdateClusterIds.length > 0)
                    this.updateProperties(propertiesUpdateClusterIds);

                if (filteringUpdateClusterIds.length > 0)
                    this.updateFiltering(filteringUpdateClusterIds);
            },

            async updateProperties(clusterIds) {
                const clusterDatas = this.clusters.filter(clusterData => clusterIds.includes(clusterData.cluster.id));
                clusterDatas.forEach(clusterData => clusterData.updateProperties = false);

                const clusters = await this.$root.getClusters(this.type, this.specId, {
                    clusterIds, applyFilters: false
                });

                clusterDatas.forEach(clusterData => {
                    const newCluster = clusters.find(cluster => cluster.id === clusterData.cluster.id);
                    if (newCluster)
                        clusterData.cluster.values = newCluster.values;
                });
            },

            async updateFiltering(clusterIds) {
                const clusterDatas = this.clusters.filter(clusterData => clusterIds.includes(clusterData.cluster.id));
                clusterDatas.forEach(clusterData => clusterData.updateFiltering = false);

                const clusters = await this.$root.getClusters(this.type, this.specId, {
                    clusterIds, withProperties: 'none', min: this.similarityRange[0], max: this.similarityRange[1]
                });

                clusterDatas.forEach(clusterData => {
                    const newCluster = clusters.find(cluster => cluster.id === clusterData.cluster.id);
                    clusterData.cluster.linksFiltered = newCluster ? newCluster.links : {};
                    clusterData.cluster.sizeFiltered = newCluster ? newCluster.size : 0;
                });
            },

            triggerPropertiesUpdate() {
                this.clusters.forEach(clusterData => clusterData.updateProperties = true);
            },

            triggerFilteringUpdate() {
                this.clusters.forEach(clusterData => clusterData.updateFiltering = true);
            },
        },
        mounted() {
            this.observer = new IntersectionObserver(this.onObserved, {
                root: this.$el.querySelector('.modal-body')
            });

            if (this.sizeRange.length !== 2)
                this.sizeRange = [this.clustering['smallest_size'], this.clustering['largest_size']];

            if (this.linksRange.length !== 2)
                this.linksRange = [this.clustering['smallest_count'], this.clustering['largest_count']];
        },
        beforeDestroy() {
            this.observer.disconnect();
        },
    };
</script>
