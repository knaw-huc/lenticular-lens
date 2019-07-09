<template>
    <div id="clustering_dataset_linking_stats_cluster_results"
         style="height: 20em; width:100%; scroll: both; overflow: auto;">
        <table class="table table-striped" id="clustering_resultTable"
               style="height: 20em; scroll: both; overflow: auto;">
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
            <cluster-table-row-component
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
    import ClusterTableRowComponent from "./ClusterTableRow";

    export default {
        name: "ClusterTableComponent",
        components: {
            ClusterTableRowComponent,
        },
        props: ['clusters', 'cluster_id_selected'],
        methods: {

        },
        mounted() {

        },
    }
</script>
