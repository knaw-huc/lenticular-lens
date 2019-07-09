<template>
  <div class="border p-4 mt-4 bg-light">
    <div class="row align-items-center justify-content-between">
      <div class="col-auto">
        <octicon name="chevron-down" scale="3" v-b-toggle="'clustering_clusters_match_' + match.id"></octicon>
      </div>

      <div class="col" v-b-toggle="'clustering_clusters_match_' + match.id">
        <div class="h2">{{ match.label }}</div>
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

      <div v-if="app.job_data" class="col-auto">
        <select class="form-control" v-model="association" :id="'match_' + match.id + '_association'">
          <option value="">No association</option>
          <option v-for="association_file_name in app.job_data.association_files" :value="association_file_name">
            {{ association_file_name }}
          </option>
        </select>
      </div>
    </div>

    <div class="row mt-3" v-if="getResultForMatch(match.id).clusterings.length > 0">
      <div class="col-5">
        <div class="row">
          <div class="col-6">
            Clusters:
          </div>
          <div class="col-6">
            {{ getResultForMatch(match.id).clusterings[0].clusters_count }}
          </div>
        </div>
        <div class="row">
          <div class="col-6">
            Extended Clusters:
          </div>
          <div class="col-6">
            {{ getResultForMatch(match.id).clusterings[0].extended_count }}
          </div>
        </div>
        <div class="row">
          <div class="col-6">
            Clusters with Cycles:
          </div>
          <div class="col-6">
            {{ getResultForMatch(match.id).clusterings[0].cycles_count }}
          </div>
        </div>
      </div>
      <div class="col-5">
        <div class="row">
          <div class="col-6">
            Clusters not Extended:
          </div>
          <div class="col-6">
            {{ getResultForMatch(match.id).clusterings[0].clusters_count -
            getResultForMatch(match.id).clusterings[0].extended_count }}
          </div>
        </div>
        <div class="row">
          <div class="col-6">
            Clusters without Cycles:
          </div>
          <div class="col-6">
            {{ getResultForMatch(match.id).clusterings[0].clusters_count -
            getResultForMatch(match.id).clusterings[0].cycles_count }}
          </div>
        </div>
      </div>
    </div>

    <b-collapse
        @show="getClusters(getResultForMatch(match.id).clusterings[0].clustering_id)"
        v-model="showData"
        :id="'clustering_clusters_match_' + match.id"
        class="pt-3"
        accordion="clusters-matches-accordion"
    >
      <div class="shadow p-3 border mb-3 bg-info-light border-info">
        <div class="row">
          <div class="h4 col-auto">Properties</div>
        </div>

        <div class="row ml-4" v-for="(property, idx) in this.properties">
          <property-component
              :property="property"
              :singular="true"
              :singular-resource-info="true"
              :follow-referenced-collection="false"
              @resetProperty="resetProperty(idx, property, $event)"
          />
        </div>
      </div>

      <cluster-table-component
          v-if="showData"
          :clusters="clusters"
          :cluster_id_selected="cluster_id_selected"
          @select:cluster_id="cluster_id_selected = $event"
      />

      <cluster-visualization-component
          v-if="showData && cluster_id_selected && hasProperties"
          parent_tab="clusters"
          :clustering_id="clustering_id"
          :cluster_id="cluster_id_selected"
          :cluster_data="clusters[cluster_id_selected]"
          :properties="properties"
          :association="association"
      />
    </b-collapse>
  </div>
</template>

<script>
    import ClusterTableComponent from "./ClusterTable";
    import ClusterVisualizationComponent from "./ClusterVisualization";

    export default {
        name: "ClusterComponent",
        components: {
            ClusterTableComponent,
            ClusterVisualizationComponent,
        },
        data() {
            return {
                app: this.$root.$children[0],
                properties: [],
                association: '',
                cluster_id_selected: null,
                showData: false,
                clustering_id: null,
                clusters: [],
            }
        },
        props: ['match'],
        computed: {
            hasProperties() {
                return !this.properties.map(res => res[1] !== '').includes(false);
            },
        },
        methods: {
            getClusters(clustering_id) {
                this.clustering_id = clustering_id;

                fetch('/job/' + this.job_id + '/clusters/' + clustering_id + '?association=' + this.association)
                    .then((response) => response.json())
                    .then((data) => {
                        this.clusters = data;
                    });
            },
            getResultForMatch(match_id) {
                let clusterings = [];

                if (this.app.job_data) {
                    this.app.job_data.results.clusterings.forEach(clustering => {
                        if (clustering.alignment === match_id) {
                            clusterings.push(clustering);
                        }
                    });
                }

                return {
                    'clusterings': clusterings,
                }
            },
            createClustering(mapping_id, event) {
                if (event) {
                    let btn = event.target;
                    btn.setAttribute('disabled', 'disabled');
                }
                const clustered = this.getResultForMatch(mapping_id).clusterings.length > 0;

                fetch('/job/' + this.app.job_id + '/create_clustering/',
                    {
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                        },
                        method: "POST",
                        body: JSON.stringify({
                            'alignment': mapping_id,
                            'association_file': clustered ? this.association : '',
                            'clustered': clustered,
                        })
                    })
                    .then((response) => response.json())
                    .then((data) => {
                        if (!clustered && this.association) {
                            this.app.getJobData(() => {
                                this.createClustering(mapping_id);
                            });
                        }
                        else {
                            this.app.getJobData();
                        }
                    });
            },
            resetProperty(idx, property, property_index) {
                let new_property = property.slice(0, property_index);
                new_property.push('');
                if (new_property.length % 2 > 0) {
                    new_property.push('');
                }
                this.$set(this.properties, idx, new_property);
            },
        },
        mounted() {
            const resources = [...this.match.sources];
            this.match.targets.forEach(res => {
                if (!resources.includes(res))
                    resources.push(res)
            });
            this.properties = resources.map(res => [res, '']);
        },
    }
</script>
