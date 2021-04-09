<template>
  <card :id="'entity_type_selection_' + entityTypeSelection.id" type="entityTypeSelections"
        :res-id="entityTypeSelection.id" v-model="entityTypeSelection.label"
        :has-error="errors.length > 0" :has-handle="true"
        @show="onToggle(true)" @hide="onToggle(false)">
    <template v-slot:title-columns>
      <div class="col-auto" v-if="entityTypeSelection.dataset.collection_id !== ''">
        <button type="button" class="btn btn-secondary" @click="runSample">
          Explore sample
        </button>

        <sample-view :entity-type-selection="entityTypeSelection" ref="sampleView"/>
      </div>

      <div v-if="!isOpen" class="col-auto">
        <button class="btn btn-secondary" @click="$emit('duplicate', entityTypeSelection)">Duplicate</button>
      </div>

      <div v-if="!isOpen" class="col-auto">
        <button-delete v-on:click="$emit('remove')" title="Delete Collection" :disabled="isUsedInLinkset"/>
      </div>
    </template>

    <sub-card label="Description">
      <textarea class="form-control mt-3" :id="'description_' + entityTypeSelection.id"
                v-model="entityTypeSelection.description">
      </textarea>

      <small class="form-text text-muted mt-2">
        Provide a description for this entity-type selection
      </small>
    </sub-card>

    <fieldset :disabled="isUsedInLinkset">
      <sub-card label="Dataset" :hasError="errors.includes('dataset') || errors.includes('collection')">
        <div class="row form-group align-items-end mt-3">
          <label class="col-auto" :for="'timbuctoo_' + entityTypeSelection.id">
            Timbuctoo GraphQL endpoint:
          </label>

          <div class="col-5">
            <input type="text" v-model="entityTypeSelection.dataset.timbuctoo_graphql" class="form-control"
                   :id="'timbuctoo_' + entityTypeSelection.id" @input="resetDatasets"
                   v-bind:class="{'is-invalid': errors.includes('graphql_endpoint')}"/>
          </div>

          <div v-if="!datasetsLoaded" class="col-4">
            <button v-if="!datasetsLoaded" class="btn btn-primary" @click="loadDatasets">Load datasets</button>
          </div>

          <div class="invalid-feedback" v-show="errors.includes('graphql_endpoint')">
            Please provide a valid Timbuctoo GraphQL endpoint
          </div>
        </div>

        <div v-if="datasetsLoaded" class="row">
          <div class="form-group col-8">
            <label :for="'dataset_' + entityTypeSelection.id">Dataset</label>

            <v-select :id="'dataset_' + entityTypeSelection.id" :value="selectedDataset" :options="datasetsList"
                      :clearable="false" :disabled="isUsedInLinkset" autocomplete="off"
                      placeholder="Type to search for a dataset" @input="updateDataset"
                      v-bind:class="{'is-invalid': errors.includes('dataset')}">
              <div slot="option" slot-scope="option">
                <div>
                  <span class="font-weight-bold">{{ option.title }}</span>
                  <span class="smaller text-wrap text-muted ml-1">{{ option.name }}</span>
                </div>

                <div v-if="option.description" class="text-wrap font-italic small pt-1">
                  {{ option.description }}
                </div>
              </div>
            </v-select>

            <small v-if="selectedDataset" class="form-text text-muted mt-2">
              {{ selectedDataset.description }}
            </small>

            <div class="invalid-feedback" v-show="errors.includes('dataset')">
              Please select a dataset
            </div>
          </div>

          <div v-if="entityTypeSelection.dataset.dataset_id !== ''" class="form-group collection-input col-4">
            <label :for="'collection_' + entityTypeSelection.id">Entity type</label>

            <v-select :id="'collection_' + entityTypeSelection.id" :value="selectedCollection"
                      :options="collectionsList" :clearable="false" :disabled="isUsedInLinkset"
                      autocomplete="off" placeholder="Type to search for an entity type"
                      @input="updateCollection" v-bind:class="{'is-invalid': errors.includes('collection')}">
              <div slot="option" slot-scope="option">
                <div>
                  {{ option.title || option.shortenedUri || option.id }}
                  <span class="smaller font-italic text-muted ml-1">{{ option.total.toLocaleString('en') }}</span>
                </div>

                <div class="smaller pt-1">
                  <download-progress :dataset-id="entityTypeSelection.dataset.dataset_id" :collection-id="option.id"/>
                </div>
              </div>
            </v-select>

            <small v-if="selectedCollection" class="form-text text-muted mt-2">
              Size: {{ selectedCollection.total.toLocaleString('en') }}
              <download-progress class="ml-1"
                                 :dataset-id="entityTypeSelection.dataset.dataset_id"
                                 :collection-id="selectedCollection.id"/>
            </small>

            <div class="invalid-feedback" v-show="errors.includes('collection')">
              Please select an entity type
            </div>
          </div>
        </div>
      </sub-card>

      <sub-card v-if="entityTypeSelection.dataset.collection_id !== ''" label="Filter"
                :has-error="errors.includes('filters')">
        <logic-box :element="entityTypeSelection.filter" elements-name="conditions" :is-root="true"
                   group="entity-type-selection-filters"
                   :uid="'entity-type-selection_' + entityTypeSelection.id + '_filter_group_0'"
                   validate-method-name="validateFilterCondition" empty-elements-text="No conditions"
                   validation-failed-text="Please provide at least one condition" v-slot="curCondition"
                   @add="addFilterCondition($event)" ref="filterGroupComponent">
          <filter-condition
              :condition="curCondition.element"
              :index="curCondition.index"
              :entity-type-selection="entityTypeSelection"
              ref="filterConditionComponents"
              @add="curCondition.add()"
              @remove="curCondition.remove()"/>
        </logic-box>
      </sub-card>

      <sub-card v-if="entityTypeSelection.dataset.collection_id !== ''" label="Sample"
                :hasError="errors.includes('limit')">
        <div class="form-group row align-items-end mt-3">
          <label class="col-auto" :for="'entity_type_selection_' + entityTypeSelection.id + '_limit'">
            Only use a sample of this amount of records (-1 is no limit):
          </label>

          <input type="number" min="-1" v-model.number="entityTypeSelection.limit" class="form-control col-1"
                 :id="'entity_type_selection_' + entityTypeSelection.id + '_limit'"
                 v-bind:class="{'is-invalid': errors.includes('limit')}">

          <div class="invalid-feedback" v-show="errors.includes('limit')">
            Please provide a limit, or -1 if there is no limit
          </div>
        </div>

        <div class="form-check">
          <input v-model.boolean="entityTypeSelection.random" type="checkbox" class="form-check-input"
                 :id="'entity_type_selection_' + entityTypeSelection.id + '_random'">

          <label class="form-check-label" :for="'entity_type_selection_' + entityTypeSelection.id + '_random'">
            Randomize order
          </label>
        </div>
      </sub-card>
    </fieldset>
  </card>
