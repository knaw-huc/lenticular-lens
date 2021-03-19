<template>
  <property :graphql-endpoint="entityTypeSelection.dataset.timbuctoo_graphql"
            :dataset-id="entityTypeSelection.dataset.dataset_id"
            :collection-id="entityTypeSelection.dataset.collection_id"
            :property="property"
            :read-only="readOnly"
            :small="small"
            :singular="singular"
            :allow-delete="allowDelete"
            :show-info="showInfo"
            @clone="$emit('clone')"
            @delete="$emit('delete')"
            ref="property"/>
</template>

<script>
    export default {
        name: "EtsProperty",
        props: {
            entityTypeSelection: Object,
            property: Array,
            readOnly: {
                type: Boolean,
                default: false,
            },
            small: {
                type: Boolean,
                default: false,
            },
            singular: {
                type: Boolean,
                default: false,
            },
            allowDelete: {
                type: Boolean,
                default: true,
            },
            showInfo: {
                type: Boolean,
                default: true,
            }
        },
        methods: {
            validateProperty() {
                return this.$refs.property.validateProperty();
            },
        }
    };
</script>
