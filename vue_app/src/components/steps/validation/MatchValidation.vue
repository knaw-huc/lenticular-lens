<template>
  <card :id="'clusters_match_' + match.id" type="clusters-matches" :label="match.label" :fill-label="false"
        :open-card="show" @show="updateShow('open')" @hide="updateShow('close')">
    <template v-slot:columns>
      <div class="col-auto d-flex flex-column align-items-center ml-auto mr-auto">
        <div class="col-auto">
          <div class="bg-white border small p-2">
            <div class="row align-items-center m-0">
              <div class="col-auto" v-if="clusteringRunning">
                <loading :small="true"/>
              </div>

              <div class="col-auto">
                <div>
                  <strong>Links: </strong>
                  {{ alignment.links_count }}
                </div>
                <div>
                  <strong>Clustering request: </strong>
                  <template v-if="clustering">{{ clustering.requested_at }}</template>
                  <template v-else>-</template>
                </div>
                <div>
                  <strong>Clustering started at: </strong>
                  <template v-if="clustering && clustering.processing_at">{{ clustering.processing_at }}</template>
                  <template v-else>-</template>
                </div>
                <div>
                  <strong>Clustering finished at: </strong>
                  <template v-if="clustering && clustering.finished_at">{{ clustering.finished_at }}</template>
                  <template v-else>-</template>
                </div>
                <div>
                  <strong>Status: </strong>
                  <pre v-if="clustering" class="d-inline">{{ clustering.status }}</pre>
                  <pre v-else class="d-inline">Not yet clustered</pre>
                </div>
              </div>

              <div class="col-auto">
                <div>
                  <strong>Clusters: </strong>
                  <template v-if="clustering && clustering.status === 'Finished'">
                    {{ clustering.clusters_count }}
                  </template>
                  <template v-else>-</template>
                </div>
                <div>
                  <strong>Extended Clusters: </strong>
                  <template v-if="clustering && clustering.status === 'Finished'">
                    {{ clustering.extended_count || 0 }}
                  </template>
                  <template v-else>-</template>
                </div>
                <div>
                  <strong>Clusters with Cycles: </strong>
                  <template v-if="clustering && clustering.status === 'Finished'">
                    {{ clustering.cycles_count || 0 }}
                  </template>
                  <template v-else>-</template>
                </div>
                <div>
                  <strong>Clusters not Extended: </strong>
                  <template v-if="clustering && clustering.status === 'Finished'">
                    {{ clustering.clusters_count - clustering.extended_count }}
                  </template>
                  <template v-else>-</template>
                </div>
                <div>
                  <strong>Clusters without Cycles: </strong>
                  <template v-if="clustering && clustering.status === 'Finished'">
                    {{ clustering.clusters_count - clustering.cycles_count }}
                  </template>
                  <template v-else>-</template>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-auto">
          <div class="btn-toolbar mt-2" role="toolbar" aria-label="Toolbar">
            <div class="btn-group btn-group-toggle mr-2">
              <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showInfo}">
                <input type="checkbox" autocomplete="off" v-model="showInfo" @change="updateShow"/>
                <fa-icon icon="info-circle"/>
                Alignment specs
              </label>

              <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showPropertySelection}">
                <input type="checkbox" autocomplete="off" v-model="showPropertySelection" @change="updateShow"/>
                <fa-icon icon="cog"/>
                Properties
              </label>

              <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showAllLinks}">
                <input type="checkbox" autocomplete="off" v-model="showAllLinks" @change="updateShow('links')"/>
                <fa-icon icon="list"/>
                Links
              </label>

              <label v-if="clustering && !clusteringRunning" class="btn btn-secondary btn-sm"
                     v-bind:class="{'active': showClusters}">
                <input type="checkbox" autocomplete="off" v-model="showClusters" @change="updateShow('clusters')"/>
                <fa-icon icon="list"/>
                Clusters
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="col-auto d-flex flex-column align-items-center">
        <div class="col-auto">
          <button v-if="clustering && !clusteringRunning" type="button" class="btn btn-info my-1"
                  @click="runClustering($event)" :disabled="association === ''"
                  :title="association === '' ? 'Choose an association first' : ''">
            Reconcile
          </button>

          <button v-else-if="!clustering && !clusteringRunning" type="button" class="btn btn-info my-1"
                  @click="runClustering($event)">
            Cluster
            <template v-if="association !== ''"> &amp; Reconcile</template>
          </button>
        </div>

        <div class="col-auto" v-if="associationFiles">
          <select class="col-auto form-control association-select my-1" v-model="association"
                  :id="'match_' + match.id + '_association'">
            <option value="">No association</option>
            <option v-for="association_file_name in associationFiles" :value="association_file_name">
              {{ association_file_name }}
            </option>
          </select>
        </div>
      </div>
    </template>

    <match-info v-if="showInfo" :match="match"/>

    <sub-card v-if="showPropertySelection" :id="'properties_card_' + match.id" type="properties"
              label="Property selection" :has-margin-auto="true" :has-columns="true">
      <template v-slot:columns>
        <div class="col-auto ml-auto">
          <button type="button" class="btn btn-info" @click="saveProperties">
            Save
          </button>
        </div>
      </template>

      <div class="mt-4">
        <property
            v-for="(property, idx) in match.properties"
            v-if="property[0]"
            class="mx-0"
            :key="idx"
            :property="property"
            :singular="false"
            :follow-referenced-collection="false"
            :allow-delete="match.properties.findIndex(p => p[0] === property[0]) !== idx"
            @clone="match.properties.splice(idx + 1, 0, [match.properties[idx][0], ''])"
            @delete="$delete(match.properties, idx)"
            @resetProperty="resetProperty(idx, property, $event)"/>
      </div>
    </sub-card>

    <loading v-if="loading" class="mt-4"/>

    <template v-if="!loading && showClusters && clustering && !clusteringRunning">
      <sub-card label="Clusters" :open-card="true" :has-collapse="true" :has-margin-auto="!!clusterIdSelected"
                id="clusters-list" type="clusters-list">
        <template v-slot:columns>
          <template v-if="clusterIdSelected">
            <div class="col-auto small ml-auto mr-auto">
              <strong>Selected cluster: </strong>
              {{ clusterIdSelected }}
            </div>

            <div class="col-auto">
              <div class="btn-group btn-group-toggle">
                <label class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': clusterView === 'links'}">
                  <input type="radio" v-model="clusterView" value="links" autocomplete="off"/>
                  <fa-icon icon="align-justify"/>
                  Show links
                </label>

                <label v-if="hasProperties" class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': clusterView === 'visualize'}">
                  <input type="radio" v-model="clusterView" value="visualize" autocomplete="off"/>
                  <fa-icon icon="project-diagram"/>
                  Visualize
                </label>

                <label v-if="hasProperties" class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': clusterView === 'visualize-compact'}">
                  <input type="radio" v-model="clusterView" value="visualize-compact" autocomplete="off"/>
                  <fa-icon icon="project-diagram"/>
                  Visualize compact
                </label>

                <label v-if="hasProperties && association" class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': clusterView === 'visualize-reconciled'}">
                  <input type="radio" v-model="clusterView" value="visualize-reconciled" autocomplete="off"/>
                  <fa-icon icon="project-diagram"/>
                  Visualize reconciled
                </label>
              </div>
            </div>
          </template>
        </template>

        <div class="bg-white px-3 py-1 mt-4 mb-2">
          <div class="row font-weight-bold">
            <div class="col">Id</div>
            <div class="col">Extended</div>
            <div class="col">Reconciled</div>
            <div class="col">Size</div>
            <div class="col">Links</div>
            <div class="col-4">Property</div>
          </div>
        </div>

        <virtual-list
            :size="90"
            :remain="5"
            :item="clusterItem"
            :itemcount="clustering.clusters_count"
            :itemprops="getClusterItemProps"/>
      </sub-card>

      <cluster-visualization
          v-if="!loading && showClusters && clusterIdSelected && hasProperties && clusterView.startsWith('visualize')"
          :show="clusterView"
          :clustering-id="clustering.clustering_id"
          :cluster-id="clusterIdSelected"
          :cluster-data="clusters[clusterIdSelected]"
          :properties="match.properties"
          :association="association"/>
    </template>

    <virtual-list
        v-if="!loading && showLinks"
        class="mt-4"
        :size="130"
        :remain="5"
        :item="linkItem"
        :pagemode="true"
        :itemcount="showAllLinks ? links.length : clusterLinks.length"
        :itemprops="getLinkItemProps"/>
  </card>
