<template>
  <card :id="'clusters_match_' + match.id" type="clusters-matches" :label="match.label" :fill-label="false"
        @show="getLinksOrClusters()" @hide="showData = false">
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
                <strong>Clustering request received at: </strong>
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
        <div class="d-flex flex-column align-items-center">
          <div class="row my-1">
            <div class="col-auto">
              <button type="button" class="btn btn-sm btn-info" v-b-toggle="'matches_info_' + match.id">
                <octicon name="chevron-down" scale="1" v-b-toggle="'matches_info_' + match.id"></octicon>
                Show alignment
              </button>
            </div>

            <div class="col-auto">
              <button type="button" class="btn btn-sm btn-info" v-b-toggle="'properties_' + match.id">
                <octicon name="chevron-down" scale="1" v-b-toggle="'properties_' + match.id"></octicon>
                Select properties
              </button>
            </div>
          </div>

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

          <select v-if="associationFiles" class="form-control association-select my-1" v-model="association"
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
      <b-collapse :id="'matches_info_' + match.id" accordion="cluster-toggle-accordion">
        <match-info :match="match"/>
      </b-collapse>

      <b-collapse :id="'properties_' + match.id" accordion="cluster-toggle-accordion">
        <sub-card>
          <property
              v-for="(property, idx) in match.properties"
              v-if="property[0]"
              class="mx-0"
              :property="property"
              :singular="true"
              :follow-referenced-collection="false"
              @resetProperty="resetProperty(idx, property, $event)"/>
        </sub-card>
      </b-collapse>
    </template>

    <loading v-if="loading" class="mt-4"/>

    <template v-else-if="!clustering || clusteringRunning">
      <virtual-list
          v-if="showData"
          class="mt-4"
          :size="130"
          :remain="5"
          :item="linkItem"
          :pagemode="true"
          :itemcount="links.length"
          :itemprops="getLinkItemProps"/>
    </template>

    <template v-else>
      <sub-card label="Clusters" :has-collapse="true" id="clusters-list" type="clusters-list">
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

      <sub-card v-if="showData && clusterIdSelected" label="Links" :has-collapse="true"
                id="cluster-links" type="cluster-links">
        <virtual-list
            class="mt-4"
            :size="130"
            :remain="5"
            :item="linkItem"
            :pagemode="true"
            :itemcount="clusterLinks.length"
            :itemprops="getClusterLinkItemProps"/>
      </sub-card>

      <cluster-visualization
          v-if="showData && clusterIdSelected && hasProperties"
          :clustering-id="clustering.clustering_id"
          :cluster-id="clusterIdSelected"
          :cluster-data="clusters[clusterIdSelected]"
          :properties="match.properties"
          :association="association"/>
    </template>
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
        name: "Cluster",
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
                links: [],
                linkItem: MatchLink,
                clusters: {},
                clusterItem: Clustering,
                clusterIdSelected: null,
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
                this.loading = true;
                this.showData = true;

                if (this.clustering && this.clustering.status === 'Finished') {
                    this.links = [];
                    await this.getClusters();
                }
                else {
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

            getLinkItemProps(idx) {
                const link = this.links[idx];
                return {
                    props: {
                        source: link[0],
                        sourceValues: this.properties[link[0]] || [],
                        target: link[1],
                        targetValues: this.properties[link[1]] || [],
                        strength: link[2],
                        isFirst: (idx === 0),
                    },
                };
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

            getClusterLinkItemProps(idx) {
                const link = this.clusterLinks[idx];
                return {
                    props: {
                        source: link[0],
                        sourceValues: this.properties[link[0]] || [],
                        target: link[1],
                        targetValues: this.properties[link[1]] || [],
                        strength: link[2],
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
        }
    };
</script>

<style>
  .association-select {
    width: 160px !important;
  }
</style>