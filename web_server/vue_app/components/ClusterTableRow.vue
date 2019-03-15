<template>
    <tr :clusterid="cluster_id" @click="$emit('select:cluster_id', cluster_id)">
        <td :style="'color: ' + ext_colors[ext] + '; font-weight: bold;'"> {{ ext }} </td>
        <td> {{ cluster_id }} </td>
        <td> {{ index }} </td>
        <td> {{ size }} </td>
        <td> {{ properties.join(' | ') }} </td>
        <td> {{ sample }} </td>
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
            cluster_id: String,
            ext: String,
            index: Number,
            size: Number,
            properties: Array,
            sample: String,
        },
    }
</script>
