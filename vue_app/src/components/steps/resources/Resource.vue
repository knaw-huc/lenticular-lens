<template>
  <card :id="'resource_' + resource.id" type="resources" v-model="resource.label" :hasError="errors.length > 0">
    <template v-slot:columns>
      <div class="col-auto">
        <button-delete v-on:click="$emit('remove')" :disabled="isUsedInAlignmentResults()" title="Delete Collection"/>
      </div>
    </template>

    <fieldset :disabled="isUsedInAlignmentResults()">
      <sub-card :hasError="errors.includes('dataset') || errors.includes('collection')">
        <div class="row">
          <div class="form-group col-8">
            <label :for="'dataset_' + resource.id">Dataset</label>

            <v-select v-model="resource.dataset_id" :id="'dataset_' + resource.id"
                      v-on:change="resource.collection_id = ''"
                      v-bind:class="{'is-invalid': errors.includes('dataset')}">
              <option value="" selected disabled>Choose a dataset</option>
              <option v-for="(data, dataset) in $root.datasets" v-bind:value="dataset">
                {{ data.title }}
              </option>
            </v-select>

            <div class="invalid-feedback" v-show="errors.includes('dataset')">
              Please select a dataset
            </div>
          </div>

          <div v-if="resource.dataset_id !== ''" class="form-group collection-input col-4">
            <label :for="'collection_' + resource.id">Entity type</label>

            <v-select v-model="resource.collection_id" :id="'collection_' + resource.id"
                      v-bind:class="{'is-invalid': errors.includes('collection')}">
              <option value="" selected disabled>Choose an entity type</option>
              <option v-for="(data, collection) in $root.datasets[resource.dataset_id].collections"
                      v-bind:value="collection">
                {{ collection }}
              </option>
            </v-select>

            <div class="invalid-feedback" v-show="errors.includes('collection')">
              Please select an entity type
            </div>
          </div>
        </div>
      </sub-card>

      <sub-card v-if="resource.collection_id !== ''" label="Filter" :hasError="errors.includes('filters')">
        <conditions-group :conditions-group="resource.filter"
                          :is-root="true"
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

      <sub-card v-if="resource.collection_id !== ''" label="Sample" :hasError="errors.includes('limit')">
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

      <sub-card v-if="resource.collection_id !== ''" label="Relations" add-button="Add Relation"
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

            <v-select v-model="relation.resource"
                      :id="'resource_' + resource.id + '_related_' + relation.id + '_resource'"
                      v-bind:class="{'is-invalid': errors.includes(`relations_resource_${index}`)}">
              <option disabled selected value="">Choose a collection</option>
              <option v-for="root_resource in $root.resources" :value="root_resource.id"
                      v-if="root_resource.id !== resource.id">
                {{ root_resource.label }}
              </option>
            </v-select>

            <div class="invalid-feedback" v-show="errors.includes(`relations_resource_${index}`)">
              Please provide a related collection
            </div>
          </div>

          <div v-if="relation.resource > 0" class="form-group col-4">
            <label :for="'resource_' + resource.id + '_related_' + relation.id + '_local_property'">
              Local property
            </label>

            <v-select v-model="relation.local_property"
                      v-bind:class="{'is-invalid': errors.includes(`relations_local_prop_${index}`)}">
              <option value="" selected disabled>Select local property</option>
              <option
                  v-for="(_, property) in $root.datasets[resource.dataset_id]['collections'][resource.collection_id]"
                  :value="property">
                {{ property }}
              </option>
            </v-select>

            <div class="invalid-feedback" v-show="errors.includes(`relations_local_prop_${index}`)">
              Please provide a local property
            </div>
          </div>

          <div v-if="relation.resource > 0" class="form-group col-3">
            <label :for="'resource_' + resource.id + '_related_' + relation.id + '_remote_property'">
              Remote property
            </label>

            <v-select v-model="relation.remote_property"
                      v-bind:class="{'is-invalid': errors.includes(`relations_remote_prop_${index}`)}">
              <option value="" selected disabled>Select remote property</option>
              <option v-for="(_, property) in getPropertiesForResource(relation.resource)" :value="property">
                {{ property }}
              </option>
            </v-select>

            <div class="invalid-feedback" v-show="errors.includes(`relations_remote_prop_${index}`)">
              Please provide a remote property
            </div>
          </div>

          <div class="form-group col-1 align-self-end">
            <button-delete v-on:click="resource.related.splice(index, 1)"/>
          </div>
        </div>
      </sub-card>
    </fieldset>
  </card>
