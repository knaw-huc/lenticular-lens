<template>
  <span v-if="downloadedInfo" class="text-success">Downloaded</span>
  <span v-else-if="downloadingInfo" class="text-info font-italic">
    Downloading {{ downloadingInfo.rows_count }}/{{ downloadingInfo.total }}
  </span>
  <span v-else class="text-danger">Not yet downloaded</span>
</template>

<script>
    export default {
        name: "DownloadProgress",
        props: {
            'datasetId': String,
            'collectionId': String,
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
