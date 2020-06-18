<template>
  <div class="property">
    <div v-if="entityTypeSelectionInfo" class="property-resource resource-pills">
      <div class="property-pill read-only" v-bind:class="{'sm': small}">
        {{ dataset.title }}
      </div>

      <div class="property-pill read-only mx-2" v-bind:class="{'sm': small}">
        {{ collection.title || collectionId }}

        <download-progress :dataset-id="datasetId" :collection-id="collectionId" :small="true" class="pl-2"/>
      </div>

      <div v-if="!singular && !readOnly" class="mr-2">
        <button-add @click="$emit('clone')" size="sm" title="Add another property"/>
        <button-delete v-if="allowDelete" class="ml-2" @click="$emit('delete')" size="sm" title="Remove this property"/>
      </div>
    </div>

    <div class="property-path property-pills">
      <template v-for="prop in props">
        <template v-if="prop.collections">
          <div class="mx-2">
            <fa-icon icon="arrow-right"/>
          </div>

          <v-select v-if="prop.collection === '' && !readOnly" :value="prop.collection"
                    :clearable="false" autocomplete="off" placeholder="Choose a referenced collection"
                    :options="['__value__', ...Object.keys(prop.collections).sort()]"
                    v-bind:class="{'is-invalid': errors.includes(`value_${prop.collectionIdx}`)}"
                    @input="updateProperty($event, prop.collectionIdx)">
            <div slot="option" slot-scope="option">
              <div v-if="option.label === '__value__'">
                <span class="text-success pr-2">Value</span>
                <span class="font-italic text-muted small">Do not follow reference</span>
              </div>

              <template v-else>
                <div>
                  <span class="pr-2">{{ prop.collections[option.label].title || option.label }}</span>
                  <span class="font-italic text-muted small">{{ prop.collections[option.label].total }}</span>
                </div>

                <div class="small pt-1">
                  <download-progress :dataset-id="entityTypeSelection.dataset.dataset_id"
                                     :collection-id="option.label"/>
                </div>
              </template>
            </div>
          </v-select>

          <div v-else-if="readOnly" class="property-pill read-only" v-bind:class="{'sm': small}">
            {{ prop.collections[prop.collection].title || prop.collection }}

            <download-progress :dataset-id="datasetId" :collection-id="prop.collection" :small="true" class="pl-2"/>
          </div>

          <button v-else type="button" class="property-pill"
                  v-bind:class="{'sm': small}" @click="resetProperty(prop.collectionIdx)">
            {{ prop.collections[prop.collection].title || prop.collection }}

            <download-progress :dataset-id="datasetId" :collection-id="prop.collection" :small="true" class="pl-2"/>
          </button>
        </template>

        <template v-if="prop.properties && prop.property !== '__value__'">
          <div v-if="prop.collection" class="mx-2">
            <fa-icon icon="arrow-right"/>
          </div>

          <v-select v-if="!prop.property && !readOnly"
                    :clearable="false" autocomplete="off" placeholder="Choose a property"
                    :options="Object.keys(prop.properties).sort()" @input="updateProperty($event, prop.propIdx)"
                    v-bind:class="{'is-invalid': errors.includes(`value_${prop.propIdx}`)}">
            <div slot="option" slot-scope="option">
              <div>{{ option.label }}</div>

              <div class="clearfix">
                <ul class="small font-italic text-info inline-list px-0 pt-1">
                  <li>Density: {{ prop.properties[option.label].density }}&percnt;</li>
                  <li v-if="prop.properties[option.label].isValueType">Has values</li>

                  <li v-if="prop.properties[option.label].isLink && !prop.properties[option.label].isInverse">
                    Has links to another collection
                  </li>
                  <li v-else-if="prop.properties[option.label].isLink && prop.properties[option.label].isInverse">
                    Has inverted links to another collection
                  </li>
                </ul>
              </div>
            </div>
          </v-select>

          <div v-else-if="readOnly" class="property-pill read-only" v-bind:class="{'sm': small}">
            {{ prop.property }}
          </div>

          <button v-else type="button" class="property-pill"
                  v-bind:class="{'sm': small}" @click="resetProperty(prop.propIdx)">
            {{ prop.property }}
          </button>
        </template>
      </template>

      <button v-if="notDownloaded.length > 0" type="button" class="property-pill download-pill ml-4"
              v-bind:class="{'sm': small}" @click="startDownloading">
        Start downloading missing entities
      </button>
    </div>

    <div v-if="!entityTypeSelectionInfo && !singular && !readOnly" class="ml-2">
      <button-add @click="$emit('clone')" size="sm" title="Add another property"/>
      <button-delete v-if="allowDelete" class="ml-2" @click="$emit('delete')" size="sm" title="Remove this property"/>
    </div>
  </div>
