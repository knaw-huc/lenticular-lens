<template>
  <card :id="'resource_' + resource.id" type="resources" v-model="resource.label"
        :has-error="errors.length > 0" :has-handle="true">
    <template v-slot:title-columns>
      <div class="col-auto" v-if="resource.dataset.collection_id !== ''">
        <button type="button" class="btn btn-info" @click="runSample">
          Explore sample
        </button>

        <resource-sample-view :resource="resource" ref="resourceSampleView"/>
      </div>

      <div class="col-auto">
        <b-button variant="info" @click="$emit('duplicate', resource)">Duplicate</b-button>
      </div>

      <div v-if="!isUsedInAlignmentResults" class="col-auto">
        <button-delete v-on:click="$emit('remove')" title="Delete Collection"/>
      </div>
    </template>

    <sub-card label="Description">
      <textarea class="form-control mt-3" :id="'description_' + resource.id" v-model="resource.description">
      </textarea>

      <small class="form-text text-muted mt-2">
        Provide a description for this collection
      </small>
    </sub-card>

    <fieldset :disabled="isUsedInAlignmentResults">
      <sub-card label="Dataset" :hasError="errors.includes('dataset') || errors.includes('collection')">
        <div class="row form-group align-items-end mt-3">
          <label class="col-auto" :for="'timbuctoo_' + resource.id">
            Timbuctoo GraphQL endpoint:
          </label>

          <div class="col-5">
            <input type="text" v-model="resource.dataset.timbuctoo_graphql" class="form-control"
                   :id="'timbuctoo_' + resource.id" @input="resetDatasets"
                   v-bind:class="{'is-invalid': errors.includes('graphql_endpoint')}"/>
          </div>

          <div v-if="!resource.dataset.timbuctoo_hsid || !datasetsLoaded" class="col-4">
            <button v-if="!datasetsLoaded" class="btn btn-primary" @click="loadDatasets">Load datasets</button>

            <form v-if="!resource.dataset.timbuctoo_hsid" class="d-inline-block" :id="'login_' + resource.id"
                  method="post" action="https://secure.huygens.knaw.nl/saml2/login" target="loginWindow">
              <input type="hidden" name="hsurl" :value="hsurl()"/>
              <button class="btn btn-primary" v-bind:class="{'ml-2': !datasetsLoaded}" @click="login">
                {{ !datasetsLoaded ? 'Login and load datasets' : 'Login and reload datasets'}}
              </button>
            </form>
          </div>

          <div class="invalid-feedback" v-show="errors.includes('graphql_endpoint')">
            Please provide a valid Timbuctoo GraphQL endpoint
          </div>
        </div>

        <div v-if="datasetsLoaded" class="row">
          <div class="form-group col-8">
            <label :for="'dataset_' + resource.id">Dataset</label>

            <v-select :id="'dataset_' + resource.id" :value="selectedDataset" label="title" :options="datasetsList"
                      :clearable="false" :disabled="isUsedInAlignmentResults" autocomplete="off"
                      placeholder="Type to search for a dataset" @input="updateDataset"
                      v-bind:class="{'is-invalid': errors.includes('dataset')}">
              <div slot="option" slot-scope="option">
                <div>
                  <span class="font-weight-bold pr-2">{{ option.title }}</span>
                  <span class="text-wrap text-muted small">{{ option.name }}</span>
                </div>

                <div v-if="option.description" class="text-wrap font-italic small pt-2">
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

          <div v-if="resource.dataset.dataset_id !== ''" class="form-group collection-input col-4">
            <label :for="'collection_' + resource.id">Entity type</label>

            <v-select :id="'collection_' + resource.id" :value="selectedCollection" label="id"
                      :options="collectionsList" :clearable="false" :disabled="isUsedInAlignmentResults"
                      autocomplete="off" placeholder="Type to search for an entity type"
                      @input="updateCollection" v-bind:class="{'is-invalid': errors.includes('collection')}">
              <div slot="option" slot-scope="option">
                <div>
                  <span class="pr-2">{{ option.title || option.id }}</span>
                  <span class="font-italic text-muted small">{{ option.total }}</span>
                </div>

                <div class="small pt-1">
                  <download-progress :dataset-id="resource.dataset.dataset_id" :collection-id="option.id"/>
                </div>
              </div>
            </v-select>

            <div class="invalid-feedback" v-show="errors.includes('collection')">
              Please select an entity type
            </div>
          </div>
        </div>
      </sub-card>

      <sub-card v-if="resource.dataset.collection_id !== ''" label="Filter" :has-error="errors.includes('filters')">
        <conditions-group :conditions-group="resource.filter"
                          :is-root="true"
                          group="resource-filters"
                          :uid="'resource_' + resource.id + '_filter_group_0'"
                          validate-method-name="validateFilterCondition"
                          v-slot="curCondition"
                          @add="addFilterCondition($event)"
                          ref="filterGroupComponent">
          <resource-filter-condition
              :condition="curCondition.condition"
              :index="curCondition.index"
              :resource="resource"
              ref="filterConditionComponents"
              @add="curCondition.add()"
              @remove="curCondition.remove()"/>
        </conditions-group>
      </sub-card>

      <sub-card v-if="resource.dataset.collection_id !== ''" label="Sample" :hasError="errors.includes('limit')">
        <div class="form-group row align-items-end mt-3">
          <label class="col-auto" :for="'resource_' + resource.id + '_limit'">
            Only use a sample of this amount of records (-1 is no limit):
          </label>

          <input type="number" min="-1" v-model.number="resource.limit" class="form-control col-1"
                 :id="'resource_' + resource.id + '_limit'"
                 v-bind:class="{'is-invalid': errors.includes('limit')}">

          <div class="invalid-feedback" v-show="errors.includes('limit')">
            Please provide a limit, or -1 if there is no limit
          </div>
        </div>

        <div class="form-check">
          <input v-model.boolean="resource.random" type="checkbox" class="form-check-input"
                 :id="'resource_' + resource.id + '_random'">

          <label class="form-check-label" :for="'resource_' + resource.id + '_random'">Randomize order</label>
        </div>
      </sub-card>

      <sub-card v-if="resource.dataset.collection_id !== ''" label="Relations" add-button="Add Relation"
                :hasError="errors.find(err => err.startsWith('relations_'))" @add="addRelation">
        <div v-if="resource.related.length === 0" class="font-italic mt-3">
          No relations
        </div>

        <div v-if="resource.related.length > 0" class="form-group form-check mt-3">
          <input :id="resource.label + 'related_array'" class="form-check-input" type="checkbox"
                 v-model="resource.related_array">

          <label :for="resource.label + 'related_array'" class="form-check-label">
            Use relations as combined source
          </label>
        </div>

        <div v-for="(relation, index) in resource.related" class="row">
          <div class="form-group col-4">
            <label :for="'resource_' + resource.id + '_related_' + relation.id + '_resource'">
              Related collection
            </label>

            <select-box v-model="relation.resource"
                        :id="'resource_' + resource.id + '_related_' + relation.id + '_resource'"
                        v-bind:class="{'is-invalid': errors.includes(`relations_resource_${index}`)}">
              <option disabled selected value="">Choose a collection</option>
              <option v-for="root_resource in $root.resources" :value="root_resource.id"
                      v-if="root_resource.id !== resource.id">
                {{ root_resource.label }}
              </option>
            </select-box>

            <div class="invalid-feedback" v-show="errors.includes(`relations_resource_${index}`)">
              Please provide a related collection
            </div>
          </div>

          <div v-if="relation.resource > 0" class="form-group col-4">
            <label :for="'resource_' + resource.id + '_related_' + relation.id + '_local_property'">
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

          <div v-if="relation.resource > 0" class="form-group col-3">
            <label :for="'resource_' + resource.id + '_related_' + relation.id + '_remote_property'">
              Remote property
            </label>

            <select-box v-model="relation.remote_property"
                        v-bind:class="{'is-invalid': errors.includes(`relations_remote_prop_${index}`)}">
              <option value="" selected disabled>Select remote property</option>
              <option v-for="(_, property) in getPropertiesForResource(relation.resource)" :value="property">
                {{ property }}
              </option>
            </select-box>

            <div class="invalid-feedback" v-show="errors.includes(`relations_remote_prop_${index}`)">
              Please provide a remote property
            </div>
          </div>

          <div class="form-group col-1 align-self-end">
            <button-delete size="" v-on:click="resource.related.splice(index, 1)"/>
          </div>
        </div>
      </sub-card>
    </fieldset>
  </card>
