<template>
  <card :id="'clusters_match_' + match.id" type="clusters-matches" :label="match.label"
        :has-extra-row="true" :open-card="show" @show="updateShow('open')" @hide="updateShow('close')">
    <template v-slot:columns>
      <div class="col">
        <sub-card :is-first="true" class="small">
          <div class="row justify-content-center">
            <div class="col-auto">
              <div>
                <strong>Links: </strong>
                {{ alignment.links_count.toLocaleString('en') }}

                <span v-if="alignment.links_count > alignment.distinct_links_count" class="font-italic text-info">
                  ({{ alignment.distinct_links_count.toLocaleString('en') }} distinct links)
                </span>
              </div>
              <div v-if="clustering">
                <strong>Clusters: </strong>
                {{ clustering.clusters_count.toLocaleString('en') }}
              </div>
            </div>

            <div class="col-auto">
              <div>
                <strong>Resources in source: </strong>
                {{ alignment.sources_count.toLocaleString('en') }}

                <span v-if="alignment.sources_count > alignment.distinct_sources_count" class="font-italic text-info">
                  ({{ alignment.distinct_sources_count.toLocaleString('en') }} distinct resources)
                </span>
              </div>
              <div>
                <strong>Resources in target: </strong>
                {{ alignment.targets_count.toLocaleString('en') }}

                <span v-if="alignment.targets_count > alignment.distinct_targets_count" class="font-italic text-info">
                  ({{ alignment.distinct_targets_count.toLocaleString('en') }} distinct resources)
                </span>
              </div>
            </div>

            <div v-if="clustering" class="col-auto">
              <div>
                <strong>Extended: </strong>

                <strong>Yes = </strong>
                {{ clustering.extended_count ? clustering.extended_count.toLocaleString('en') : 0 }}

                <strong>No = </strong>
                {{ (clustering.clusters_count - clustering.extended_count).toLocaleString('en') }}
              </div>
              <div>
                <strong>Cycles: </strong>

                <strong>Yes = </strong>
                {{ clustering.cycles_count ? clustering.cycles_count.toLocaleString('en') : 0 }}

                <strong>No = </strong>
                {{ (clustering.clusters_count - clustering.cycles_count).toLocaleString('en') }}
              </div>
            </div>
          </div>

          <div class="row justify-content-center mt-2">
            <div class="col-auto">
              <div class="btn-toolbar" role="toolbar" aria-label="Toolbar">
                <div class="btn-group btn-group-toggle mr-4">
                  <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showInfo}">
                    <input type="checkbox" autocomplete="off" v-model="showInfo" @change="updateShow"/>
                    <fa-icon icon="info-circle"/>
                    Show alignment specs
                  </label>

                  <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showPropertySelection}">
                    <input type="checkbox" autocomplete="off" v-model="showPropertySelection" @change="updateShow"/>
                    <fa-icon icon="cog"/>
                    Show property config
                  </label>
                </div>

                <div class="btn-group btn-group-toggle">
                  <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showAllLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showAllLinks" @change="updateShow('links')"/>
                    <fa-icon icon="list"/>
                    Overview of all links
                  </label>

                  <label v-if="clustering" class="btn btn-secondary btn-sm" v-bind:class="{'active': showClusters}">
                    <input type="checkbox" autocomplete="off" v-model="showClusters" @change="updateShow('clusters')"/>
                    <fa-icon icon="list"/>
                    Overview of all clusters
                  </label>
                </div>
              </div>
            </div>
          </div>
        </sub-card>

        <alignment-spec v-if="showInfo" :match="match"/>

        <sub-card v-if="showPropertySelection" id="properties-card" type="properties" label="Property selection"
                  :has-margin-auto="true" :has-columns="true">
          <template v-slot:columns>
            <div class="col-auto ml-auto">
              <button type="button" class="btn btn-info" @click="saveProperties">
                Save
              </button>
            </div>
          </template>

          <property-selection class="mt-4" :properties="match.properties"/>
        </sub-card>

        <sub-card v-if="showClusters && clustering" label="Clusters" id="clusters-list" type="clusters-list"
                  :open-card="openClusters" :has-collapse="true"
                  :has-extra-row="!!(!openClusters && clusterIdSelected && showSelectedCluster)"
                  @show="openClusters = true" @hide="openClusters = false">
          <template v-slot:columns>
            <template v-if="clusterIdSelected">
              <div class="col-auto small ml-auto mr-auto">
                <strong>Selected cluster: </strong>
                {{ clusterIdSelected }}
              </div>

              <div class="col-auto">
                <div class="btn-toolbar" role="toolbar" aria-label="Toolbar">
                  <div class="btn-group btn-group-toggle mr-2">
                    <label class="btn btn-sm btn-secondary" v-bind:class="{'active': showSelectedCluster}">
                      <input type="checkbox" autocomplete="off" v-model="showSelectedCluster" @change="updateShow"/>
                      <fa-icon icon="info-circle"/>
                      Show selected cluster spec
                    </label>

                    <label v-if="hasProperties" class="btn btn-sm btn-secondary" @click="showVisualization">
                      <fa-icon icon="project-diagram"/>
                      Visualize
                    </label>
                  </div>
                </div>
              </div>
            </template>
          </template>

          <template v-if="!openClusters && clusterIdSelected && showSelectedCluster" v-slot:row-columns>
            <div class="col">
              <cluster :index="0" :cluster="selectedCluster" :selected="true" :selectable="false"/>
            </div>
          </template>

          <div class="max-overflow mt-4">
            <cluster
                v-for="(cluster, idx) in clusters"
                :key="idx"
                :index="idx"
                :cluster="cluster"
                :selected="clusterIdSelected === cluster.id"
                @select:clusterId="selectClusterId($event)"/>

            <infinite-loading :identifier="clustersIdentifier" @infinite="getClusters">
              <template v-slot:spinner>
                <loading class="mt-4"/>
              </template>

              <template v-slot:no-more>
                No more clusters
              </template>

              <template v-slot:error="{trigger}">
                <div class="text-danger mb-2">
                  Failed to obtain clusters
                </div>
                <button type="button" class="btn btn-sm btn-danger" @click="trigger">Retry</button>
              </template>
            </infinite-loading>
          </div>
        </sub-card>
      </div>
    </template>

    <cluster-visualization
        v-if="showClusters && clustering && clusterIdSelected && hasProperties"
        :matchId="match.id"
        :cluster="selectedCluster"
        :association="clustering.association"
        ref="visualization"/>

    <template v-if="showLinks">
      <match-link
          v-for="(link, idx) in links"
          :key="idx"
          :index="idx"
          :link="link"
          @accepted="acceptLink(link)"
          @declined="declineLink(link)"/>

      <infinite-loading :identifier="linksIdentifier" @infinite="getLinks">
        <template v-slot:spinner>
          <loading class="mt-4"/>
        </template>

        <template v-slot:no-more>
          No more links
        </template>

        <template v-slot:error="{trigger}">
          <div class="text-danger mb-2">
            Failed to obtain links
          </div>
          <button type="button" class="btn btn-sm btn-danger" @click="trigger">Retry</button>
        </template>
      </infinite-loading>
    </template>
  </card>
