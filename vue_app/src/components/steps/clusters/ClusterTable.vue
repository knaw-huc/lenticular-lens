<template>
  <div class="clustering_result bg-white border mt-4">
    <table class="table table-striped">
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

<style>
  .clustering_result {
    height: 20em;
  }

  .clustering_result table {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .clustering_result table thead {
    margin-right: 15px;
  }

  .clustering_result table tbody {
    overflow-y: scroll;
  }

  .clustering_result table tr {
    width: 100%;
    display: flex;
  }

  .clustering_result table th {
    display: flex;
    flex: 1;
    align-items: center;
  }

  .clustering_result table th,
  .clustering_result table td {
    border: none;
  }
</style>