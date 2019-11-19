<template>
  <sub-card :is-first="true" class="small">
    <div class="row align-items-center justify-content-center">
      <div v-if="running" class="col-auto">
        <loading :small="true"/>
      </div>

      <div v-if="failed" class="col-auto">
        <failed size="3x"/>
      </div>

      <div class="col-auto">
        <div v-if="status" class="row justify-content-center">
          <div class="col-auto">
            <strong>Status: </strong>
            {{ status }}
          </div>
        </div>

        <div v-if="alignmentStatus === 'failed' && alignment.status_message" class="row justify-content-center">
          <div class="col-auto text-danger font-italic">
            {{ alignment.status_message }}
          </div>
        </div>

        <div v-if="clusteringStatus === 'failed' && clustering.status_message" class="row justify-content-center">
          <div class="col-auto text-danger font-italic">
            {{ clustering.status_message }}
          </div>
        </div>

        <div v-if="alignmentStatus === 'downloading' && downloads.length > 0" class="row justify-content-center">
          <div class="col-auto clearfix">
            <ul class="font-italic text-info inline-list px-0">
              <li v-for="download in downloads">
                {{ download.collection_id }}:
                <download-progress :dataset-id="download.dataset_id" :collection-id="download.collection_id"/>
              </li>
            </ul>
          </div>
        </div>

        <div class="row justify-content-center mt-1">
          <div class="col-auto">
            <div>
              <strong>Links found: </strong>
              {{ alignment.links_count ? alignment.links_count.toLocaleString('en') : 0 }}

              <span
                  v-if="alignment.links_count && alignment.distinct_links_count && alignment.links_count > alignment.distinct_links_count"
                  class="font-italic text-info">
                ({{ alignment.distinct_links_count.toLocaleString('en') }} distinct links)
              </span>
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
              <strong>Resources in source: </strong>
              {{ alignment.sources_count ? alignment.sources_count.toLocaleString('en') : 0 }}

              <span
                  v-if="alignment.sources_count && alignment.distinct_sources_count && alignment.sources_count > alignment.distinct_sources_count"
                  class="font-italic text-info">
                  ({{ alignment.distinct_sources_count.toLocaleString('en') }} distinct resources)
              </span>
            </div>

            <div>
              <strong>Resources in target: </strong>
              {{ alignment.targets_count ? alignment.targets_count.toLocaleString('en') : 0 }}

              <span
                  v-if="alignment.targets_count && alignment.distinct_targets_count && alignment.targets_count > alignment.distinct_targets_count"
                  class="font-italic text-info">
                  ({{ alignment.distinct_targets_count.toLocaleString('en') }} distinct resources)
              </span>
            </div>
          </div>

          <div class="col-auto">
            <div v-if="alignmentStatus === 'waiting'">
              <strong>Request: </strong>
              {{ alignment.requested_at | moment("MMMM Do YYYY, hh:mm") }}

              <span class="font-italic">
                (<duration :from="alignment.requested_at"/>)
              </span>
            </div>

            <div v-else-if="alignmentStatus === 'downloading' || alignmentStatus === 'running'">
              <strong>Start: </strong>
              {{ alignment.processing_at | moment("MMMM Do YYYY, hh:mm") }}

              <span class="font-italic">
                (<duration :from="alignment.processing_at"/>)
              </span>
            </div>

            <div v-else-if="alignment && alignment.finished_at">
              <strong>Matching duration: </strong>
              <duration :from="alignment.processing_at" :until="alignment.finished_at"/>
            </div>

            <div v-if="clusteringStatus === 'waiting'">
              <strong>Request clustering: </strong>
              {{ clustering.requested_at | moment("MMMM Do YYYY, hh:mm") }}

              <span class="font-italic">
                (<duration :from="clustering.requested_at"/>)
              </span>
            </div>

            <div v-else-if="clusteringStatus === 'running'">
              <strong>Start clustering: </strong>
              {{ clustering.processing_at | moment("MMMM Do YYYY, hh:mm") }}

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
    import {EventBus} from '../../../eventbus.js';

    export default {
        name: "MatchStatus",
        props: ['match'],
        data() {
            return {
                refreshDownloadsInProgress: false,
            };
        },
        computed: {
            alignment() {
                return this.$root.alignments.find(alignment => alignment.alignment === this.match.id);
            },

            clustering() {
                return this.$root.clusterings.find(clustering => clustering.alignment === this.match.id);
            },

            alignmentStatus() {
                return this.alignment ? this.alignment.status : null;
            },

            clusteringStatus() {
                return this.clustering ? this.clustering.status : null;
            },

            running() {
                return this.alignmentStatus === 'downloading' ||
                    this.alignmentStatus === 'running' ||
                    this.clusteringStatus === 'running';
            },

            failed() {
                return this.alignmentStatus === 'failed' || this.clusteringStatus === 'failed';
            },

            status() {
                if (['waiting', 'failed'].includes(this.clusteringStatus))
                    return `Clustering ${this.clusteringStatus}`;

                if (this.clusteringStatus === 'running')
                    return this.clustering.status_message;

                if (['waiting', 'downloading', 'failed'].includes(this.alignmentStatus))
                    return `Alignment ${this.alignmentStatus}`;

                if (this.alignmentStatus === 'running')
                    return this.alignment.status_message;

                return null;
            },

            downloads() {
                if (this.alignmentStatus !== 'downloading')
                    return [];

                if (!this.refreshDownloadsInProgress) {
                    this.refreshDownloadsInProgress = true;
                    EventBus.$emit('refreshDownloadsInProgress');
                }

                const datasets = [];
                [...this.match.sources, ...this.match.targets].forEach(resourceId => {
                    const resource = this.$root.getResourceById(resourceId);
                    const datasetId = resource.dataset.dataset_id;
                    if (!datasets.includes(datasetId))
                        datasets.push(datasetId);
                });

                return this.$root.downloading.filter(collection => datasets.includes(collection.dataset_id));
            },
        },
    };
</script>