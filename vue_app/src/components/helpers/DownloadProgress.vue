<template>
  <span v-if="small && downloadingInfo" class="smaller font-italic">
    {{ downloadingInfo.rows_count }}/{{ downloadingInfo.total }}
  </span>

  <span v-else-if="small && !downloadingInfo && !downloadedInfo" class="text-warning">
    <fa-icon icon="times" size="sm"/>
  </span>

  <span v-else-if="!small && downloadedInfo" class="text-success">
    Downloaded
  </span>

  <span v-else-if="!small && downloadingInfo" class="text-info font-italic">
    Downloading {{ downloadingInfo.rows_count }}/{{ downloadingInfo.total }}
  </span>

  <span v-else-if="!small" class="text-danger">
    Not yet downloaded
  </span>
</template>

<script>
    export default {
        name: "DownloadProgress",
        props: {
            'datasetId': String,
            'collectionId': String,
            'small': {
                type: Boolean,
                default: false
            },
        },
        computed: {
            downloadedInfo() {
                return this.$root.downloaded.find(collection =>
                    collection.dataset_id === this.datasetId && collection.collection_id === this.collectionId);
            },

            downloadingInfo() {
                return this.$root.downloading.find(collection =>
                    collection.dataset_id === this.datasetId && collection.collection_id === this.collectionId);
            },
        },
    };
</script>
