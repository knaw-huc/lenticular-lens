<template>
  <div v-if="entityTypeSelection">
    <property
        v-for="(prop, idx) in properties"
        :key="idx"
        :entity-type-selection="entityTypeSelection"
        :property="prop"
        :singular="false"
        :entity-type-selection-info="false"
        :allow-delete="idx !== 0"
        @clone="properties.splice(idx + 1, 0, [''])"
        @delete="$delete(properties, idx)"/>
  </div>

  <div v-else>
    <property
        v-for="(prop, idx) in properties"
        :key="idx"
        :entity-type-selection="$root.getEntityTypeSelectionById(prop.entity_type_selection)"
        :property="prop.property"
        :singular="false"
        :allow-delete="properties.findIndex(p => p.entity_type_selection === prop.entity_type_selection) !== idx"
        @clone="properties.splice(idx + 1, 0, {entity_type_selection: properties[idx].entity_type_selection, property: ['']})"
        @delete="$delete(properties, idx)"/>
  </div>
</template>

<script>
    export default {
        name: "PropertySelection",
        props: {
            properties: Array,
            entityTypeSelection: {
                type: Object,
                default: null,
            },
        },
    }
</script>
