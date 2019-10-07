<template>
  <sub-card :label="label" :has-info="true" :has-columns="true">
    <template v-slot:info>
      <cluster-visualization-compact-info v-if="show === 'visualize-compact'"/>
      <cluster-visualization-reconciled-info v-else-if="show === 'visualize-reconciled'"/>
      <cluster-visualization-info v-else/>
    </template>

<!--    <template v-slot:columns>-->
<!--      <div class="col-auto ml-auto">-->
<!--        <button type="button" v-if="association" @click="getGraphData('cluster')" class="btn btn-info mr-4">-->
<!--          Load Original Clusters-->
<!--        </button>-->
<!--      </div>-->
<!--    </template>-->

    <svg class="plot mt-3" id="graph-cluster"></svg> <!-- :visible="!Boolean(association)" -->

    <b-modal id="visualization_popup" ref="visualizationPopup" title="CLUSTER DETAIL" size="xl" hide-footer
             :return-focus="$root.$children[0].$el" :static="true">
      <svg class="plot" id="graph-cluster-popup"></svg>
    </b-modal>
  </sub-card>
</template>

<script>
    import ClusterVisualizationInfo from '../../info/ClusterVisualizationInfo';
    import ClusterVisualizationCompactInfo from '../../info/ClusterVisualizationCompactInfo';
    import ClusterVisualizationReconciledInfo from '../../info/ClusterVisualizationReconciledInfo';

    import {draw, clear} from '../../../utils/visualization';

    export default {
        name: "ClusterVisualization",
        components: {
            ClusterVisualizationInfo,
            ClusterVisualizationCompactInfo,
            ClusterVisualizationReconciledInfo,
        },
        data() {
            return {
                clusterGraph: null,
                clusterGraphCompact: null,
                reconciliationGraph: null,
            };
        },
        props: {
            show: String,
            matchId: Number,
            cluster: Object,
        },
        computed: {
            label() {
                switch (this.show) {
                    case 'visualize-compact':
                        return 'Visualization of Compact Cluster';
                    case 'visualize-reconciled':
                        return 'Visualization of Reconciled Cluster';
                    case 'visualize':
                    default:
                        return 'Visualization of Cluster';
                }
            },
        },
        methods: {
            draw(graphParent) {
                clear('svg#graph-cluster');
                draw(this.$refs.visualizationPopup, graphParent, 'svg#graph-cluster', 'svg#graph-cluster-popup');
            },

            async getGraphData(type) {
                clear('svg#graph-cluster');

                const data = await this.$root.getClusterGraphs(this.matchId, this.cluster.id,
                    type === 'cluster', this.cluster.extended === 'yes');

                this.clusterGraph = data.cluster_graph;
                this.clusterGraphCompact = data.cluster_graph_compact;
                this.reconciliationGraph = data.reconciliation_graph;

                this.drawShown();
            },

            drawShown() {
                switch (this.show) {
                    case 'visualize-compact':
                        if (this.clusterGraphCompact) this.draw(this.clusterGraphCompact);
                        break;
                    case 'visualize-reconciled':
                        if (this.reconciliationGraph) this.draw(this.reconciliationGraphDrawn);
                        break;
                    case 'visualize':
                    default:
                        if (this.clusterGraph) this.draw(this.clusterGraph);
                }
            },
        },
        mounted() {
            if (this.cluster)
                this.getGraphData();
        },
        watch: {
            cluster() {
                this.getGraphData();
            },

            show() {
                this.drawShown();
            },
        },
    };
</script>

<style scoped>
  .plot {
    width: 100%;
    height: 750px;
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