</template>

<script>
    import {EventBus} from "../../eventbus";
    import ValidationMixin from "../../mixins/ValidationMixin";

    export default {
        name: "Property",
        mixins: [ValidationMixin],
        props: {
            entityTypeSelection: Object,
            property: Array,
            readOnly: {
                type: Boolean,
                default: false,
            },
            small: {
                type: Boolean,
                default: false,
            },
            singular: {
                type: Boolean,
                default: false,
            },
            allowDelete: {
                type: Boolean,
                default: true,
            },
            entityTypeSelectionInfo: {
                type: Boolean,
                default: true,
            }
        },
        computed: {
            datasetId() {
                return this.entityTypeSelection.dataset.dataset_id;
            },

            collectionId() {
                return this.entityTypeSelection.dataset.collection_id;
            },

            dataset() {
                const datasets = this.$root.getDatasets(
                    this.entityTypeSelection.dataset.timbuctoo_graphql, this.entityTypeSelection.dataset.timbuctoo_hsid);
                return datasets[this.datasetId];
            },

            collection() {
                return this.dataset.collections[this.collectionId];
            },

            entities() {
                return [
                    this.collectionId,
                    ...this.property
                        .filter(prop => prop !== '__value__' && prop !== '')
                        .filter((_, idx) => idx % 2 === 1)
                ];
            },

            downloading() {
                return this.entities.filter(entity => {
                    return this.$root.downloading.find(downloadInfo => {
                        return downloadInfo.dataset_id === this.datasetId && downloadInfo.collection_id === entity;
                    });
                });
            },

            notDownloaded() {
                return this.entities.filter(entity => {
                    return ![...this.$root.downloading, ...this.$root.downloaded].find(downloadInfo => {
                        return downloadInfo.dataset_id === this.datasetId && downloadInfo.collection_id === entity;
                    });
                });
            },

            props() {
                return new Array(Math.floor((this.property.length + 1) / 2))
                    .fill(null)
                    .map((_, idx) => {
                        const collectionIdx = idx > 0 ? (idx * 2) - 1 : null;
                        const propIdx = idx * 2;

                        return {
                            collectionIdx,
                            collection: collectionIdx ? this.property[collectionIdx] : null,
                            collections: this.getCollectionsForIndex(collectionIdx),
                            propIdx,
                            property: this.property[propIdx],
                            properties: this.getPropertiesForIndex(propIdx),
                        };
                    });
            },
        },
        methods: {
            validateProperty() {
                this.errors = [];
                return !this.property
                    .map((prop, idx) => this.validateField(`value_${idx}`, !!prop))
                    .includes(false);
            },

            getPropertiesForIndex(index) {
                const collectionId = index === 0 ? this.collectionId : this.property[index - 1];
                return this.getPropertiesForCollection(collectionId);
            },

            getPropertiesForCollection(collectionId) {
                return this.dataset.collections.hasOwnProperty(collectionId)
                    ? this.dataset.collections[collectionId].properties : null;
            },

            getCollectionsForIndex(index) {
                if (index === null)
                    return null;

                const properties = this.getPropertiesForIndex(index - 1);
                const property = properties[this.property[index - 1]];
                return this.getReferencedCollections(property.referencedCollections);
            },

            getReferencedCollections(referencedCollections) {
                return referencedCollections
                    .filter(collectionId => this.dataset.collections.hasOwnProperty(collectionId))
                    .reduce((acc, collectionId) => {
                        acc[collectionId] = this.dataset.collections[collectionId];
                        return acc;
                    }, {});
            },

            resetProperty(index) {
                const replaceBy = (index % 2 === 1) ? ['', ''] : [''];
                this.property.splice(index, (this.property.length - index), ...replaceBy);
            },

            updateProperty(newValue, index) {
                this.$set(this.property, index, newValue);

                const length = this.property.length;
                const collectionId = length > 2 ? this.property[length - 2] : this.collectionId;
                const prop = this.property[length - 1];

                if (newValue === '__value__')
                    this.property.splice(length - 1);

                const properties = prop ? this.getPropertiesForCollection(collectionId)[prop] : null;
                if (properties && properties.referencedCollections.length > 0)
                    this.property.push('', '');
            },

            async startDownloading() {
                const downloads = this.notDownloaded.map(async collection => {
                    return this.$root.startDownload(
                        this.entityTypeSelection.dataset.dataset_id,
                        collection,
                        this.entityTypeSelection.dataset.timbuctoo_graphql,
                        this.entityTypeSelection.dataset.timbuctoo_hsid
                    );
                });

                await Promise.all(downloads);
                EventBus.$emit('refreshDownloadsInProgress');
            },
        },
    };
</script>
