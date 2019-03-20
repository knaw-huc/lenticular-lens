<template>
    <tr :clusterid="cluster_id" @click="$emit('select:cluster_id', cluster_id)">
        <td :style="'color: ' + ext_colors['no'] + '; font-weight: bold;'"> {{ 'no' }} </td>
        <td> {{ cluster_id }} </td>
        <td> {{ cluster_data.index }} </td>
        <td> {{ cluster_data.nodes.length }} </td>
        <td> {{ ['full_name'].join(' | ') }} </td>
        <td> {{ 'name' }} </td>
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
        },
    }
</script>