</template>

<script>
    import InfiniteLoading from 'vue-infinite-loading';

    import Properties from "../../helpers/Properties";
    import PropertySelection from "../../helpers/PropertySelection";
    import AlignmentSpec from "../../helpers/AlignmentSpec";

    import MatchLink from "./MatchLink";
    import Cluster from "./Cluster";
    import ClusterVisualization from "./ClusterVisualization";

    export default {
        name: "MatchValidation",
        components: {
            InfiniteLoading,
            Properties,
            PropertySelection,
            AlignmentSpec,
            MatchLink,
            Cluster,
            ClusterVisualization,
        },
        data() {
            return {
                show: false,
                showInfo: false,
                showPropertySelection: false,
                showSelectedCluster: false,

                showAllLinks: false,
                showClusters: false,

                links: [],
                linksIdentifier: +new Date(),

                clusters: [],
                clustersIdentifier: +new Date(),

                openClusters: true,
                clusterIdSelected: null,
                clusterView: '',
            };
        },
        props: {
            match: Object,
        },
        computed: {
            hasProperties() {
                return !this.match.properties.map(res => res.property[0] !== '').includes(false);
            },

            alignment() {
                return this.$root.alignments.find(alignment => alignment.alignment === this.match.id);
            },

            clustering() {
                const clustering = this.$root.clusterings.find(clustering => clustering.alignment === this.match.id);
                if (clustering && clustering.status === 'done')
                    return clustering;

                return null;
            },

            showLinks() {
                return this.showAllLinks || this.showClusterLinks;
            },

            showClusterLinks() {
                return this.showClusters && this.clusterIdSelected;
            },

            selectedCluster() {
                if (!this.clusterIdSelected)
                    return null;

                return this.clusters.find(cluster => cluster.id === this.clusterIdSelected);
            },
        },
        methods: {
            updateShow(state) {
                const showSomething = this.showInfo || this.showPropertySelection
                    || this.showAllLinks || this.showClusters;

                if (state === 'open' && !showSomething)
                    this.showInfo = true;
                else if (state === 'close' && showSomething) {
                    this.showInfo = false;
                    this.showPropertySelection = false;
                    this.showSelectedCluster = false;

                    this.showAllLinks = false;
                    this.showClusters = false;
                }

                if (this.show !== showSomething)
                    this.show = showSomething;

                if (state === 'links' && this.showClusters) {
                    this.showSelectedCluster = false;
                    this.showClusters = false;
                }
                else if (state === 'clusters' && this.showAllLinks) {
                    this.showSelectedCluster = true;
                    this.showAllLinks = false;
                }

                if (this.showAllLinks || this.showClusters)
                    this.resetLists();
            },

            resetLists() {
                if (this.showClusters && this.clustering && this.clusters.length === 0) {
                    this.links = [];
                    this.linksIdentifier += 1;
                }
                else if ((!this.showClusters || !this.clustering) && this.links.length === 0) {
                    this.clusters = [];
                    this.clustersIdentifier += 1;
                }
            },

            selectClusterId(clusterId) {
                this.clusterIdSelected = clusterId;
                this.openClusters = false;
                this.links = [];
                this.linksIdentifier += 1;
            },

            showVisualization() {
                this.$refs.visualization.showVisualization();
            },

            async saveProperties() {
                await this.$root.submit();
                this.resetLists();
            },

            async getLinks(state) {
                const clusterId = this.showClusterLinks ? this.clusterIdSelected : undefined;
                const links = await this.$root.getAlignment(this.match.id, clusterId, 50, this.links.length);

                if (links !== null)
                    this.links.push(...links);

                if (state) {
                    if (links === null)
                        state.error();
                    else if (links.length > 0)
                        state.loaded();
                    else
                        state.complete();
                }
            },

            async getClusters(state) {
                if (!this.clustering)
                    return;

                const clusters = await this.$root.getClusters(
                    this.match.id, this.clustering.association, 5, this.clusters.length);

                if (clusters !== null)
                    this.clusters.push(...clusters);

                if (state) {
                    if (clusters === null)
                        state.error();
                    else if (clusters.length > 0)
                        state.loaded();
                    else
                        state.complete();
                }
            },

            async acceptLink(link) {
                const accepted = link.valid === true ? null : true;

                link.valid = accepted;
                await this.$root.validateLink(this.match.id, link.source, link.target, accepted);
            },

            async declineLink(link) {
                const declined = link.valid === false ? null : false;

                link.valid = declined;
                await this.$root.validateLink(this.match.id, link.source, link.target, declined);
            },
        }
    };
</script>
