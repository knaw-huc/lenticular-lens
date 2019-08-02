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

      <div v-if="getResultForMatch(match.id).clusterings.length > 0" class="col-auto">
        <div class="h3 text-success">Clustered</div>
      </div>

      <div class="col-auto">
        <button v-if="getResultForMatch(match.id).clusterings.length > 0" type="button" class="btn btn-info"
                @click="createClustering(match.id, $event)" :disabled="association === ''"
                :title="association === '' ? 'Choose an association first' : ''">Reconcile
        </button>
        <button v-if="getResultForMatch(match.id).clusterings.length === 0" type="button" class="btn btn-info"
                @click="createClustering(match.id, $event)">Cluster
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

      <sub-card v-if="getResultForMatch(match.id).clusterings.length > 0">
        <div class="row">
          <div class="col-5">
            <div class="row">
              <div class="col-6 font-weight-bold">
                Clusters:
              </div>
              <div class="col-6">
                {{ getResultForMatch(match.id).clusterings[0].clusters_count }}
              </div>
            </div>
            <div class="row">
              <div class="col-6 font-weight-bold">
                Extended Clusters:
              </div>
              <div class="col-6">
                {{ getResultForMatch(match.id).clusterings[0].extended_count }}
              </div>
            </div>
            <div class="row">
              <div class="col-6 font-weight-bold">
                Clusters with Cycles:
              </div>
              <div class="col-6">
                {{ getResultForMatch(match.id).clusterings[0].cycles_count }}
              </div>
            </div>
          </div>

          <div class="col-5">
            <div class="row">
              <div class="col-6 font-weight-bold">
                Clusters not Extended:
              </div>
              <div class="col-6">
                {{ getResultForMatch(match.id).clusterings[0].clusters_count -
                getResultForMatch(match.id).clusterings[0].extended_count }}
              </div>
            </div>
            <div class="row">
              <div class="col-6 font-weight-bold">
                Clusters without Cycles:
              </div>
              <div class="col-6">
                {{ getResultForMatch(match.id).clusterings[0].clusters_count -
                getResultForMatch(match.id).clusterings[0].cycles_count }}
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
        :itemcount="getResultForMatch(match.id).clusterings[0].clusters_count"
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

            associationFiles() {
                return this.$root.job.association_files;
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
            async getClusters() {
                const results = this.getResultForMatch(this.match.id);
                if (results.clusterings.length > 0) {
                    this.clusteringId = results.clusterings[0].clustering_id;
                    const targets = this.$root.getTargetsForMatch(this.match.id);

                    this.clusters = await this.$root.getClusters(this.clusteringId, this.association);
                    this.properties = await this.$root.loadProperties(this.resources, targets);

                    this.showData = true;
                }
            },

            getResultForMatch(match_id) {
                let clusterings = [];

                if (this.$root.job) {
                    this.$root.job.results.clusterings.forEach(clustering => {
                        if (clustering.alignment === match_id)
                            clusterings.push(clustering);
                    });
                }

                return {'clusterings': clusterings};
            },

            async createClustering(mapping_id, event) {
                if (event) {
                    let btn = event.target;
                    btn.setAttribute('disabled', 'disabled');
                }

                const clustered = this.getResultForMatch(mapping_id).clusterings.length > 0;
                const associationFile = clustered ? this.association : '';

                await this.$root.createClustering(mapping_id, associationFile, clustered);

                if (!clustered && this.association)
                    this.createClustering(mapping_id);
                else
                    this.$emit('reload');
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
    };
</script>