</template>

<script>
    import LogicBox from "@/components/helpers/LogicBox";
    import FilterCondition from "@/components/helpers/FilterCondition";

    import ValidationMixin from "@/mixins/ValidationMixin";

    import SampleView from "./SampleView";

    export default {
        name: "EntityTypeSelection",
        mixins: [ValidationMixin],
        components: {
            LogicBox,
            FilterCondition,
            SampleView,
        },
        data() {
            return {
                prevAutoLabel: '',
                datasetsLoaded: true,
                isOpen: false,
            };
        },
        props: {
            entityTypeSelection: Object,
        },
        computed: {
            datasets() {
                return this.datasetsLoaded
                    ? this.$root.getDatasets(this.entityTypeSelection.dataset.timbuctoo_graphql) : {};
            },

            collections() {
                return this.entityTypeSelection.dataset.dataset_id
                    ? this.datasets[this.entityTypeSelection.dataset.dataset_id].collections : {};
            },

            datasetsList() {
                return Object.entries(this.datasets)
                    .map(([id, data]) => ({id, ...data, label: data.title || data.id}))
                    .sort((dsA, dsB) => dsA.title.localeCompare(dsB.title));
            },

            collectionsList() {
                return Object.entries(this.collections)
                    .map(([id, data]) => ({id, ...data, label: data.title || data.shortenedUri || data.id}))
                    .sort((collA, collB) => collA.id.localeCompare(collB.id));
            },

            selectedDataset() {
                return this.datasetsList.find(dataset =>
                    dataset.id === this.entityTypeSelection.dataset.dataset_id);
            },

            selectedCollection() {
                return this.collectionsList.find(collection =>
                    collection.id === this.entityTypeSelection.dataset.collection_id);
            },

            autoLabel() {
                if (this.datasetsLoaded && this.entityTypeSelection.dataset.dataset_id
                    && this.entityTypeSelection.dataset.collection_id) {
                    const datasetTitle = this.selectedDataset.title;
                    const collectionTitle = this.selectedCollection.title
                        || this.entityTypeSelection.dataset.collection_id;
                    return `${datasetTitle} [type: ${collectionTitle}]`;
                }
                return 'Entity-type selection ' + (this.entityTypeSelection.id + 1);
            },

            isUsedInLinkset() {
                const ids = this.$root.linksets.map(linkset => linkset.spec_id);

                for (let i = 0; i < this.$root.linksetSpecs.length; i++) {
                    const linksetSpec = this.$root.linksetSpecs[i];

                    if (ids.includes(linksetSpec.id) &&
                        (linksetSpec.sources.includes(this.entityTypeSelection.id) ||
                            linksetSpec.targets.includes(this.entityTypeSelection.id))) {
                        return true;
                    }
                }

                return false;
            },

            filteredConditions() {
                return this.$root.getRecursiveElements(this.entityTypeSelection.filter, 'conditions');
            },

            allCollections() {
                const all = this.filteredConditions.reduce((acc, condition) => {
                    return acc.concat(condition.property.filter((_, idx) => idx > 0 && idx % 2 === 0));
                }, [this.entityTypeSelection.dataset.collection_id]);
                return [...new Set(all)];
            },

            notDownloaded() {
                return this.allCollections.filter(collection => {
                    return ![...this.$root.downloading, ...this.$root.downloaded].find(downloadInfo => {
                        return downloadInfo.dataset_id === this.entityTypeSelection.dataset.dataset_id &&
                            downloadInfo.collection_id === collection;
                    });
                });
            },

            hasProperties() {
                return this.entityTypeSelection.properties.length > 0 &&
                    !this.entityTypeSelection.properties.find(prop => prop[0] === '');
            },
        },
        methods: {
            validateEntityTypeSelection() {
                const datasetValid = this.validateField('dataset',
                    this.entityTypeSelection.dataset.dataset_id &&
                    this.datasets.hasOwnProperty(this.entityTypeSelection.dataset.dataset_id));

                const dataset = this.datasets[this.entityTypeSelection.dataset.dataset_id];
                const collectionValid = this.validateField('collection',
                    this.entityTypeSelection.dataset.collection_id &&
                    dataset && dataset.collections.hasOwnProperty(this.entityTypeSelection.dataset.collection_id));

                const limit = parseInt(this.entityTypeSelection.limit);
                const limitValid = this.validateField('limit', !isNaN(limit) && (limit === -1 || limit > 0));

                let filtersGroupsValid = true;
                if (this.$refs.filterGroupComponent)
                    filtersGroupsValid = this.$refs.filterGroupComponent.validateLogicBox();
                filtersGroupsValid = this.validateField('filters', filtersGroupsValid);

                return collectionValid && datasetValid && limitValid && filtersGroupsValid;
            },

            onToggle(isOpen) {
                this.isOpen = isOpen;
                isOpen ? this.$emit('show') : this.$emit('hide');
            },

            clearFilter() {
                this.entityTypeSelection.filter = {
                    type: 'AND',
                    conditions: [],
                };
            },

            updateDataset(dataset) {
                this.entityTypeSelection.dataset.dataset_id = dataset.id;
                this.entityTypeSelection.dataset.collection_id = '';

                this.clearFilter();
            },

            updateCollection(collection) {
                this.entityTypeSelection.dataset.collection_id = collection.id;
                this.clearFilter();
            },

            addFilterCondition(group) {
                group.conditions.push({
                    type: '',
                    property: [''],
                });
            },

            resetDatasets() {
                this.datasetsLoaded = false;
                this.entityTypeSelection.dataset.dataset_id = '';
                this.entityTypeSelection.dataset.collection_id = '';

                this.clearFilter();
            },

            async runSample() {
                if (!this.validateEntityTypeSelection())
                    return;

                if (!this.hasProperties && this.filteredConditions.length > 0)
                    this.entityTypeSelection.properties = this.filteredConditions.map(condition => condition.property);

                await this.$root.submit();
                this.$refs.sampleView.resetSample();
            },

            async loadDatasets() {
                await this.$root.loadDatasets(this.entityTypeSelection.dataset.timbuctoo_graphql);
                this.datasetsLoaded = true;
            },
        },
        updated() {
            if (this.entityTypeSelection.label === this.prevAutoLabel) {
                this.prevAutoLabel = this.autoLabel;
                this.$set(this.entityTypeSelection, 'label', this.autoLabel);
            }
        },
        mounted() {
            if (!this.entityTypeSelection.label || this.entityTypeSelection.label === this.autoLabel) {
                this.prevAutoLabel = this.autoLabel;
                this.$set(this.entityTypeSelection, 'label', this.autoLabel);
            }

            if (this.datasetsList.length === 0)
                this.datasetsLoaded = false;

            if (this.entityTypeSelection.properties.length === 0)
                this.entityTypeSelection.properties.push(['']);
        },
    };
</script>
