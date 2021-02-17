<template>
  <sub-card :is-first="true" class="small">
    <div class="row align-items-center justify-content-center">
      <div v-if="running" class="col-auto">
        <loading :small="true"/>
      </div>

      <div v-if="failed" class="col-auto">
        <div class="d-flex justify-content-center text-danger">
          <fa-icon icon="times" size="3x"/>
        </div>
      </div>

      <div class="col-auto">
        <div v-if="status" class="row justify-content-center">
          <div class="col-auto">
            <strong>Status: </strong>
            {{ status }}
          </div>
        </div>

        <div v-if="linksetStatus === 'failed' && linkset.status_message" class="row justify-content-center">
          <div class="col-auto text-danger font-italic">
            {{ linkset.status_message }}
          </div>
        </div>

        <div v-if="clusteringStatus === 'failed' && clustering.status_message" class="row justify-content-center">
          <div class="col-auto text-danger font-italic">
            {{ clustering.status_message }}
          </div>
        </div>

        <div v-if="linksetStatus === 'downloading' && downloads.length > 0" class="row justify-content-center">
          <div class="col-auto clearfix">
            <ul class="font-italic text-secondary inline-list px-0">
              <li v-for="download in downloads">
                {{ download.collection_id }}:
                <download-progress :dataset-id="download.dataset_id" :collection-id="download.collection_id"/>
              </li>
            </ul>
          </div>
        </div>

        <div class="row justify-content-center mt-1">
          <div class="col-auto">
            <div v-if="linksetStatus === 'running' && linksetSpec.use_counter">
              <strong>Links found: </strong>
              {{ linkset.links_count ? linkset.links_count.toLocaleString('en') : 0 }}
            </div>

            <div v-if="linkset.distinct_links_count">
              <strong>Links found: </strong>
              {{ linkset.distinct_links_count.toLocaleString('en') }}
            </div>

            <div v-if="clustering && clusteringStatus === 'running'">
              <strong>Clusters found / Links processed: </strong>
              {{ clustering.clusters_count ? clustering.clusters_count.toLocaleString('en') : 0 }} /
              {{ clustering.links_count ? clustering.links_count.toLocaleString('en') : 0 }}
            </div>

            <div v-else-if="clustering">
              <strong>Clusters found: </strong>
              {{ clustering.clusters_count ? clustering.clusters_count.toLocaleString('en') : 0 }}
            </div>
          </div>

          <div class="col-auto">
            <div>
              <strong>Source entities in linkset: </strong>
              {{
                linkset.distinct_linkset_sources_count ? linkset.distinct_linkset_sources_count.toLocaleString('en') : 0
              }}
            </div>

            <div>
              <strong>Target entities in linkset: </strong>
              {{
                linkset.distinct_linkset_targets_count ? linkset.distinct_linkset_targets_count.toLocaleString('en') : 0
              }}
            </div>
          </div>

          <div class="col-auto">
            <div>
              <strong>Entities in source: </strong>
              {{ linkset.distinct_sources_count ? linkset.distinct_sources_count.toLocaleString('en') : 0 }}
            </div>

            <div>
              <strong>Entities in target: </strong>
              {{ linkset.distinct_targets_count ? linkset.distinct_targets_count.toLocaleString('en') : 0 }}
            </div>
          </div>

          <div class="col-auto">
            <div v-if="linksetStatus === 'waiting'">
              <strong>Request: </strong>
              {{ linkset.requested_at | moment("MMMM Do YYYY, HH:mm") }}

              <span class="font-italic">
                (<duration :from="linkset.requested_at"/>)
              </span>
            </div>

            <div v-else-if="linksetStatus === 'downloading' || linksetStatus === 'running'">
              <strong>Start: </strong>
              {{ linkset.processing_at | moment("MMMM Do YYYY, HH:mm") }}

              <span class="font-italic">
                (<duration :from="linkset.processing_at"/>)
              </span>
            </div>

            <div v-else-if="linkset && linkset.finished_at">
              <strong>Matching duration: </strong>
              <duration :from="linkset.processing_at" :until="linkset.finished_at"/>
            </div>

            <div v-if="clusteringStatus === 'waiting'">
              <strong>Request clustering: </strong>
              {{ clustering.requested_at | moment("MMMM Do YYYY, HH:mm") }}

              <span class="font-italic">
                (<duration :from="clustering.requested_at"/>)
              </span>
            </div>

            <div v-else-if="clusteringStatus === 'running'">
              <strong>Start clustering: </strong>
              {{ clustering.processing_at | moment("MMMM Do YYYY, HH:mm") }}

              <span class="font-italic">
                (<duration :from="clustering.processing_at"/>)
              </span>
            </div>

            <div v-else-if="clustering && clustering.finished_at">
              <strong>Clustering duration: </strong>
              <duration :from="clustering.processing_at" :until="clustering.finished_at"/>
            </div>
          </div>
        </div>
      </div>
    </div>
  </sub-card>
</template>

<script>
    import {EventBus} from "@/eventbus";

    export default {
        name: "Status",
        props: ['linksetSpec'],
        data() {
            return {
                refreshDownloadsInProgress: false,
            };
        },
        computed: {
            linkset() {
                return this.$root.linksets.find(linkset => linkset.spec_id === this.linksetSpec.id);
            },

            clustering() {
                return this.$root.clusterings.find(clustering =>
                    clustering.spec_type === 'linkset' && clustering.spec_id === this.linksetSpec.id);
            },

            linksetStatus() {
                return this.linkset ? this.linkset.status : null;
            },

            clusteringStatus() {
                return this.clustering ? this.clustering.status : null;
            },

            running() {
                return this.linksetStatus === 'downloading'
                    || this.linksetStatus === 'running'
                    || this.clusteringStatus === 'running';
            },

            failed() {
                return this.linksetStatus === 'failed' || this.clusteringStatus === 'failed';
            },

            status() {
                if (['waiting', 'failed'].includes(this.clusteringStatus))
                    return `Clustering ${this.clusteringStatus}`;

                if (this.clusteringStatus === 'running')
                    return this.clustering.status_message;

                if (['waiting', 'downloading', 'failed'].includes(this.linksetStatus))
                    return `Matching ${this.linksetStatus}`;

                if (this.linksetStatus === 'running')
                    return this.linkset.status_message;

                return null;
            },

            downloads() {
                if (this.linksetStatus !== 'downloading')
                    return [];

                if (!this.refreshDownloadsInProgress) {
                    this.refreshDownloadsInProgress = true;
                    EventBus.$emit('refreshDownloadsInProgress');
                }

                const datasets = [];
                [...this.linksetSpec.sources, ...this.linksetSpec.targets].forEach(entityTypeSelectionId => {
                    const entityTypeSelection = this.$root.getEntityTypeSelectionById(entityTypeSelectionId);
                    const datasetId = entityTypeSelection.dataset.dataset_id;
                    if (!datasets.includes(datasetId))
                        datasets.push(datasetId);
                });

                return this.$root.downloading.filter(collection => datasets.includes(collection.dataset_id));
            },
        },
    };
</script>