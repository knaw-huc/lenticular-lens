<template>
  <card :id="'clusters_match_' + match.id" type="clusters-matches" :label="match.label" :fill-label="false"
        @show="getClusters" @hide="showData = false">
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

    <template v-slot:header>
      <b-collapse :id="'matches_info_' + match.id" accordion="matches-info-accordion">
        <match-info :match="match"/>
      </b-collapse>

      <b-collapse :id="'properties_' + match.id" accordion="properties-accordion">
        <properties :properties="match.properties"/>
      </b-collapse>

      <sub-card v-if="clustering">
        <div class="row">
          <div class="col-5">
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
                Extended Clusters:
              </div>
              <div class="col-6">
                {{ clustering.extended_count }}
              </div>
            </div>
            <div class="row">
              <div class="col-6 font-weight-bold">
                Clusters with Cycles:
              </div>
              <div class="col-6">
                {{ clustering.cycles_count }}
              </div>
            </div>
          </div>

          <div class="col-5">
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

    <div class="bg-white border px-3 py-1 mt-4 mb-2">
      <div class="row font-weight-bold">
        <div class="col">Extended</div>
        <div class="col">Reconciled</div>
        <div class="col">Id</div>
        <div class="col">Count</div>
        <div class="col">Size</div>
      </div>
    </div>

    <virtual-list
        v-if="showData && hasProperties"
        :size="150"
        :remain="5"
        :item="item"
        :itemcount="clustering.clusters_count"
        :itemprops="getItemProps"/>

    <cluster-visualization
        v-if="showData && clusterIdSelected && hasProperties"
        :clustering-id="clusteringId"
        :cluster-id="clusterIdSelected"
        :cluster-data="clusters[clusterIdSelected]"
        :properties="match.properties"
        :association="association"/>
  </card>
</template>

<script>
    import VirtualList from 'vue-virtual-scroll-list';

    import Card from "../../structural/Card";
    import SubCard from "../../structural/SubCard";

    import MatchInfo from "../../helpers/MatchInfo";
    import Properties from "../../helpers/Properties";

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
            Clustering,
            ClusterVisualization,
        },
        data() {
            return {
                clusters: {},
                clusteringId: null,
                clusterIdSelected: null,
                association: '',
                properties: Object,
                item: Clustering,
                showData: false,
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

            async getClusters() {
                if (this.clustering) {
                    this.clusteringId = this.clustering.clustering_id;
                    const targets = this.$root.getTargetsForMatch(this.match.id);

                    this.clusters = await this.$root.getClusters(this.clusteringId, this.association);
                    this.properties = await this.$root.getProperties(this.resources, targets);

                    this.showData = true;
                }
            },

            getItemProps(idx) {
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
        },
        async mounted() {
            this.associationFiles = await this.$root.getAssociationFiles();
        }
    };
</script>
