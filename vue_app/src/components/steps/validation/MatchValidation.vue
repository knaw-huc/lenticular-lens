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
                {{ alignment.links_count }}
              </div>
              <div>
                <strong>Resources in source: </strong>
                {{ alignment.sources_count }}
              </div>
              <div>
                <strong>Resources in target: </strong>
                {{ alignment.targets_count }}
              </div>
            </div>

            <div v-if="clustering" class="col-auto">
              <div>
                <strong>Clusters: </strong>
                <template>
                  {{ clustering.clusters_count }}
                </template>
              </div>
              <div>
                <strong>Extended: </strong>

                <strong>Yes = </strong>
                {{ clustering.extended_count || 0 }}

                <strong>No = </strong>
                {{ clustering.clusters_count - clustering.extended_count }}
              </div>
              <div>
                <strong>Cycles: </strong>

                <strong>Yes = </strong>
                {{ clustering.cycles_count || 0 }}

                <strong>No = </strong>
                {{ clustering.clusters_count - clustering.cycles_count }}
              </div>
            </div>
          </div>

          <div class="row justify-content-center mt-4">
            <div class="col-auto">
              <div class="btn-toolbar" role="toolbar" aria-label="Toolbar">
                <div class="btn-group btn-group-toggle mr-2">
                  <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showInfo}">
                    <input type="checkbox" autocomplete="off" v-model="showInfo" @change="updateShow"/>
                    <fa-icon icon="info-circle"/>
                    Alignment specs
                  </label>

                  <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showPropertySelection}">
                    <input type="checkbox" autocomplete="off" v-model="showPropertySelection" @change="updateShow"/>
                    <fa-icon icon="cog"/>
                    Properties
                  </label>

                  <label class="btn btn-secondary btn-sm" v-bind:class="{'active': showAllLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showAllLinks" @change="updateShow('links')"/>
                    <fa-icon icon="list"/>
                    Links
                  </label>

                  <label v-if="clustering" class="btn btn-secondary btn-sm"
                         v-bind:class="{'active': showClusters}">
                    <input type="checkbox" autocomplete="off" v-model="showClusters" @change="updateShow('clusters')"/>
                    <fa-icon icon="list"/>
                    Clusters
                  </label>
                </div>
              </div>
            </div>
          </div>
        </sub-card>
      </div>
    </template>

    <match-info v-if="showInfo" :match="match"/>

    <sub-card v-if="showPropertySelection" :id="'properties_card_' + match.id" type="properties"
              label="Property selection" :has-margin-auto="true" :has-columns="true">
      <template v-slot:columns>
        <div class="col-auto ml-auto">
          <button type="button" class="btn btn-info" @click="saveProperties">
            Save
          </button>
        </div>
      </template>

      <div class="mt-4">
        <property
            v-for="(property, idx) in match.properties"
            v-if="property[0]"
            class="mx-0"
            :key="idx"
            :property="property"
            :singular="false"
            :allow-delete="match.properties.findIndex(p => p[0] === property[0]) !== idx"
            @clone="match.properties.splice(idx + 1, 0, [match.properties[idx][0], ''])"
            @delete="$delete(match.properties, idx)"
            @resetProperty="resetProperty(idx, property, $event)"/>
      </div>
    </sub-card>

    <loading v-if="loading" class="mt-4"/>

    <template v-if="!loading && showClusters && clustering">
      <sub-card label="Clusters" :open-card="true" :has-collapse="true" :has-margin-auto="!!clusterIdSelected"
                id="clusters-list" type="clusters-list">
        <template v-slot:columns>
          <template v-if="clusterIdSelected">
            <div class="col-auto small ml-auto mr-auto">
              <strong>Selected cluster: </strong>
              {{ clusterIdSelected }}
            </div>

            <div class="col-auto">
              <div class="btn-group btn-group-toggle">
                <label class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': clusterView === 'links'}">
                  <input type="radio" v-model="clusterView" value="links" autocomplete="off"/>
                  <fa-icon icon="align-justify"/>
                  Show links
                </label>

                <label v-if="hasProperties" class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': clusterView === 'visualize'}">
                  <input type="radio" v-model="clusterView" value="visualize" autocomplete="off"/>
                  <fa-icon icon="project-diagram"/>
                  Visualize
                </label>

                <label v-if="hasProperties" class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': clusterView === 'visualize-compact'}">
                  <input type="radio" v-model="clusterView" value="visualize-compact" autocomplete="off"/>
                  <fa-icon icon="project-diagram"/>
                  Visualize compact
                </label>

                <label v-if="hasProperties && clustering.association" class="btn btn-sm btn-secondary"
                       v-bind:class="{'active': clusterView === 'visualize-reconciled'}">
                  <input type="radio" v-model="clusterView" value="visualize-reconciled" autocomplete="off"/>
                  <fa-icon icon="project-diagram"/>
                  Visualize reconciled
                </label>
              </div>
            </div>
          </template>
        </template>

        <div class="bg-white px-3 py-1 mt-4 mb-2">
          <div class="row font-weight-bold">
            <div class="col">Id</div>
            <div class="col">Extended</div>
            <div class="col">Reconciled</div>
            <div class="col">Size</div>
            <div class="col">Links</div>
            <div class="col-4">Property</div>
          </div>
        </div>

        <virtual-list
            :size="58"
            :remain="5"
            :item="clusterItem"
            :itemcount="clustering.clusters_count"
            :itemprops="getClusterItemProps"/>
      </sub-card>

      <cluster-visualization
          v-if="!loading && showClusters && clusterIdSelected && hasProperties && clusterView.startsWith('visualize')"
          :show="clusterView"
          :clustering-id="clustering.clustering_id"
          :cluster-id="clusterIdSelected"
          :cluster-data="clusters[clusterIdSelected]"
          :properties="match.properties"
          :association="clustering.association"/>
    </template>

    <virtual-list
        v-if="!loading && showLinks"
        class="mt-4"
        :size="130"
        :remain="5"
        :item="linkItem"
        :pagemode="true"
        :itemcount="showAllLinks ? links.length : clusterLinks.length"
        :itemprops="getLinkItemProps"/>
  </card>
