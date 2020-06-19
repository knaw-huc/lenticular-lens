<template>
  <card :id="'validation_' + type + '_' + spec.id" type="validation" :res-id="spec.id" :label="spec.label"
        :has-extra-row="true" :open-card="show" @show="updateShow('open')" @hide="updateShow('close')">
    <template v-slot:columns>
      <div class="col">
        <sub-card :is-first="true" class="small">
          <div class="row justify-content-center">
            <div class="col-auto">
              <div>
                <strong>Links: </strong>
                {{ isLinkset ? linkset.links_count.toLocaleString('en') : lens.links_count.toLocaleString('en') }}

                <span v-if="isLinkset && linkset.links_count > linkset.distinct_links_count"
                      class="font-italic text-info">
                  ({{ linkset.distinct_links_count.toLocaleString('en') }} distinct links)
                </span>
              </div>
              <div v-if="clustering">
                <strong>Clusters: </strong>
                {{ clustering.clusters_count.toLocaleString('en') }}
              </div>
            </div>

            <div v-if="isLinkset" class="col-auto">
              <div>
                <strong>Source entities in linkset: </strong>
                {{ linkset.distinct_linkset_sources_count.toLocaleString('en') }}
              </div>
              <div>
                <strong>Target entities in linkset: </strong>
                {{ linkset.distinct_linkset_targets_count.toLocaleString('en') }}
              </div>
            </div>

            <div v-if="isLinkset" class="col-auto">
              <div>
                <strong>Entities in source: </strong>
                {{ linkset.distinct_sources_count.toLocaleString('en') }}
              </div>
              <div>
                <strong>Entities in target: </strong>
                {{ linkset.distinct_targets_count.toLocaleString('en') }}
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
                    Show {{ type }} specs
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

          <div v-if="showLinks" class="row justify-content-center mt-2">
            <div class="col-auto">
              <div class="btn-toolbar" role="toolbar" aria-label="Toolbar">
                <div class="btn-group btn-group-toggle ml-auto">
                  <label class="btn btn-sm btn-secondary" v-bind:class="{'active': showAcceptedLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showAcceptedLinks"
                           :disabled="loadingTotals" @change="resetLinks()"/>
                    {{ showAcceptedLinks ? 'Hide accepted' : 'Show accepted' }}

                    <span v-if="acceptedLinks !== null" class="badge badge-light ml-1">
                      {{ acceptedLinks.toLocaleString('en') }}
                    </span>
                  </label>

                  <label class="btn btn-sm btn-secondary" v-bind:class="{'active': showRejectedLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showRejectedLinks"
                           :disabled="loadingTotals" @change="resetLinks()"/>
                    {{ showRejectedLinks ? 'Hide rejected' : 'Show rejected' }}

                    <span v-if="rejectedLinks !== null" class="badge badge-light ml-1">
                      {{ rejectedLinks.toLocaleString('en') }}
                    </span>
                  </label>

                  <label class="btn btn-sm btn-secondary" v-bind:class="{'active': showNotValidatedLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showNotValidatedLinks"
                           :disabled="loadingTotals" @change="resetLinks()"/>
                    {{ showNotValidatedLinks ? 'Hide not validated' : 'Show not validated' }}

                    <span v-if="notValidatedLinks !== null" class="badge badge-light ml-1">
                      {{ notValidatedLinks.toLocaleString('en') }}
                    </span>
                  </label>

                  <label v-if="isLens" class="btn btn-sm btn-secondary" v-bind:class="{'active': showMixedLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showMixedLinks"
                           :disabled="loadingTotals" @change="resetLinks()"/>
                    {{ showMixedLinks ? 'Hide mixed' : 'Show mixed' }}

                    <span v-if="mixedLinks !== null" class="badge badge-light ml-1">
                      {{ mixedLinks.toLocaleString('en') }}
                    </span>
                  </label>
                </div>

                <div v-if="resetShownLinks" class="btn-group ml-4" role="group">
                  <button type="button" class="btn btn-sm btn-white border" @click="resetLinks()">
                    <fa-icon icon="sync"/>
                    Reset
                  </button>
                </div>
              </div>
            </div>
          </div>
        </sub-card>

        <spec-info v-if="showInfo" :type="type" :spec="spec"/>

        <sub-card v-if="showPropertySelection" id="properties-card" type="properties" label="Property selection"
                  :has-margin-auto="true" :has-columns="true">
          <template v-slot:columns>
            <div class="col-auto ml-auto">
              <button type="button" class="btn btn-info" @click="saveProperties">
                Save
              </button>
            </div>
          </template>

          <property-selection class="mt-4" :properties="spec.properties"/>
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
        :type="type"
        :spec-id="spec.id"
        :cluster="selectedCluster"
        :association="clustering.association"
        ref="visualization"/>

    <template v-if="showLinks">
      <link-component
          v-for="(link, idx) in links"
          :key="idx"
          :index="idx"
          :link="link"
          @accepted="acceptLink(link)"
          @rejected="rejectLink(link)"/>

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
    import SpecInfo from "../../spec/SpecInfo";

    import Link from "./Link";
    import Cluster from "./Cluster";
    import ClusterVisualization from "./ClusterVisualization";

    export default {
        name: "Validation",
        components: {
            InfiniteLoading,
            Properties,
            PropertySelection,
            SpecInfo,
            LinkComponent: Link,
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

                showAcceptedLinks: false,
                showRejectedLinks: false,
                showNotValidatedLinks: true,
                showMixedLinks: false,
                resetShownLinks: false,

                acceptedLinks: null,
                rejectedLinks: null,
                notValidatedLinks: null,
                mixedLinks: null,

                loadingTotals: false,
                loadingLinks: false,
                loadingClusters: false,

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
            type: String,
            spec: Object,
        },
        computed: {
            hasProperties() {
                return !this.spec.properties.map(res => res.property[0] !== '').includes(false);
            },

            isLinkset() {
                return this.type === 'linkset';
            },

            isLens() {
                return this.type === 'lens';
            },

            linkset() {
                return this.isLinkset
                    ? this.$root.linksets.find(linkset => linkset.spec_id === this.spec.id)
                    : null;
            },

            lens() {
                return this.isLens
                    ? this.$root.lenses.find(lens => lens.spec_id === this.spec.id)
                    : null;
            },

            clustering() {
                const clustering = this.$root.clusterings.find(clustering =>
                    clustering.spec_type === this.type && clustering.spec_id === this.spec.id);
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
                    this.resetLinks();

                if (this.showInfo || this.showPropertySelection || this.showAllLinks || this.showClusters)
                    this.$emit('show');
                else
                    this.$emit('hide');
            },

            selectClusterId(clusterId) {
                this.openClusters = false;
                this.clusterIdSelected = clusterId;
                this.resetLinks();
            },

            showVisualization() {
                this.$refs.visualization.showVisualization();
            },

            async resetLinks(resetClusters = false) {
                await this.getLinkTotals();

                this.links = [];
                this.linksIdentifier += 1;
                this.resetShownLinks = false;

                if (resetClusters) {
                    this.clusters = [];
                    this.clustersIdentifier += 1;
                }
            },

            async saveProperties() {
                await this.$root.submit();
                this.clusterIdSelected = null;
                await this.resetLinks(true);
            },

            async getLinkTotals() {
                if (this.loadingTotals)
                    return;

                this.loadingTotals = true;

                const clusterId = this.showClusterLinks ? this.clusterIdSelected : undefined;
                const totals = await this.$root.getLinksTotals(this.type, this.spec.id, clusterId);

                if (totals) {
                    this.acceptedLinks = totals.accepted || 0;
                    this.rejectedLinks = totals.rejected || 0;
                    this.notValidatedLinks = totals.not_validated || 0;
                    this.mixedLinks = totals.mixed || 0;
                }

                this.loadingTotals = false;
            },

            async getLinks(state) {
                if (this.loadingLinks)
                    return;

                this.loadingLinks = true;

                const clusterId = this.showClusterLinks ? this.clusterIdSelected : undefined;
                const links = await this.$root.getLinks(this.type, this.spec.id,
                    this.showAcceptedLinks, this.showRejectedLinks, this.showNotValidatedLinks, this.showMixedLinks,
                    clusterId, 50, this.links.length);

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

                this.loadingLinks = false;
            },

            async getClusters(state) {
                if (!this.clustering || this.loadingClusters)
                    return;

                this.loadingClusters = true;

                const clusters = await this.$root.getClusters(
                    this.type, this.spec.id, this.clustering.association, 5, this.clusters.length);

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

                this.loadingClusters = false;
            },

            async acceptLink(link) {
                const before = link.valid;
                const after = (before === 'accepted') ? 'not_validated' : 'accepted';

                link.updating = true;
                const result = await this.$root.validateLink(this.type, this.spec.id, link.source, link.target, after);
                link.updating = false;

                if (result !== null) {
                    link.valid = after;

                    if (before === 'accepted')
                        this.acceptedLinks--;
                    else
                        this.acceptedLinks++;

                    if (before === 'not_validated')
                        this.notValidatedLinks--;
                    else if (before === 'accepted')
                        this.notValidatedLinks++;
                    else if (before === 'mixed')
                        this.mixedLinks--;
                    else
                        this.rejectedLinks--;

                    this.resetShownLinks = true;
                }
            },

            async rejectLink(link) {
                const before = link.valid;
                const after = (before === 'rejected') ? 'not_validated' : 'rejected';

                link.updating = true;
                const result = await this.$root.validateLink(this.type, this.spec.id, link.source, link.target, after);
                link.updating = false;

                if (result !== null) {
                    link.valid = after;

                    if (before === 'rejected')
                        this.rejectedLinks--;
                    else
                        this.rejectedLinks++;

                    if (before === 'not_validated')
                        this.notValidatedLinks--;
                    else if (before === 'rejected')
                        this.notValidatedLinks++;
                    else if (before === 'mixed')
                        this.mixedLinks--;
                    else
                        this.acceptedLinks--;

                    this.resetShownLinks = true;
                }
            },
        }
    };
</script>
