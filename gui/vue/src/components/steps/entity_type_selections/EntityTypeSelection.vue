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
        <b-button variant="secondary" @click="$emit('duplicate', entityTypeSelection)">Duplicate</b-button>
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

          <div v-if="!entityTypeSelection.dataset.timbuctoo_hsid || !datasetsLoaded" class="col-4">
            <button v-if="!datasetsLoaded" class="btn btn-primary" @click="loadDatasets">Load datasets</button>

            <form v-if="!entityTypeSelection.dataset.timbuctoo_hsid" class="d-inline-block"
                  :id="'login_' + entityTypeSelection.id"
                  method="post" action="https://secure.huygens.knaw.nl/saml2/login" target="loginWindow">
              <input type="hidden" name="hsurl" :value="hsurl()"/>
              <button class="btn btn-primary" v-bind:class="{'ml-2': !datasetsLoaded}" @click="login">
                {{ !datasetsLoaded ? 'Login and load datasets' : 'Login and reload datasets' }}
              </button>
            </form>
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

      <sub-card v-if="entityTypeSelection.dataset.collection_id !== ''" label="Relations" add-button="Add Relation"
                :hasError="errors.find(err => err.startsWith('relations_'))" @add="addRelation">
        <div v-if="entityTypeSelection.related.length === 0" class="font-italic mt-3">
          No relations
        </div>

        <div v-if="entityTypeSelection.related.length > 0" class="form-group form-check mt-3">
          <input :id="entityTypeSelection.label + 'related_array'" class="form-check-input" type="checkbox"
                 v-model="entityTypeSelection.related_array">

          <label :for="entityTypeSelection.label + 'related_array'" class="form-check-label">
            Use relations as combined source
          </label>
        </div>

        <div v-for="(relation, index) in entityTypeSelection.related" class="row">
          <div class="form-group col-4">
            <label :for="'entity_type_selection_' + entityTypeSelection.id + '_related_' + relation.id">
              Related entity-type selection
            </label>

            <select-box v-model="relation.entityTypeSelection"
                        :id="'entity_type_selection_' + entityTypeSelection.id + '_related_' + relation.id"
                        v-bind:class="{'is-invalid': errors.includes(`relations_entity_type_selection_${index}`)}">
              <option disabled selected value="">Choose an entity-type selection</option>
              <option v-if="ets.id !== entityTypeSelection.id"
                      v-for="ets in $root.entityTypeSelections" :value="ets.id">
                {{ ets.label }}
              </option>
            </select-box>

            <div class="invalid-feedback" v-show="errors.includes(`relations_entity_type_selection_${index}`)">
              Please provide a related entity-type selection
            </div>
          </div>

          <div v-if="relation.entityTypeSelection > 0" class="form-group col-4">
            <label
                :for="'entity_type_selection_' + entityTypeSelection.id + '_related_' + relation.id + '_local_property'">
              Local property
            </label>

            <select-box v-model="relation.local_property"
                        v-bind:class="{'is-invalid': errors.includes(`relations_local_prop_${index}`)}">
              <option value="" selected disabled>Select local property</option>
              <option v-for="(_, property) in selectedCollection['properties']" :value="property">
                {{ property }}
              </option>
            </select-box>

            <div class="invalid-feedback" v-show="errors.includes(`relations_local_prop_${index}`)">
              Please provide a local property
            </div>
          </div>

          <div v-if="relation.entityTypeSelection > 0" class="form-group col-3">
            <label
                :for="'entityTypeSelection_' + entityTypeSelection.id + '_related_' + relation.id + '_remote_property'">
              Remote property
            </label>

            <select-box v-model="relation.remote_property"
                        v-bind:class="{'is-invalid': errors.includes(`relations_remote_prop_${index}`)}">
              <option value="" selected disabled>Select remote property</option>
              <option v-for="(_, property) in getPropertiesForEntityTypeSelection(relation.entityTypeSelection)"
                      :value="property">
                {{ property }}
              </option>
            </select-box>

            <div class="invalid-feedback" v-show="errors.includes(`relations_remote_prop_${index}`)">
              Please provide a remote property
            </div>
          </div>

          <div class="form-group col-1 align-self-end">
            <button-delete size="sm" v-on:click="entityTypeSelection.related.splice(index, 1)"/>
          </div>
        </div>
      </sub-card>
    </fieldset>
  </card>
