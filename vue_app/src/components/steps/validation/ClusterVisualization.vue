<template>
  <b-modal id="visualization" ref="visualization" size="xl" dialog-class="modal-full-size" hide-footer static>
    <template v-slot:modal-header="{close}">
      <h5 class="modal-title">{{ label }}</h5>

      <cluster-visualization-compact-info v-if="show === 'visualize-compact'"/>
      <cluster-visualization-reconciled-info v-else-if="show === 'visualize-reconciled'"/>
      <cluster-visualization-info v-else/>

      <div class="btn-group btn-group-toggle ml-auto">
        <label class="btn btn-sm btn-secondary" v-bind:class="{'active': show === 'visualize'}"
               @click="drawShown('visualize')">
          Cluster
        </label>

        <label class="btn btn-sm btn-secondary" v-bind:class="{'active': show === 'visualize-compact'}"
               @click="drawShown('visualize-compact')">
          Compact
        </label>

        <label v-if="association" class="btn btn-sm btn-secondary"
               v-bind:class="{'active': show === 'visualize-reconciled'}" @click="drawShown('visualize-reconciled')">
          Reconciled
        </label>
      </div>

      <button type="button" aria-label="Close" class="close modal-header-close" @click="close()">×</button>
    </template>

    <div class="plot"></div>
  </b-modal>
</template>

<script>
    import ClusterVisualizationInfo from '../../info/ClusterVisualizationInfo';
    import ClusterVisualizationCompactInfo from '../../info/ClusterVisualizationCompactInfo';
    import ClusterVisualizationReconciledInfo from '../../info/ClusterVisualizationReconciledInfo';

    import {draw} from '../../../utils/visualization';

    export default {
        name: "ClusterVisualization",
        components: {
            ClusterVisualizationInfo,
            ClusterVisualizationCompactInfo,
            ClusterVisualizationReconciledInfo,
        },
        data() {
            return {
                show: null,
                clusterGraph: null,
                clusterGraphCompact: null,
                reconciliationGraph: null,
            };
        },
        props: {
            matchId: Number,
            cluster: Object,
            association: String,
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
            showVisualization(show = null) {
                this.show = show || 'visualize';
                this.$refs.visualization.show();
                this.$refs.visualization.$on('shown', _ => this.drawShown());
            },

            draw(graphParent) {
                draw('.plot', graphParent);
            },

            async getGraphData(type) {
                const data = await this.$root.getClusterGraphs(this.matchId, this.cluster.id,
                    type === 'cluster', this.cluster.extended === 'yes');

                this.clusterGraph = data.cluster_graph;
                this.clusterGraphCompact = data.cluster_graph_compact;
                this.reconciliationGraph = data.reconciliation_graph;

                this.drawShown();
            },

            drawShown(show = null) {
                if (show)
                    this.show = show;

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
        },
    };
</script>

<style scoped>
  .plot {
    width: 100%;
    height: 100%;
  }
</style>