<template>
  <sub-card id="properties-card" type="properties" :label="label" :has-margin-auto="true" :has-columns="true"
            :is-first="isFirst">
    <template v-slot:columns>
      <div class="col-auto ml-auto">
        <button type="button" class="btn btn-info" @click="$emit('save')">
          Save
        </button>
      </div>
    </template>

    <div v-if="resource" class="mt-4">
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

    <div v-else class="mt-4">
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
  </sub-card>
</template>

<script>
    export default {
        name: "PropertySelection",
        props: {
            label: String,
            properties: Array,
            resource: {
                type: Object,
                default: null,
            },
            isFirst: {
                type: Boolean,
                default: false,
            },
        },
    }
</script>