</template>

<script>
    import LogicBox from "../../helpers/LogicBox";
    import ValidationMixin from "../../../mixins/ValidationMixin";

    import SampleView from "./SampleView";
    import FilterCondition from "./FilterCondition";

    export default {
        name: "EntityTypeSelection",
        mixins: [ValidationMixin],
        components: {
            LogicBox,
            SampleView,
            FilterCondition,
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
                return this.datasetsLoaded ? this.$root.getDatasets(
                    this.entityTypeSelection.dataset.timbuctoo_graphql,
                    this.entityTypeSelection.dataset.timbuctoo_hsid
                ) : {};
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
            hsurl() {
                return window.location.origin;
            },

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

                let relatedValid = true;
                this.errors = this.errors.filter(err => !err.startsWith('relations_'));
                this.entityTypeSelection.related.forEach((related, idx) => {
                    const remoteentityTypeSelection = this.$root.entityTypeSelections.find(res => res.id === parseInt(related.entityTypeSelection));
                    const entityTypeSelectionValid = this.validateField(`relations_entity_type_selection_${idx}`,
                        related.entityTypeSelection && remoteentityTypeSelection);

                    const localProperties = dataset && dataset.collections
                        [this.entityTypeSelection.dataset.collection_id].properties;
                    const localPropValid = this.validateField(`relations_local_prop_${idx}`,
                        related.local_property && localProperties && localProperties.hasOwnProperty(related.local_property));

                    const remoteDatasets = remoteentityTypeSelection && this.datasets[remoteentityTypeSelection.dataset.dataset_id];
                    const remoteProperties = remoteDatasets && remoteDatasets.collections
                        [remoteentityTypeSelection.dataset.collection_id].properties;
                    const remotePropValid = this.validateField(`relations_remote_prop_${idx}`,
                        related.remote_property && remoteProperties &&
                        remoteProperties.hasOwnProperty(related.remote_property));

                    if (!(entityTypeSelectionValid && localPropValid && remotePropValid))
                        relatedValid = false;
                });

                let filtersGroupsValid = true;
                if (this.$refs.filterGroupComponent)
                    filtersGroupsValid = this.$refs.filterGroupComponent.validateLogicBox();
                filtersGroupsValid = this.validateField('filters', filtersGroupsValid);

                return collectionValid && datasetValid && limitValid && relatedValid && filtersGroupsValid;
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
                this.entityTypeSelection.dataset.published = dataset.published;

                this.clearFilter();
            },

            updateCollection(collection) {
                this.entityTypeSelection.dataset.collection_id = collection.id;
                this.clearFilter();
            },

            addRelation() {
                this.entityTypeSelection.related.push({
                    entityTypeSelection: '',
                    local_property: '',
                    remote_property: '',
                });
            },

            addFilterCondition(group) {
                group.conditions.push({
                    type: '',
                    property: [''],
                });
            },

            getPropertiesForEntityTypeSelection(entityTypeSelectionId) {
                const entityTypeSelection = this.$root.getEntityTypeSelectionById(entityTypeSelectionId);
                return this.datasets[entityTypeSelection.dataset.dataset_id]['collections']
                    [entityTypeSelection.dataset.collection_id]['properties'];
            },

            resetDatasets() {
                this.datasetsLoaded = false;
                this.entityTypeSelection.dataset.dataset_id = '';
                this.entityTypeSelection.dataset.collection_id = '';

                this.clearFilter();
            },

            login() {
                this.resetDatasets();

                const loginWindow = window.open('', 'loginWindow');
                window.addEventListener('message', event => {
                    if (event.origin !== window.location.origin || !event.data.hasOwnProperty('timbuctoo-hsid'))
                        return;

                    this.entityTypeSelection.dataset.timbuctoo_hsid = event.data['timbuctoo-hsid'];

                    loginWindow.close();
                    this.loadDatasets();
                }, false);

                document.getElementById('login_' + this.entityTypeSelection.id).submit();
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
                await this.$root.loadDatasets(
                    this.entityTypeSelection.dataset.timbuctoo_graphql, this.entityTypeSelection.dataset.timbuctoo_hsid);
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
