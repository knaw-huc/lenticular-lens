<template>
  <div id="clustering_dataset_linking_stats_cluster_results">
    <table class="table table-striped" id="clustering_resultTable">
      <thead>
      <tr>
        <th>Ext</th>
        <th>Rec</th>
        <th>ID</th>
        <th>count</th>
        <th>size</th>
      </tr>
      </thead>
      <tbody>
      <cluster-table-row
          v-for="(cluster_data, cluster_id) in clusters"
          :key="'clustering_cluster_' + cluster_id"
          :cluster_id="cluster_id"
          :cluster_data="cluster_data"
          :selected="cluster_id_selected === cluster_id"
          @select:cluster_id="$emit('select:cluster_id', $event)"
      />
      </tbody>
    </table>
  </div>
</template>

<script>
    import ClusterTableRow from "./ClusterTableRow";

    export default {
        name: "ClusterTable",
        components: {
            ClusterTableRow,
        },
        props: {
            'clusters': Object,
            'cluster_id_selected': String,
        }
    }
</script>

<style scoped>
  #clustering_dataset_linking_stats_cluster_results {
    height: 20em;
    width: 100%;
    scroll: both;
    overflow: auto;
  }

  #clustering_resultTable {
    height: 20em;
    scroll: both;
    overflow: auto;
  }
</style>