</template>

<script>
    import VirtualList from 'vue-virtual-scroll-list';

    import MatchInfo from "../../helpers/MatchInfo";
    import Properties from "../../helpers/Properties";

    import MatchLink from "./MatchLink";
    import Clustering from "./Clustering";
    import ClusterVisualization from "./ClusterVisualization";

    export default {
        name: "MatchValidation",
        components: {
            VirtualList,
            MatchInfo,
            Properties,
            MatchLink,
            Clustering,
            ClusterVisualization,
        },
        data() {
            return {
                show: false,
                showInfo: false,
                showPropertySelection: false,
                showAllLinks: false,
                showClusters: false,
                loading: false,
                links: [],
                linkItem: MatchLink,
                clusters: {},
                clusterItem: Clustering,
                clusterIdSelected: null,
                clusterView: '',
                properties: {},
                linkStates: {},
            };
        },
        props: {
            match: Object,
        },
        computed: {
            clusterIds() {
                return Object.keys(this.clusters);
            },

            hasProperties() {
                return !this.match.properties.map(res => res[1] !== '').includes(false);
            },

            alignment() {
                return this.$root.alignments.find(alignment => alignment.alignment === this.match.id);
            },

            clustering() {
                const clustering = this.$root.clusterings.find(clustering => clustering.alignment === this.match.id);
                if (clustering && clustering.status === 'Finished')
                    return clustering;

                return null;
            },

            showLinks() {
                return this.showAllLinks || this.showClusterLinks;
            },

            showClusterLinks() {
                return this.showClusters && this.clusterIdSelected && (this.clusterView === 'links');
            },

            selectedCluster() {
                if (!this.clusterIdSelected)
                    return null;

                return this.clusters[this.clusterIdSelected];
            },

            clusterLinks() {
                if (!this.selectedCluster)
                    return [];

                return this.selectedCluster.links.map(link => {
                    const source = link[0].substring(1, link[0].length - 1);
                    const target = link[1].substring(1, link[1].length - 1);

                    const hash = this.getLinkHash(source, target);
                    const strength = this.selectedCluster.strengths.hasOwnProperty(hash)
                        ? this.selectedCluster.strengths[hash][0] : '0';

                    return [source, target, strength];
                });
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
                    this.showAllLinks = false;
                    this.showClusters = false;
                }

                if (this.show !== showSomething)
                    this.show = showSomething;

                if (state === 'links' && this.showClusters)
                    this.showClusters = false;
                else if (state === 'clusters' && this.showAllLinks)
                    this.showAllLinks = false;

                if (this.showAllLinks || this.showClusters)
                    this.getLinksOrClusters();
            },

            async saveProperties() {
                await this.$root.submit();
                await this.getLinksOrClusters(true);
            },

            async getLinksOrClusters(hard = false) {
                if (this.loading)
                    return;

                if (this.showClusters && this.clustering && (Object.keys(this.clusters).length === 0)) {
                    this.loading = true;
                    this.links = [];
                    await this.getClusters();
                }
                else if ((!this.showClusters || !this.clustering) && (this.links.length === 0)) {
                    this.loading = true;
                    this.clusters = {};
                    await this.getLinks();
                }

                if (this.hasProperties && (hard || (Object.keys(this.properties).length === 0))) {
                    this.loading = true;

                    const targets = this.$root.getTargetsForMatch(this.match.id);
                    this.properties = await this.$root.getPropertiesForAlignment(this.match.id, targets);
                }

                this.loading = false;
            },

            async getLinks() {
                this.links = await this.$root.getAlignment(this.match.id);
            },

            async getClusters() {
                if (this.clustering)
                    this.clusters = await this.$root.getClusters(
                        this.clustering.clustering_id, this.clustering.association);
            },

            getClusterItemProps(idx) {
                const clusterId = this.clusterIds[idx];
                return {
                    props: {
                        clusterId: clusterId,
                        clusterData: this.clusters[clusterId],
                        properties: this.properties,
                        selected: this.clusterIdSelected === clusterId,
                        isFirst: idx === 0,
                    },
                    on: {
                        'select:clusterId': clusterId => this.clusterIdSelected = clusterId,
                    }
                };
            },

            getLinkItemProps(idx) {
                const link = this.showAllLinks ? this.links[idx] : this.clusterLinks[idx];
                return {
                    props: {
                        index: idx,
                        state: this.linkStates[this.getLinkHash(link[0], link[1])],
                        source: link[0],
                        sourceValues: this.properties[link[0]] || [],
                        target: link[1],
                        targetValues: this.properties[link[1]] || [],
                        strength: parseFloat(link[2]).toFixed(3),
                        isFirst: (idx === 0),
                    },
                    on: {
                        accepted: () => this.acceptLink(link[0], link[1]),
                        declined: () => this.declineLink(link[0], link[1]),
                    },
                };
            },

            getLinkHash(source, target) {
                const obj = (source < target) ? `('<${source}>', '<${target}>')` : `('<${target}>', '<${source}>')`;
                const hash = this.$utilities.md5(obj).substring(0, 15);

                return `key_H${hash}`;
            },

            acceptLink(source, target) {
                this.$set(this.linkStates, this.getLinkHash(source, target), 'accepted');
            },

            declineLink(source, target) {
                this.$set(this.linkStates, this.getLinkHash(source, target), 'declined');
            },

            resetProperty(idx, property, propertyIndex) {
                const newProperty = property.slice(0, propertyIndex);
                newProperty.push('');

                if (newProperty.length % 2 > 0)
                    newProperty.push('');

                this.$set(this.match.properties, idx, newProperty);
            },
        }
    };
</script>