</template>

<script>
    import VirtualList from 'vue-virtual-scroll-list';

    import Card from "../../structural/Card";
    import SubCard from "../../structural/SubCard";

    import MatchInfo from "../../helpers/MatchInfo";
    import Properties from "../../helpers/Properties";

    import MatchLink from "./MatchLink";
    import Clustering from "./Clustering";
    import ClusterVisualization from "./ClusterVisualization";

    export default {
        name: "MatchValidation",
        components: {
            VirtualList,
            Card,
            SubCard,
            MatchInfo,
            Properties,
            MatchLink,
            Clustering,
            ClusterVisualization,
        },
        data() {
            return {
                show: false,
                showInfo: false,
                showPropertySelection: false,
                showAllLinks: false,
                showClusters: false,
                loading: false,
                links: [],
                linkItem: MatchLink,
                clusters: {},
                clusterItem: Clustering,
                clusterIdSelected: null,
                clusterView: '',
                association: '',
                properties: {},
                associationFiles: [],
                linkStates: {},
            };
        },
        props: {
            match: Object,
        },
        computed: {
            clusterIds() {
                return Object.keys(this.clusters);
            },

            hasProperties() {
                return !this.match.properties.map(res => res[1] !== '').includes(false);
            },

            alignment() {
                return this.$root.alignments.find(alignment => alignment.alignment === this.match.id);
            },

            clustering() {
                return this.$root.clusterings.find(clustering => clustering.alignment === this.match.id);
            },

            clusteringRunning() {
                return this.clustering &&
                    this.clustering.status !== 'Finished' &&
                    !this.clustering.status.startsWith('FAILED');
            },

            showLinks() {
                return this.showAllLinks || this.showClusterLinks;
            },

            showClusterLinks() {
                return this.showClusters && this.clusterIdSelected && (this.clusterView === 'links');
            },

            selectedCluster() {
                if (!this.clusterIdSelected)
                    return null;

                return this.clusters[this.clusterIdSelected];
            },

            clusterLinks() {
                if (!this.selectedCluster)
                    return [];

                return this.selectedCluster.links.map(link => {
                    return [
                        link[0].substring(1, link[0].length - 1),
                        link[1].substring(1, link[1].length - 1),
                        '1'
                    ];
                });
            },
        },
        methods: {
            updateShow(state) {
                const showSomething = this.showInfo || this.showPropertySelection
                    || this.showAllLinks || this.showClusters;

                if (state === 'open' && !showSomething)
                    this.showInfo = true;
                else if (state === 'close' && showSomething) {
                    this.showInfo = false;
                    this.showPropertySelection = false;
                    this.showAllLinks = false;
                    this.showClusters = false;
                }
                else if (state !== 'open' && state !== 'close')
                    this.show = showSomething;

                if (state === 'links' && this.showClusters)
                    this.showClusters = false;
                else if (state === 'clusters' && this.showAllLinks)
                    this.showAllLinks = false;

                if (this.showAllLinks || this.showClusters)
                    this.getLinksOrClusters();
            },

            async saveProperties() {
                await this.$root.submit();
                await this.getLinksOrClusters(true);
            },

            async runClustering() {
                const associationFile = this.association !== '' ? this.association : null;
                await this.$root.runClustering(this.match.id, associationFile);
                this.$emit('refresh');
            },

            async getLinksOrClusters(hard = false) {
                if (this.showClusters && this.clustering && (this.clustering.status === 'Finished')
                    && (Object.keys(this.clusters).length === 0)) {
                    this.loading = true;
                    this.links = [];
                    await this.getClusters();
                }
                else if ((!this.showClusters || !this.clustering || !this.clusteringRunning)
                    && (this.links.length === 0)) {
                    this.loading = true;
                    this.clusters = {};
                    await this.getLinks();
                }

                if (this.hasProperties && (hard || (Object.keys(this.properties).length === 0))) {
                    this.loading = true;

                    const targets = this.$root.getTargetsForMatch(this.match.id);
                    this.properties = await this.$root.getPropertiesForAlignment(this.match.id, targets);
                }

                this.loading = false;
            },

            async getLinks() {
                this.links = await this.$root.getAlignment(this.match.id);
            },

            async getClusters() {
                if (this.clustering && this.clustering.status === 'Finished')
                    this.clusters = await this.$root.getClusters(this.clustering.clustering_id, this.association);
            },

            getClusterItemProps(idx) {
                const clusterId = this.clusterIds[idx];
                return {
                    props: {
                        clusterId: clusterId,
                        clusterData: this.clusters[clusterId],
                        properties: this.properties,
                        selected: this.clusterIdSelected === clusterId,
                        isFirst: idx === 0,
                    },
                    on: {
                        'select:clusterId': clusterId => this.clusterIdSelected = clusterId,
                    }
                };
            },

            getLinkItemProps(idx) {
                const link = this.showAllLinks ? this.links[idx] : this.clusterLinks[idx];
                return {
                    props: {
                        state: this.linkStates[this.getLinkHash(link[0], link[1])],
                        source: link[0],
                        sourceValues: this.properties[link[0]] || [],
                        target: link[1],
                        targetValues: this.properties[link[1]] || [],
                        strength: parseFloat(link[2]).toFixed(3),
                        isFirst: (idx === 0),
                    },
                    on: {
                        accepted: () => this.acceptLink(link[0], link[1]),
                        declined: () => this.declineLink(link[0], link[1]),
                    },
                };
            },

            getLinkHash(source, target) {
                if (source < target)
                    return this.$utilities.md5(source + '-' + target);

                return this.$utilities.md5(target + '-' + source);
            },

            acceptLink(source, target) {
                this.$set(this.linkStates, this.getLinkHash(source, target), 'accepted');
            },

            declineLink(source, target) {
                this.$set(this.linkStates, this.getLinkHash(source, target), 'declined');
            },

            resetProperty(idx, property, propertyIndex) {
                const newProperty = property.slice(0, propertyIndex);
                newProperty.push('');

                if (newProperty.length % 2 > 0)
                    newProperty.push('');

                this.$set(this.match.properties, idx, newProperty);
            },
        },
        async mounted() {
            this.associationFiles = await this.$root.getAssociationFiles();
        },
    };
</script>

<style>
  .association-select {
    width: 160px !important;
  }
</style>