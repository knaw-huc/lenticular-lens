<template>
  <b-modal ref="propertyConfig" body-class="bg-light" size="xl" hide-footer static>
    <template v-slot:modal-header="{close}">
      <h5 class="modal-title">Property labels configuration</h5>

      <button class="btn btn-secondary btn-sm ml-auto" @click="saveProperties">
        Save
      </button>

      <button type="button" aria-label="Close" class="close modal-header-close" @click="close()">×</button>
    </template>

    <template v-for="(entityInfo, entityInfoIdx) in properties">
      <property
          v-for="(prop, idx) in entityInfo.properties"
          :key="entityInfoIdx + '_' + idx"
          :graphql-endpoint="entityInfo.timbuctoo_graphql"
          :dataset-id="entityInfo.dataset_id"
          :collection-id="entityInfo.collection_id"
          :property="prop"
          :singular="false"
          :allow-delete="idx > 0"
          @clone="entityInfo.properties.splice(idx + 1, 0, [''])"
          @delete="$delete(entityInfo.properties, idx)"/>
    </template>
  </b-modal>
</template>

<script>
    export default {
        name: "PropertyConfig",
        props: {
            properties: Array,
        },
        methods: {
            show() {
                this.$refs.propertyConfig.show();
            },

            async saveProperties() {
                await this.$root.submit();
                this.$emit('save');
            }
        },
    };
</script>
