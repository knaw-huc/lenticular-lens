<template>
  <card :id="'validation_' + type + '_' + spec.id" type="validation" :res-id="spec.id" :res-type="type"
        :label="spec.label" :has-extra-row="true" @show="onToggle(true)" @hide="onToggle(false)">
    <template v-slot:columns>
      <div class="col">
        <sub-card :is-first="true" class="small">
          <div class="row justify-content-center">
            <div class="col-auto">
              <div>
                <strong>Links: </strong>
                {{ isLinkset ? linkset.links_count.toLocaleString('en') : lens.links_count.toLocaleString('en') }}
              </div>
              <div v-if="clustering">
                <strong>Clusters: </strong>
                {{ clustering.clusters_count.toLocaleString('en') }}
              </div>
            </div>

            <div v-if="isLinkset" class="col-auto">
              <div>
                <strong>Source / target / total entities in linkset: </strong>
                {{ linkset.linkset_sources_count ? linkset.linkset_sources_count.toLocaleString('en') : 0 }} /
                {{ linkset.linkset_targets_count ? linkset.linkset_targets_count.toLocaleString('en') : 0 }} /
                {{ linkset.linkset_entities_count ? linkset.linkset_entities_count.toLocaleString('en') : 0 }}
              </div>

              <div>
                <strong>Entities in source / target / total: </strong>
                {{ linkset.sources_count ? linkset.sources_count.toLocaleString('en') : 0 }} /
                {{ linkset.targets_count ? linkset.targets_count.toLocaleString('en') : 0 }} /
                {{ linkset.entities_count ? linkset.entities_count.toLocaleString('en') : 0 }}
              </div>
            </div>

            <div v-else class="col-auto">
              <div>
                <strong>Source / target entities in lens: </strong>
                {{ lens.lens_sources_count ? lens.lens_sources_count.toLocaleString('en') : 0 }} /
                {{ lens.lens_targets_count ? lens.lens_targets_count.toLocaleString('en') : 0 }}
              </div>

              <div>
                <strong>Total entities in lens: </strong>
                {{ lens.lens_entities_count ? lens.lens_entities_count.toLocaleString('en') : 0 }}
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

          <div v-if="isOpen" class="row justify-content-center mt-2">
            <div class="col-auto">
              <div class="btn-toolbar" role="toolbar" aria-label="Toolbar">
                <div class="btn-group btn-group-sm btn-group-toggle ml-auto">
                  <label class="btn btn-secondary" v-bind:class="{'active': showAcceptedLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showAcceptedLinks"
                           :disabled="loadingTotals" @change="resetLinks('filtering')"/>
                    {{ showAcceptedLinks ? 'Hide accepted' : 'Show accepted' }}

                    <span v-if="acceptedLinks !== null || allAcceptedLinks !== null" class="badge badge-light ml-1">
                      <template v-if="acceptedLinks !== null && allAcceptedLinks !== null">
                        {{ acceptedLinks.toLocaleString('en') }} /
                      </template>

                      <template v-if="allAcceptedLinks !== null">
                        {{ allAcceptedLinks.toLocaleString('en') }}
                      </template>
                    </span>
                  </label>

                  <label class="btn btn-secondary" v-bind:class="{'active': showRejectedLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showRejectedLinks"
                           :disabled="loadingTotals" @change="resetLinks('filtering')"/>
                    {{ showRejectedLinks ? 'Hide rejected' : 'Show rejected' }}

                    <span v-if="rejectedLinks !== null || allRejectedLinks !== null" class="badge badge-light ml-1">
                      <template v-if="rejectedLinks !== null && allRejectedLinks !== null">
                        {{ rejectedLinks.toLocaleString('en') }} /
                      </template>

                      <template v-if="allRejectedLinks !== null">
                        {{ allRejectedLinks.toLocaleString('en') }}
                      </template>
                    </span>
                  </label>

                  <label class="btn btn-secondary" v-bind:class="{'active': showNotSureLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showNotSureLinks"
                           :disabled="loadingTotals" @change="resetLinks('filtering')"/>
                    {{ showNotSureLinks ? 'Hide not sure' : 'Show not sure' }}

                    <span v-if="notSureLinks !== null || allAcceptedLinks !== null" class="badge badge-light ml-1">
                      <template v-if="notSureLinks !== null && allNotSureLinks !== null">
                        {{ notSureLinks.toLocaleString('en') }} /
                      </template>

                      <template v-if="allNotSureLinks !== null">
                        {{ allNotSureLinks.toLocaleString('en') }}
                      </template>
                    </span>
                  </label>

                  <label class="btn btn-secondary" v-bind:class="{'active': showNotValidatedLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showNotValidatedLinks"
                           :disabled="loadingTotals" @change="resetLinks('filtering')"/>
                    {{ showNotValidatedLinks ? 'Hide not validated' : 'Show not validated' }}

                    <span v-if="notValidatedLinks !== null || allNotValidatedLinks !== null"
                          class="badge badge-light ml-1">
                      <template v-if="notValidatedLinks !== null && allNotValidatedLinks !== null">
                        {{ notValidatedLinks.toLocaleString('en') }} /
                      </template>

                      <template v-if="allNotValidatedLinks !== null">
                        {{ allNotValidatedLinks.toLocaleString('en') }}
                      </template>
                    </span>
                  </label>

                  <label v-if="isLens" class="btn btn-secondary" v-bind:class="{'active': showMixedLinks}">
                    <input type="checkbox" autocomplete="off" v-model="showMixedLinks"
                           :disabled="loadingTotals" @change="resetLinks('filtering')"/>
                    {{ showMixedLinks ? 'Hide mixed' : 'Show mixed' }}

                    <span v-if="mixedLinks !== null || allMixedLinks !== null" class="badge badge-light ml-1">
                      <template v-if="mixedLinks !== null && allMixedLinks !== null">
                        {{ mixedLinks.toLocaleString('en') }} /
                      </template>

                      <template v-if="allMixedLinks !== null">
                        {{ allMixedLinks.toLocaleString('en') }}
                      </template>
                    </span>
                  </label>
                </div>

                <div class="btn-group btn-group-sm ml-4" role="group">
                  <button type="button" class="btn btn-white border"
                          :disabled="!resetShownLinks" @click="resetLinks('all', 'all')">
                    <fa-icon icon="sync"/>
                    Reset
                  </button>
                </div>

                <b-dropdown class="ml-4" variant="secondary" size="sm">
                  <template #button-content>
                    <fa-icon icon="check-square"/>
                    With selection
                  </template>

                  <b-dropdown-item-button variant="success" :disabled="isUpdating"
                                          @click="validateSelection('accepted')">
                    <fa-icon icon="check"/>
                    Accept
                  </b-dropdown-item-button>

                  <b-dropdown-item-button variant="danger" :disabled="isUpdating"
                                          @click="validateSelection('rejected')">
                    <fa-icon icon="times"/>
                    Reject
                  </b-dropdown-item-button>

                  <b-dropdown-item-button variant="warning" :disabled="isUpdating"
                                          @click="validateSelection('not_sure')">
                    <fa-icon icon="question"/>
                    Not sure
                  </b-dropdown-item-button>
                </b-dropdown>
              </div>
            </div>
          </div>

          <div v-if="isOpen" class="row justify-content-center mt-2">
            <div class="col-auto">
              <div class="btn-toolbar align-items-baseline" role="toolbar" aria-label="Toolbar">
                <div class="btn-group btn-group-sm mr-4">
                  <button type="button" class="btn btn-secondary" @click="showSimilarityConfig">
                    <fa-icon icon="info-circle"/>
                    Show specification
                  </button>

                  <button type="button" class="btn btn-secondary" :disabled="!view" @click="showPropertyConfig">
                    <fa-icon icon="cog"/>
                    Configure property labels
                  </button>
                </div>

                <div class="btn-group btn-group-sm mr-4">
                  <button type="button" class="btn btn-secondary" :disabled="!view" @click="showFilterConfig">
                    Filter on properties
                  </button>

                  <button type="button" class="btn btn-secondary" v-bind:class="{'active': clusters.length > 0}"
                          :disabled="!clustering" @click="showClusters">
                    Filter by cluster

                    <span class="badge badge-light ml-1">
                      {{ clusters.length.toLocaleString('en') }}
                    </span>
                  </button>
                </div>

                <div class="btn-group btn-group-sm btn-group-toggle input-group input-group-sm align-items-baseline">
                  <div class="input-group-prepend">
                    <div class="input-group-text bg-white">Similarity</div>

                    <div class="input-group-text">
                      <vue-slider v-model="similarityRange" class="mx-5 p-0"
                                  :width="150" :min="0" :max="1" :interval="0.05" :lazy="true"
                                  :tooltip-placement="['left', 'right']" tooltip="always"
                                  @change="resetLinks('filtering', 'filtering')"/>
                    </div>
                  </div>

                  <label class="btn btn-secondary" v-bind:class="{'active': sortDesc}">
                    <input type="radio" autocomplete="off" v-model="sortDesc" :value="true" :disabled="loadingTotals"
                           @change="resetLinks('reset', 'none')"/>
                    <fa-icon icon="sort-numeric-up"/>
                  </label>

                  <label class="btn btn-secondary" v-bind:class="{'active': !sortDesc}">
                    <input type="radio" autocomplete="off" v-model="sortDesc" :value="false" :disabled="loadingTotals"
                           @change="resetLinks('reset', 'none')"/>
                    <fa-icon icon="sort-numeric-down"/>
                  </label>
                </div>

                <div class="btn-group btn-group-sm ml-4" role="group">
                  <button class="btn btn-secondary"
                          :disabled="!hasProperties || clusters.length === 0 || clusters.length > 1"
                          @click="showVisualization">
                    <fa-icon icon="project-diagram"/>
                    Visualize
                  </button>
                </div>
              </div>
            </div>
          </div>
        </sub-card>
      </div>
    </template>

    <similarity-config :type="type" :spec="spec" ref="similarityConfig"/>

    <property-config v-if="view" :properties="view.properties" ref="propertyConfig"
                     @save="resetLinks('reset', 'properties')"/>

    <filter-config v-if="view" :filters="view.filters" ref="filterConfig"
                   @save="resetLinks('filtering', 'filtering')"/>

    <clusters v-if="clustering"
              :type="type"
              :spec-id="spec.id"
              :selected-clusters="clusters"
              :similarity-range="similarityRange"
              ref="clusters"
              @select="selectCluster"
              @closed="resetLinks('filtering', 'none')"/>

    <cluster-visualization
        v-if="clustering && clusters.length === 1 && hasProperties"
        :type="type"
        :spec-id="spec.id"
        :cluster="clusters[0]"
        ref="visualization"/>

    <template v-if="isOpen && !isUpdatingSelection">
      <link-component
          v-for="(link, idx) in links"
          :key="idx"
          :index="idx"
          :link="link"
          :is-active="currentIdx === idx"
          @accepted="validateLink(link,'accepted')"
          @rejected="validateLink(link,'rejected')"
          @not_sure="validateLink(link,'not_sure')"
          ref="link"/>

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
    import VueSlider from 'vue-slider-component';
    import InfiniteLoading from 'vue-infinite-loading';

    import Link from "./Link";
    import SimilarityConfig from "./SimilarityConfig";
    import PropertyConfig from "./PropertyConfig";
    import FilterConfig from "./FilterConfig";
    import Clusters from "./Clusters";
    import ClusterVisualization from "./ClusterVisualization";

    export default {
        name: "Validation",
        components: {
            VueSlider,
            InfiniteLoading,
            LinkComponent: Link,
            SimilarityConfig,
            PropertyConfig,
            FilterConfig,
            Clusters,
            ClusterVisualization,
        },
        data() {
            return {
                isOpen: false,
                isUpdating: false,
                isUpdatingSelection: false,

                showAcceptedLinks: false,
                showRejectedLinks: false,
                showNotSureLinks: false,
                showNotValidatedLinks: true,
                showMixedLinks: false,
                resetShownLinks: false,

                allAcceptedLinks: null,
                allRejectedLinks: null,
                allNotSureLinks: null,
                allNotValidatedLinks: null,
                allMixedLinks: null,

                acceptedLinks: null,
                rejectedLinks: null,
                notSureLinks: null,
                notValidatedLinks: null,
                mixedLinks: null,

                loadingTotals: false,
                loadingLinks: false,

                links: [],
                linksIdentifier: +new Date(),
                currentIdx: 0,

                clusters: [],
                similarityRange: [0, 1],
                sortDesc: true,
            };
        },
        props: {
            type: String,
            spec: Object,
        },
        computed: {
            isLinkset() {
                return this.type === 'linkset';
            },

            isLens() {
                return this.type === 'lens';
            },

            view() {
                return this.$root.getViewByIdAndType(this.spec.id, this.type);
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

            hasProperties() {
                return this.view && !Object.values(this.view.properties)
                    .flatMap(datasetProperty => datasetProperty.properties)
                    .map(prop => prop[0] !== '')
                    .includes(false);
            },

            clusterIds() {
                return this.clusters.map(cluster => cluster.id);
            },
        },
        methods: {
            async onToggle(isOpen) {
                this.isOpen = isOpen;

                if (isOpen) {
                    this.$emit('show');
                    await this.resetLinks('all', 'all');
                }
                else {
                    this.$emit('hide');
                    await this.resetLinks('reset', 'none');
                }
            },

            showSimilarityConfig() {
                this.$refs.similarityConfig.show();
            },

            showPropertyConfig() {
                this.$refs.propertyConfig.show();
            },

            showFilterConfig() {
                this.$refs.filterConfig.show();
            },

            showClusters() {
                this.$refs.clusters.show();
            },

            showVisualization() {
                this.$refs.visualization.showVisualization();
            },

            selectCluster(cluster) {
                if (this.clusters.includes(cluster))
                    this.clusters.splice(this.clusters.indexOf(cluster), 1);
                else
                    this.clusters.push(cluster);
            },

            async resetLinks(linkUpdate = 'all', clusterUpdate = 'none') {
                if (linkUpdate !== 'none') {
                    this.links = [];
                    this.linksIdentifier += 1;
                    this.currentIdx = 0;
                    this.resetShownLinks = false;
                }

                switch (linkUpdate) {
                    case 'no_filtering':
                        await this.getLinksTotals(false);
                        break;
                    case 'filtering':
                        await this.getLinksTotals(true);
                        break;
                    case 'all':
                        await this.getLinksTotals(false);
                        await this.getLinksTotals(true);
                        break;
                }

                switch (clusterUpdate) {
                    case 'properties':
                        this.$refs.clusters.triggerPropertiesUpdate();
                        break;
                    case 'filtering':
                        this.$refs.clusters.triggerFilteringUpdate();
                        break;
                    case 'all':
                        this.$refs.clusters.triggerPropertiesUpdate();
                        this.$refs.clusters.triggerFilteringUpdate();
                        break;
                }
            },

            async getLinksTotals(applyFiltering) {
                if (this.loadingTotals)
                    return;

                this.loadingTotals = true;

                const totals = await this.$root.getLinksTotals(this.type, this.spec.id, {
                    applyFilters: applyFiltering,
                    clusterIds: applyFiltering ? this.clusterIds : [],
                    min: applyFiltering ? this.similarityRange[0] : 0,
                    max: applyFiltering ? this.similarityRange[1] : 1
                });

                if (totals) {
                    if (applyFiltering) {
                        this.acceptedLinks = totals.accepted || 0;
                        this.rejectedLinks = totals.rejected || 0;
                        this.notSureLinks = totals.not_sure || 0;
                        this.notValidatedLinks = totals.not_validated || 0;
                        this.mixedLinks = totals.mixed || 0;
                    }
                    else {
                        this.allAcceptedLinks = totals.accepted || 0;
                        this.allRejectedLinks = totals.rejected || 0;
                        this.allNotSureLinks = totals.not_sure || 0;
                        this.allNotValidatedLinks = totals.not_validated || 0;
                        this.allMixedLinks = totals.mixed || 0;
                    }
                }

                this.loadingTotals = false;
            },

            async getLinks(state) {
                if (this.loadingLinks)
                    return;

                this.loadingLinks = true;

                const links = await this.$root.getLinks(this.type, this.spec.id, {
                    accepted: this.showAcceptedLinks, rejected: this.showRejectedLinks, notSure: this.showNotSureLinks,
                    notValidated: this.showNotValidatedLinks, mixed: this.showMixedLinks,
                    clusterIds: this.clusterIds, min: this.similarityRange[0], max: this.similarityRange[1],
                    sort: this.sortDesc ? 'desc' : 'asc'
                }, 50, this.links.length);

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

            async onKey(e) {
                if (!this.isOpen || this.isUpdating)
                    return;

                switch (e.keyCode) {
                    case 65: // a
                        await this.validateLink(this.links[this.currentIdx], 'accepted');
                        break;
                    case 88: // x
                        await this.validateLink(this.links[this.currentIdx], 'rejected');
                        break;
                    case 32: // space
                        await this.validateLink(this.links[this.currentIdx], 'not_sure');
                        break;
                    case 37: // arrow left
                    case 38: // arrow up
                        if (this.currentIdx > 0)
                            this.currentIdx--;
                        break;
                    case 39: // arrow right
                    case 40: // arrow down
                        if ((this.currentIdx + 1) < this.links.length)
                            this.currentIdx++;
                        break;
                }

                this.$refs.link[this.currentIdx].$el.scrollIntoView({behavior: 'smooth'});
            },

            async validateLink(link, validation) {
                const before = link.valid;
                const after = before === validation ? 'not_validated' : validation;

                this.isUpdating = true;
                link.updating = true;

                const result = await this.$root.validateLink(this.type, this.spec.id, after, link.source, link.target);

                this.isUpdating = false;
                link.updating = false;

                if (result !== null) {
                    link.valid = after;

                    switch (before) {
                        case 'not_validated':
                            this.notValidatedLinks--;
                            this.allNotValidatedLinks--;
                            break;
                        case 'accepted':
                            this.acceptedLinks--;
                            this.allAcceptedLinks--;
                            break;
                        case 'rejected':
                            this.rejectedLinks--;
                            this.allRejectedLinks--;
                            break;
                        case 'not_sure':
                            this.notSureLinks--;
                            this.allNotSureLinks--;
                            break;
                        case 'mixed':
                            this.mixedLinks--;
                            this.allMixedLinks--;
                            break;
                    }

                    switch (after) {
                        case 'not_validated':
                            this.notValidatedLinks++;
                            this.allNotValidatedLinks++;
                            break;
                        case 'accepted':
                            this.acceptedLinks++;
                            this.allAcceptedLinks++;
                            break;
                        case 'rejected':
                            this.rejectedLinks++;
                            this.allRejectedLinks++;
                            break;
                        case 'not_sure':
                            this.notSureLinks++;
                            this.allNotSureLinks++;
                            break;
                    }

                    if ((this.currentIdx + 1) < this.links.length)
                        this.currentIdx++;

                    this.resetShownLinks = true;
                    await this.resetLinks('none', 'filtering');
                }
            },

            async validateSelection(validation) {
                this.isUpdating = true;
                this.isUpdatingSelection = true;

                const result = await this.$root.validateSelection(this.type, this.spec.id, validation, {
                    accepted: this.showAcceptedLinks, rejected: this.showRejectedLinks, notSure: this.showNotSureLinks,
                    notValidated: this.showNotValidatedLinks, mixed: this.showMixedLinks,
                    clusterIds: this.clusterIds, min: this.similarityRange[0], max: this.similarityRange[1]
                });

                this.isUpdating = false;
                this.isUpdatingSelection = false;

                if (result !== null)
                    await this.resetLinks('all', 'filtering');
            },
        },
        mounted() {
            document.addEventListener('keyup', this.onKey);
        },
        destroyed() {
            document.removeEventListener('keyup', this.onKey);
        },
    };
</script>
