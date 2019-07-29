<template>
  <div>
    <sub-card label="Cluster" :has-collapse="true" :has-info="true" :has-columns="true"
             id="cluster_plot_row_1" type="cluster">
      <template v-slot:info>
        <cluster-visualization-info/>
      </template>

      <template v-slot:columns>
        <div class="col-auto ml-auto">
          <button type="button" v-if="association" @click="getGraphData('cluster')" class="btn btn-info mr-4">
            Load Original Clusters
          </button>

          <a :href="getGraphLink()" target="_blank" class="btn btn-info">
            Open in new tab
          </a>
        </div>
      </template>

      <svg :visible="!Boolean(association)" class="plot mt-3" id="graph_cluster_1"></svg>
    </sub-card>

    <sub-card label="Compact Cluster" :has-collapse="true" :has-info="true" :has-columns="true"
             id="cluster_plot_row_2" type="cluster-compact">
      <template v-slot:info>
        <cluster-visualization-compact-info/>
      </template>

      <template v-slot:columns>
        <div class="col-auto ml-auto">
          <button type="button" v-if="association" @click="getGraphData('cluster')" class="btn btn-info mr-4">
            Load Original Clusters
          </button>

          <a :href="getGraphLink()" target="_blank" class="btn btn-info">
            Open in new tab
          </a>
        </div>
      </template>

      <svg :visible="!Boolean(association)" class="plot mt-3" id="graph_cluster_2"></svg>
    </sub-card>

    <sub-card v-if="association" label="Reconciled" :has-collapse="true" :has-info="true" :has-columns="true"
             id="cluster_plot_row_3" type="cluster-compact">
      <template v-slot:info>
        <cluster-visualization-reconciled-info/>
      </template>

      <template v-slot:columns>
        <div class="col-auto ml-auto">
          <button type="button" v-if="association" @click="getGraphData('cluster')" class="btn btn-info mr-4">
            Load Original Clusters
          </button>

          <a :href="getGraphLink()" target="_blank" class="btn btn-info">
            Open in new tab
          </a>
        </div>
      </template>

      <svg :visible="!Boolean(association)" class="plot mt-3" id="graph_cluster_3"></svg>
    </sub-card>

    <b-modal id="visualization_popup" ref="visualization_popup" title="CLUSTER DETAIL" size="xl" hide-footer
             :return-focus="$root.$children[0].$el" :static="true">
      <svg class="plot" id="graph_cluster_4"></svg>
    </b-modal>
  </div>
</template>

<script>
    import SubCard from "../../structural/SubCard";

    import ClusterVisualizationInfo from '../../info/ClusterVisualizationInfo';
    import ClusterVisualizationCompactInfo from '../../info/ClusterVisualizationCompactInfo';
    import ClusterVisualizationReconciledInfo from '../../info/ClusterVisualizationReconciledInfo';

    import {draw, clear} from '../../../utils/visualization';

    export default {
        name: "ClusterVisualization",
        components: {
            SubCard,
            ClusterVisualizationInfo,
            ClusterVisualizationCompactInfo,
            ClusterVisualizationReconciledInfo,
        },
        props: {
            properties: Array,
            cluster_data: Object,
            cluster_id: String,
            clustering_id: String,
            parent_tab: String,
            association: String,
        },
        methods: {
            getGraphLink() {
                return `/job/${this.$root.job.job_id}/cluster/${this.clustering_id}/${this.cluster_id}`;
            },

            draw(graph_parent, svg_name) {
                draw(this.$refs['visualization_popup'], graph_parent, svg_name, "svg#graph_cluster_4");
            },

            async getGraphData(type) {
                if (this.parent_tab && this.$root.$children[0].$refs['formWizard'].activeTabIndex !== this.$root.$children[0].steps.indexOf(this.parent_tab))
                    return;

                const vm = this;

                clear('graph_cluster_1');
                clear('graph_cluster_2');
                clear('graph_cluster_3');

                const properties = this.properties.map(prop => {
                    const resource = this.$root.getResourceById(prop[0]);
                    return {
                        dataset: resource.dataset_id,
                        entity_type: resource.collection_id,
                        property: prop[1],
                    };
                });

                const data = await this.$root.getClusterGraphs(this.clustering_id, this.cluster_id, {
                    cluster_data: this.cluster_data,
                    properties: properties,
                    get_cluster: !Boolean(this.association) || type === 'cluster',
                    get_reconciliation: this.cluster_data.extended === 'yes',
                    associations: this.cluster_data.extended === 'yes' ? this.association : '',
                });

                if (data.cluster_graph)
                    this.draw(data.cluster_graph, "svg#graph_cluster_1");

                if (data.cluster_graph_compact)
                    this.draw(data.cluster_graph_compact, "svg#graph_cluster_2");

                if (data.reconciliation_graph)
                    this.draw(data.reconciliation_graph, "svg#graph_cluster_3");
            },

            scrollTo(ref) {
                this.$refs[ref].$el.parentNode.scrollIntoView({'behavior': 'smooth', 'block': 'start'});
            },
        },
        mounted() {
            if (this.cluster_id)
                this.getGraphData();
        },
        watch: {
            cluster_id() {
                this.getGraphData();
            },
        },
    }
</script>

<style scoped>
  .plot {
    width: 100%;
    height: 800px;
    background-color: #FFFFE0;
  }

  div.tooltip {
    position: absolute;
    background-color: white;
    max-width: 200px;
    height: auto;
    padding: 1px;
    border-style: solid;
    border-radius: 4px;
    border-width: 1px;
    box-shadow: 3px 3px 10px rgba(0, 0, 0, .5);
    pointer-events: none;
  }

  .links line {
    stroke: #999;
    stroke-opacity: 0.6;
  }

  .nodes circle {
    stroke: #fff;
    stroke-width: 1.5px;
  }

  text {
    font-family: sans-serif;
    font-size: 14px;
  }
</style>