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

        <div v-if="lensStatus === 'failed' && lens.status_message" class="row justify-content-center">
          <div class="col-auto text-danger font-italic">
            {{ lens.status_message }}
          </div>
        </div>

        <div v-if="clusteringStatus === 'failed' && clustering.status_message" class="row justify-content-center">
          <div class="col-auto text-danger font-italic">
            {{ clustering.status_message }}
          </div>
        </div>

        <div class="row justify-content-center mt-1">
          <div class="col-auto">
            <div>
              <strong>Links found: </strong>
              {{ lens.links_count ? lens.links_count.toLocaleString('en') : 0 }}
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
            <div v-if="lensStatus === 'waiting'">
              <strong>Request: </strong>
              {{ lens.requested_at | moment("MMMM Do YYYY, hh:mm") }}

              <span class="font-italic">
                (<duration :from="lens.requested_at"/>)
              </span>
            </div>

            <div v-else-if="lensStatus === 'running'">
              <strong>Start: </strong>
              {{ lens.processing_at | moment("MMMM Do YYYY, hh:mm") }}

              <span class="font-italic">
                (<duration :from="lens.processing_at"/>)
              </span>
            </div>

            <div v-else-if="lens && lens.finished_at">
              <strong>Lens duration: </strong>
              <duration :from="lens.processing_at" :until="lens.finished_at"/>
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
    export default {
        name: "Status",
        props: ['lensSpec'],
        computed: {
            lens() {
                return this.$root.lenses.find(lens => lens.spec_id === this.lensSpec.id);
            },

            clustering() {
                return this.$root.clusterings.find(clustering =>
                    clustering.spec_type === 'lens' && clustering.spec_id === this.lensSpec.id);
            },

            lensStatus() {
                return this.lens ? this.lens.status : null;
            },

            clusteringStatus() {
                return this.clustering ? this.clustering.status : null;
            },

            running() {
                return this.lensStatus === 'running' || this.clusteringStatus === 'running';
            },

            failed() {
                return this.lensStatus === 'failed' || this.clusteringStatus === 'failed';
            },

            status() {
                if (['waiting', 'failed'].includes(this.clusteringStatus))
                    return `Clustering ${this.clusteringStatus}`;

                if (this.clusteringStatus === 'running')
                    return this.clustering.status_message;

                if (['waiting', 'failed'].includes(this.lensStatus))
                    return `Lens ${this.lensStatus}`;

                if (this.lensStatus === 'running')
                    return this.lens.status_message;

                return null;
            },
        },
    };
</script>