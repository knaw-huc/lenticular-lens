<template>
  <card :id="'clusters_match_' + match.id" type="clusters-matches" :label="match.label" :fill-label="false"
        @show="getLinksOrClusters()" @hide="showData = false">
    <template v-slot:columns>
      <div class="col-auto">
        <button type="button" class="btn btn-info btn-sm" v-b-toggle="'matches_info_' + match.id">
          <octicon name="chevron-down" scale="1" v-b-toggle="'matches_info_' + match.id"></octicon>
          Show alignment
        </button>
      </div>

      <div class="col-auto mr-auto">
        <button type="button" class="btn btn-info btn-sm" v-b-toggle="'properties_' + match.id">
          <octicon name="chevron-down" scale="1" v-b-toggle="'properties_' + match.id"></octicon>
          Select properties
        </button>
      </div>

      <div v-if="clustering" class="col-auto">
        <div class="h3 text-success">Clustered</div>
      </div>

      <div class="col-auto">
        <button v-if="clustering" type="button" class="btn btn-info"
                @click="createClustering($event)" :disabled="association === ''"
                :title="association === '' ? 'Choose an association first' : ''">Reconcile
        </button>

        <button v-if="!clustering" type="button" class="btn btn-info"
                @click="createClustering($event)">Cluster
          <template v-if="association !== ''"> &amp; Reconcile</template>
        </button>
      </div>

      <div v-if="associationFiles" class="col-auto">
        <select class="form-control" v-model="association" :id="'match_' + match.id + '_association'">
          <option value="">No association</option>
          <option v-for="association_file_name in associationFiles" :value="association_file_name">
            {{ association_file_name }}
          </option>
        </select>
      </div>
    </template>

    <template v-slot:header-sticky v-if="selectedCluster">
      <div class="bg-white border px-3 py-1 mt-2 mb-2">
        <div class="row font-weight-bold">
          <div class="col">Id</div>
          <div class="col">Extended</div>
          <div class="col">Reconciled</div>
          <div class="col">Size</div>
          <div class="col">Links</div>
          <div class="col-4">Property</div>
        </div>
      </div>

      <clustering :cluster-id="clusterIdSelected" :cluster-data="selectedCluster" :properties="properties"/>
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

      <sub-card>
        <div class="row">
          <div class="col-5">
            <div class="row">
              <div class="col-6 font-weight-bold">
                Links:
              </div>
              <div class="col-6">
                {{ alignment.links_count }}
              </div>
            </div>
            <div class="row" v-if="clustering">
              <div class="col-6 font-weight-bold">
                Extended Clusters:
              </div>
              <div class="col-6">
                {{ clustering.extended_count }}
              </div>
            </div>
            <div class="row" v-if="clustering">
              <div class="col-6 font-weight-bold">
                Clusters with Cycles:
              </div>
              <div class="col-6">
                {{ clustering.cycles_count }}
              </div>
            </div>
          </div>

          <div class="col-5" v-if="clustering">
            <div class="row">
              <div class="col-6 font-weight-bold">
                Clusters:
              </div>
              <div class="col-6">
                {{ clustering.clusters_count }}
              </div>
            </div>
            <div class="row">
              <div class="col-6 font-weight-bold">
                Clusters not Extended:
              </div>
              <div class="col-6">
                {{ clustering.clusters_count - clustering.extended_count }}
              </div>
            </div>
            <div class="row">
              <div class="col-6 font-weight-bold">
                Clusters without Cycles:
              </div>
              <div class="col-6">
                {{ clustering.clusters_count - clustering.cycles_count }}
              </div>
            </div>
          </div>
        </div>
      </sub-card>
    </template>

    <loading v-if="loading"/>

    <template v-else-if="!clustering">
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

    import Loading from "../../misc/Loading";

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
            Loading,
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
            async createClustering(event) {
                if (event) {
                    let btn = event.target;
                    btn.setAttribute('disabled', 'disabled');
                }

                const associationFile = this.clustering ? this.association : '';
                await this.$root.createClustering(this.match.id, associationFile, this.clustering);

                if (!this.clustering && this.association)
                    this.createClustering(this.match.id);
                else
                    this.$emit('reload');
            },

            async getLinksOrClusters() {
                this.loading = true;
                this.showData = true;

                if (this.clustering) {
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
                if (this.clustering) {
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