</template>

<script>
    import Card from "../../structural/Card";
    import SubCard from "../../structural/SubCard";

    import ConditionsGroup from "../../helpers/ConditionsGroup";
    import ResourceFilterCondition from "./ResourceFilterCondition";
    import ValidationMixin from "../../../mixins/ValidationMixin";

    export default {
        name: "Resource",
        mixins: [ValidationMixin],
        components: {
            Card,
            SubCard,
            ConditionsGroup,
            ResourceFilterCondition,
        },
        data() {
            return {
                prevDatasetId: '',
                prevCollectionId: '',
            };
        },
        props: {
            'resource': Object,
        },
        computed: {
            autoLabel() {
                if (this.prevDatasetId && this.prevCollectionId) {
                    const datasetTitle = this.$root.datasets[this.prevDatasetId].title;
                    return `${datasetTitle} [type: ${this.prevCollectionId}]`;
                }
                return 'Collection ' + (this.resource.id + 1);
            },
        },
        methods: {
            validateResource() {
                const datasetValid = this.validateField('dataset',
                    this.resource.dataset_id && this.$root.datasets.hasOwnProperty(this.resource.dataset_id));

                const datasets = this.$root.datasets[this.resource.dataset_id];
                const collectionValid = this.validateField('collection',
                    this.resource.collection_id &&
                    datasets && datasets.collections.hasOwnProperty(this.resource.collection_id));

                const limit = parseInt(this.resource.limit);
                const limitValid = this.validateField('limit', !isNaN(limit) && (limit === -1 || limit > 0));

                let relatedValid = true;
                this.errors = this.errors.filter(err => !err.startsWith('relations_'));
                this.resource.related.forEach((related, idx) => {
                    const remoteResource = this.$root.resources.find(res => res.id === parseInt(related.resource));
                    const resourceValid = this.validateField(`relations_resource_${idx}`,
                        related.resource && remoteResource);

                    const localProperties = datasets && datasets.collections[this.resource.collection_id];
                    const localPropValid = this.validateField(`relations_local_prop_${idx}`,
                        related.local_property && localProperties && localProperties.hasOwnProperty(related.local_property));

                    const remoteDatasets = remoteResource && this.$root.datasets[remoteResource.dataset_id];
                    const remoteProperties = remoteDatasets && remoteDatasets.collections[remoteResource.collection_id];
                    const remotePropValid = this.validateField(`relations_remote_prop_${idx}`,
                        related.remote_property && remoteProperties && remoteProperties.hasOwnProperty(related.remote_property));

                    if (!(resourceValid && localPropValid && remotePropValid))
                        relatedValid = false;
                });

                let filtersGroupsValid = true;
                if (this.$refs.filterGroupComponent)
                    filtersGroupsValid = this.$refs.filterGroupComponent.validateConditionsGroup();
                filtersGroupsValid = this.validateField('filters', filtersGroupsValid);

                return collectionValid && datasetValid && limitValid && relatedValid && filtersGroupsValid;
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
                return this.$root.datasets[resource.dataset_id]['collections'][resource.collection_id];
            },
        },
        updated() {
            if (this.resource.label === this.autoLabel) {
                this.prevDatasetId = this.resource.dataset_id;
                this.prevCollectionId = this.resource.collection_id;

                this.$set(this.resource, 'label', this.autoLabel);
            }
        },
        mounted() {
            this.prevDatasetId = this.resource.dataset_id;
            this.prevCollectionId = this.resource.collection_id;

            if (!this.resource.label)
                this.$set(this.resource, 'label', this.autoLabel);
        },
    }
</script>
