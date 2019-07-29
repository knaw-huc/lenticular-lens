<template>
  <card :id="'clusters_match_' + match.id" type="clusters-matches" :label="match.label" :fillLabel="false"
        @show="getClusters" @hide="showData = false">
    <template v-slot:columns>
      <div class="col-auto mr-auto">
        <button type="button" class="btn btn-info btn-sm" v-b-toggle="'matches_info_' + match.id">
          <octicon name="chevron-down" scale="1" v-b-toggle="'matches_info_' + match.id"></octicon>
          Show alignment
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

    <sub-card label="Properties">
      <div class="row ml-4" v-for="(property, idx) in this.match.properties"
           v-bind:class="{'mt-3': idx === 0}">
        <property
            v-if="property[0]"
            :property="property"
            :singular="true"
            :singular-resource-info="true"
            :follow-referenced-collection="false"
            @resetProperty="resetProperty(idx, property, $event)"/>
      </div>
    </sub-card>

    <cluster-table
        v-if="showData"
        :clusters="clusters"
        :cluster_id_selected="cluster_id_selected"
        @select:cluster_id="cluster_id_selected = $event"/>

    <cluster-visualization
        v-if="showData && cluster_id_selected && hasProperties"
        parent_tab="clusters"
        :clustering_id="clustering_id"
        :cluster_id="cluster_id_selected"
        :cluster_data="clusters[cluster_id_selected]"
        :properties="match.properties"
        :association="association"/>
  </card>
</template>

<script>
    import Card from "../../structural/Card";
    import SubCard from "../../structural/SubCard";
    import MatchInfo from "../../helpers/MatchInfo";
    import ClusterTable from "./ClusterTable";
    import ClusterVisualization from "./ClusterVisualization";

    export default {
        name: "Cluster",
        components: {
            Card,
            SubCard,
            MatchInfo,
            ClusterTable,
            ClusterVisualization,
        },
        data() {
            return {
                association: '',
                cluster_id_selected: null,
                showData: false,
                clustering_id: null,
                clusters: {},
            }
        },
        props: {
            match: Object,
        },
        computed: {
            hasProperties() {
                return !this.match.properties.map(res => res[1] !== '').includes(false);
            },

            associationFiles() {
                return this.$root.job.association_files;
            },
        },
        methods: {
            async getClusters() {
                this.showData = true;

                const results = this.getResultForMatch(this.match.id);
                if (results.clusterings.length > 0) {
                    this.clustering_id = results.clusterings[0].clustering_id;
                    this.clusters = await this.$root.getClusters(this.clustering_id, this.association);
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

            resetProperty(idx, property, property_index) {
                let new_property = property.slice(0, property_index);
                new_property.push('');
                if (new_property.length % 2 > 0) {
                    new_property.push('');
                }
                this.$set(this.match.properties, idx, new_property);
            },
        },
    }
</script>
