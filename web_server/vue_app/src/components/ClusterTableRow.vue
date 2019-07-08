<template>
    <tr :clusterid="cluster_id" @click="$emit('select:cluster_id', cluster_id)" :class="selected ? 'bg-info-light' : ''">
        <td :style="'color: ' + ext_colors[cluster_data.extended] + '; font-weight: bold;'"> {{ cluster_data.extended }} </td>
        <td :style="'color: ' + ext_colors[cluster_data.reconciled] + '; font-weight: bold;'"> {{ cluster_data.reconciled }} </td>
        <td> {{ cluster_id }} </td>
        <td> {{ cluster_data.index }} </td>
        <td> {{ cluster_data.nodes.length }} </td>
    </tr>
</template>

<script>
    export default {
        data() {
            return {
                ext_colors: {
                    'cyc': 'purple',
                    'yes': 'blue',
                    'no': 'red',
                },
            }
        },
        name: "ClusterTableRowComponent",
        props: {
            cluster_data: Object,
            cluster_id: String,
            selected: Boolean,
        },
    }
</script>
