<template>
  <div v-if="resource">
    <property
        v-for="(prop, idx) in properties"
        :key="idx"
        :resource="resource"
        :property="prop"
        :singular="false"
        :resource-info="false"
        :allow-delete="idx !== 0"
        @clone="properties.splice(idx + 1, 0, [''])"
        @delete="$delete(properties, idx)"/>
  </div>

  <div v-else>
    <property
        v-for="(prop, idx) in properties"
        :key="idx"
        :resource="$root.getResourceById(prop.resource)"
        :property="prop.property"
        :singular="false"
        :allow-delete="properties.findIndex(p => p.resource === prop.resource) !== idx"
        @clone="properties.splice(idx + 1, 0, {resource: properties[idx].resource, property: ['']})"
        @delete="$delete(properties, idx)"/>
  </div>
</template>

<script>
    export default {
        name: "PropertySelection",
        props: {
            properties: Array,
            resource: {
                type: Object,
                default: null,
            },
        },
    }
</script>
