<template>
  <b-modal ref="propertyConfig" body-class="bg-light" size="xl" hide-footer static>
    <template v-slot:modal-header="{close}">
      <h5 class="modal-title">Property labels configuration</h5>

      <button class="btn btn-secondary btn-sm ml-auto" @click="saveProperties">
        Save
      </button>

      <button type="button" aria-label="Close" class="close modal-header-close" @click="close()">×</button>
    </template>

    <draggable
        v-for="(entityInfo, entityInfoIdx) in properties" :key="entityInfoIdx"
        v-model="entityInfo.properties" :group="`properties_${entityInfoIdx}`" handle=".handle"
        v-bind:class="{'mt-3': entityInfoIdx > 0}">
      <div v-for="(prop, idx) in entityInfo.properties" :key="entityInfoIdx + '_' + idx"
           class="row align-items-center">
        <div class="col-auto">
          <handle/>
        </div>

        <div class="col-auto p-0">
          <property
              :graphql-endpoint="entityInfo.timbuctoo_graphql"
              :dataset-id="entityInfo.dataset_id"
              :collection-id="entityInfo.collection_id"
              :property="prop"
              :singular="false"
              :allow-delete="idx > 0"
              @clone="entityInfo.properties.splice(idx + 1, 0, [''])"
              @delete="$delete(entityInfo.properties, idx)"/>
        </div>
      </div>
    </draggable>
  </b-modal>
</template>

<script>
    import Draggable from 'vuedraggable';

    export default {
        name: "PropertyConfig",
        components: {
            Draggable
        },
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