</template>

<script>
    import ConditionsGroup from "../../helpers/ConditionsGroup";
    import ValidationMixin from "../../../mixins/ValidationMixin";

    import ResourceSampleView from "./ResourceSampleView";
    import ResourceFilterCondition from "./ResourceFilterCondition";

    export default {
        name: "Resource",
        mixins: [ValidationMixin],
        components: {
            ConditionsGroup,
            ResourceSampleView,
            ResourceFilterCondition,
        },
        data() {
            return {
                prevAutoLabel: '',
                datasetsLoaded: true,
            };
        },
        props: {
            'resource': Object,
        },
        computed: {
            datasets() {
                return this.datasetsLoaded ? this.$root.getDatasets(
                    this.resource.dataset.timbuctoo_graphql, this.resource.dataset.timbuctoo_hsid) : {};
            },

            collections() {
                return this.resource.dataset.dataset_id
                    ? this.datasets[this.resource.dataset.dataset_id].collections : {};
            },

            datasetsList() {
                return Object.entries(this.datasets)
                    .map(([id, data]) => ({id, ...data}))
                    .sort((dsA, dsB) => dsA.title.localeCompare(dsB.title));
            },

            collectionsList() {
                return Object.entries(this.collections)
                    .map(([id, data]) => ({id, ...data}))
                    .sort((collA, collB) => collA.id.localeCompare(collB.id));
            },

            selectedDataset() {
                return this.datasetsList.find(dataset => dataset.id === this.resource.dataset.dataset_id);
            },

            selectedCollection() {
                return this.collectionsList.find(collection => collection.id === this.resource.dataset.collection_id);
            },

            autoLabel() {
                if (this.datasetsLoaded && this.resource.dataset.dataset_id && this.resource.dataset.collection_id) {
                    const datasetTitle = this.selectedDataset.title;
                    const collectionTitle = this.selectedCollection.title || this.resource.dataset.collection_id;
                    return `${datasetTitle} [type: ${collectionTitle}]`;
                }
                return 'Collection ' + (this.resource.id + 1);
            },

            isUsedInAlignmentResults() {
                const alignmentsInResults = this.$root.alignments.map(alignment => alignment.alignment);

                for (let i = 0; i < this.$root.matches.length; i++) {
                    const match = this.$root.matches[i];

                    if (alignmentsInResults.includes(match.id) &&
                        (match.sources.includes(this.resource.id) || match.targets.includes(this.resource.id))) {
                        return true;
                    }
                }

                return false;
            },

            filteredConditions() {
                return this.$root.getRecursiveConditions(this.resource.filter);
            },

            allCollections() {
                const all = this.filteredConditions.reduce((acc, condition) => {
                    return acc.concat(condition.property.filter((_, idx) => idx > 0 && idx % 2 === 0));
                }, [this.resource.dataset.collection_id]);
                return [...new Set(all)];
            },

            notDownloaded() {
                return this.allCollections.filter(collection => {
                    return ![...this.$root.downloading, ...this.$root.downloaded].find(downloadInfo => {
                        return downloadInfo.dataset_id === this.resource.dataset.dataset_id &&
                            downloadInfo.collection_id === collection;
                    });
                });
            },
        },
        methods: {
            hsurl() {
                return window.location.origin;
            },

            validateResource() {
                const datasetValid = this.validateField('dataset',
                    this.resource.dataset.dataset_id && this.datasets.hasOwnProperty(this.resource.dataset.dataset_id));

                const dataset = this.datasets[this.resource.dataset.dataset_id];
                const collectionValid = this.validateField('collection',
                    this.resource.dataset.collection_id &&
                    dataset && dataset.collections.hasOwnProperty(this.resource.dataset.collection_id));

                const limit = parseInt(this.resource.limit);
                const limitValid = this.validateField('limit', !isNaN(limit) && (limit === -1 || limit > 0));

                let relatedValid = true;
                this.errors = this.errors.filter(err => !err.startsWith('relations_'));
                this.resource.related.forEach((related, idx) => {
                    const remoteResource = this.$root.resources.find(res => res.id === parseInt(related.resource));
                    const resourceValid = this.validateField(`relations_resource_${idx}`,
                        related.resource && remoteResource);

                    const localProperties = dataset && dataset.collections
                        [this.resource.dataset.collection_id].properties;
                    const localPropValid = this.validateField(`relations_local_prop_${idx}`,
                        related.local_property && localProperties && localProperties.hasOwnProperty(related.local_property));

                    const remoteDatasets = remoteResource && ds[remoteResource.dataset.dataset_id];
                    const remoteProperties = remoteDatasets && remoteDatasets.collections
                        [remoteResource.dataset.collection_id].properties;
                    const remotePropValid = this.validateField(`relations_remote_prop_${idx}`,
                        related.remote_property && remoteProperties &&
                        remoteProperties.hasOwnProperty(related.remote_property));

                    if (!(resourceValid && localPropValid && remotePropValid))
                        relatedValid = false;
                });

                let filtersGroupsValid = true;
                if (this.$refs.filterGroupComponent)
                    filtersGroupsValid = this.$refs.filterGroupComponent.validateConditionsGroup();
                filtersGroupsValid = this.validateField('filters', filtersGroupsValid);

                return collectionValid && datasetValid && limitValid && relatedValid && filtersGroupsValid;
            },

            clearFilter() {
                this.resource.filter = {
                    type: 'AND',
                    conditions: [],
                };
            },

            updateDataset(dataset) {
                this.resource.dataset.dataset_id = dataset.id;
                this.resource.dataset.collection_id = '';
                this.resource.dataset.published = dataset.published;

                this.clearFilter();
            },

            updateCollection(collection) {
                this.resource.dataset.collection_id = collection.id;
                this.clearFilter();
            },

            addRelation(event) {
                if (event) event.target.blur();

                this.resource.related.push({
                    'resource': '',
                    'local_property': '',
                    'remote_property': '',
                });
            },

            addFilterCondition(group) {
                group.conditions.push({
                    type: '',
                    property: [this.resource.id, ''],
                });
            },

            getPropertiesForResource(resourceId) {
                const resource = this.$root.getResourceById(resourceId);
                return this.datasets[resource.dataset.dataset_id]['collections']
                    [resource.dataset.collection_id]['properties'];
            },

            resetDatasets() {
                this.datasetsLoaded = false;
                this.resource.dataset.dataset_id = '';
                this.resource.dataset.collection_id = '';

                this.clearFilter();
            },

            login() {
                this.resetDatasets();

                const loginWindow = window.open('', 'loginWindow');
                window.addEventListener('message', event => {
                    if (event.origin !== window.location.origin || !event.data.hasOwnProperty('timbuctoo-hsid'))
                        return;

                    this.resource.dataset.timbuctoo_hsid = event.data['timbuctoo-hsid'];

                    loginWindow.close();
                    this.loadDatasets();
                }, false);

                document.getElementById('login_' + this.resource.id).submit();
            },

            runSample() {
                if (!this.validateResource())
                    return;
                this.$refs.resourceSampleView.resetSample();
            },

            async loadDatasets() {
                await this.$root.loadDatasets(
                    this.resource.dataset.timbuctoo_graphql, this.resource.dataset.timbuctoo_hsid);
                this.datasetsLoaded = true;
            },
        },
        updated() {
            if (this.resource.label === this.prevAutoLabel) {
                this.prevAutoLabel = this.autoLabel;
                this.$set(this.resource, 'label', this.autoLabel);
            }
        },
        mounted() {
            if (!this.resource.label || this.resource.label === this.autoLabel) {
                this.prevAutoLabel = this.autoLabel;
                this.$set(this.resource, 'label', this.autoLabel);
            }

            if (this.datasetsList.length === 0)
                this.datasetsLoaded = false;

            if (this.resource.properties.length === 0)
                this.resource.properties.push(['']);
        },
    };
</script>
