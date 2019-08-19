<template>
  <card :id="'clusters_match_' + match.id" type="clusters-matches" :label="match.label" :fill-label="false"
        @show="getLinksOrClusters" @hide="showData = false">
    <template v-slot:title-extra>
      <div class="btn-group btn-group-toggle mt-1">
        <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showInfo}">
          <input type="checkbox" autocomplete="off" v-model="showInfo"/>
          <fa-icon icon="info-circle"/>
          {{ showInfo ? 'Hide' : 'Show' }} info
        </label>

        <label v-if="clustering && !clusteringRunning" class="btn btn-secondary btn-sm"
               v-bind:class="{'active': showClusters}">
          <input type="checkbox" autocomplete="off" v-model="showClusters" @change="getLinksOrClusters"/>
          <fa-icon icon="project-diagram"/>
          {{ showClusters ? 'Hide' : 'Show' }} clusters
        </label>
      </div>
    </template>

    <template v-slot:columns>
      <div class="col-auto ml-auto mr-auto">
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

      <div class="d-flex flex-column align-items-center">
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

    <template v-slot:header>
      <b-collapse :id="'matches_info_' + match.id" accordion="cluster-toggle-accordion" v-model="showInfo">
        <match-info :match="match"/>
      </b-collapse>
    </template>

    <sub-card :id="'properties_' + match.id" type="properties" label="Property selection" :has-collapse="true"
              :has-margin-auto="true" :has-columns="true">
      <template v-slot:columns>
        <div class="col-auto ml-auto">
          <button type="button" class="btn btn-info" @click="$root.submit">
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

    <template v-else-if="showClusters && clustering && !clusteringRunning">
      <sub-card label="Clusters" :has-collapse="true" :has-margin-auto="!!clusterIdSelected"
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
                       v-bind:class="{'active': toggleToView === 'links'}">
                  <input type="radio" v-model="toggleToView" value="links" autocomplete="off"/>
                  <fa-icon icon="align-justify"/>
                  Show links
                </label>

                <label v-if="hasProperties" class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': toggleToView === 'visualize'}">
                  <input type="radio" v-model="toggleToView" value="visualize" autocomplete="off"/>
                  <fa-icon icon="project-diagram"/>
                  Visualize
                </label>

                <label v-if="hasProperties" class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': toggleToView === 'visualize-compact'}">
                  <input type="radio" v-model="toggleToView" value="visualize-compact" autocomplete="off"/>
                  <fa-icon icon="project-diagram"/>
                  Visualize compact
                </label>

                <label v-if="hasProperties && association" class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': toggleToView === 'visualize-reconciled'}">
                  <input type="radio" v-model="toggleToView" value="visualize-reconciled" autocomplete="off"/>
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
            v-if="showData"
            :size="90"
            :remain="5"
            :item="clusterItem"
            :itemcount="clustering.clusters_count"
            :itemprops="getClusterItemProps"/>
      </sub-card>

      <cluster-visualization
          v-if="showData && clusterIdSelected && hasProperties && toggleToView.startsWith('visualize')"
          :show="toggleToView"
          :clustering-id="clustering.clustering_id"
          :cluster-id="clusterIdSelected"
          :cluster-data="clusters[clusterIdSelected]"
          :properties="match.properties"
          :association="association"/>
    </template>

    <virtual-list
        v-if="showData && showLinks"
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
                loading: false,
                showData: false,
                showInfo: false,
                showClusters: true,
                links: [],
                linkItem: MatchLink,
                clusters: {},
                clusterItem: Clustering,
                clusterIdSelected: null,
                toggleToView: '',
                association: '',
                properties: {},
                associationFiles: [],
            }
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

            showAllLinks() {
                return !this.showClusters || !this.clustering || this.clusteringRunning;
            },

            showClusterLinks() {
                return this.showClusters && this.clusterIdSelected && (this.toggleToView === 'links');
            },

            showLinks() {
                return this.showAllLinks || this.showClusterLinks;
            },

            resources() {
                const linkResources = Object.values(this.clusters)
                    .flatMap(cluster => cluster.links)
                    .flatMap(links => links)
                    .map(res => res.substring(1, res.length - 1));

                const nodeResources = Object.values(this.clusters)
                    .flatMap(cluster => cluster.nodes)
                    .map(res => res.substring(1, res.length - 1));

                return [...new Set(linkResources.concat(nodeResources))];
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
            async runClustering() {
                const associationFile = this.association !== '' ? this.association : null;
                await this.$root.runClustering(this.match.id, associationFile);
                this.$emit('refresh');
            },

            async getLinksOrClusters() {
                this.showData = true;

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

                this.loading = false;
            },

            async getLinks() {
                this.links = await this.$root.getAlignment(this.match.id);

                if (this.hasProperties) {
                    const targets = this.$root.getTargetsForMatch(this.match.id);
                    this.properties = await this.$root.getPropertiesForAlignment(this.match.id, targets);
                }
            },

            async getClusters() {
                if (this.clustering && this.clustering.status === 'Finished') {
                    this.clusters = await this.$root.getClusters(this.clustering.clustering_id, this.association);

                    if (this.hasProperties) {
                        const targets = this.$root.getTargetsForMatch(this.match.id);
                        this.properties = await this.$root.getProperties(this.resources, targets);
                    }
                }
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
                        source: link[0],
                        sourceValues: this.properties[link[0]] || [],
                        target: link[1],
                        targetValues: this.properties[link[1]] || [],
                        strength: parseFloat(link[2]).toFixed(3),
                        isFirst: (idx === 0),
                    },
                };
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