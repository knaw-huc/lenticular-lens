<template>
  <div class="property">
    <template v-if="entityTypeSelectionInfo">
      <div class="property-pill property-resource read-only" :title="dataset.uri" v-bind:class="{'sm': small}">
        {{ dataset.title }}
      </div>

      <div class="property-pill property-resource read-only" :title="collection.uri" v-bind:class="{'sm': small}">
        {{ getCollectionLabel(collection, collectionId) }}

        <download-progress :dataset-id="datasetId" :collection-id="collectionId" :small="true" class="pl-2"/>
      </div>

      <span v-if="!singular && !readOnly" class="property-part">
        <button-add @click="$emit('clone')" size="sm" title="Add another property"/>
        <button-delete v-if="allowDelete" class="ml-2" @click="$emit('delete')" size="sm" title="Remove this property"/>
      </span>
    </template>

    <template v-for="prop in props">
      <template v-if="prop.collections">
        <fa-icon icon="arrow-right" class="property-part"/>

        <div v-if="prop.collection === '' && !readOnly" class="property-part">
          <v-select :value="prop.collection" :clearable="false" autocomplete="off"
                    placeholder="Choose a referenced collection"
                    :options="['__value__', ...Object.keys(prop.collections)]"
                    v-bind:class="{'is-invalid': errors.includes(`value_${prop.collectionIdx}`)}"
                    @input="updateProperty($event, prop.collectionIdx)" ref="select">
            <div slot="option" slot-scope="option">
              <div v-if="option.label === '__value__'">
                <span class="text-success pr-2">Value</span>
                <span class="font-italic text-muted smaller ml-1">Do not follow reference</span>
              </div>

              <template v-else>
                <div>
                  {{ getCollectionLabel(prop.collections[option.label], option.label) }}

                  <span v-if="isSameShortenedAndLongUri(prop.collections[option.label])"
                        class="smaller font-italic text-muted ml-1">
                    {{ prop.collections[option.label].uri }}
                  </span>

                  <span class="font-italic text-muted smaller ml-1">{{ prop.collections[option.label].total }}</span>
                </div>

                <div class="smaller pt-1">
                  <download-progress :dataset-id="entityTypeSelection.dataset.dataset_id"
                                     :collection-id="option.label"/>
                </div>
              </template>
            </div>
          </v-select>
        </div>

        <div v-else-if="readOnly" class="property-pill property-prop read-only"
             :title="prop.collections[prop.collection].uri" v-bind:class="{'sm': small}">
          {{ getCollectionLabel(prop.collections[prop.collection], prop.collection) }}

          <download-progress :dataset-id="datasetId" :collection-id="prop.collection" :small="true" class="pl-2"/>
        </div>

        <button v-else type="button" class="property-pill property-prop"
                :title="prop.collections[prop.collection].uri" v-bind:class="{'sm': small}"
                @click="resetProperty(prop.collectionIdx)">
          {{ getCollectionLabel(prop.collections[prop.collection], prop.collection) }}

          <download-progress :dataset-id="datasetId" :collection-id="prop.collection" :small="true" class="pl-2"/>
        </button>
      </template>

      <template v-if="prop.properties && prop.property !== '__value__'">
        <fa-icon v-if="prop.collection" icon="arrow-right" class="property-part"/>

        <div v-if="!prop.property && !readOnly" class="property-part">
          <v-select :clearable="false" autocomplete="off" placeholder="Choose a property"
                    :options="Object.keys(prop.properties)" @input="updateProperty($event, prop.propIdx)"
                    v-bind:class="{'is-invalid': errors.includes(`value_${prop.propIdx}`)}" ref="select">
            <div slot="option" slot-scope="option">
              <div>
                {{ getPropertyLabel(prop.properties[option.label], option.label) }}

                <span v-if="isSameShortenedAndLongUri(prop.properties[option.label])"
                      class="smaller font-italic text-muted ml-1">
                {{ prop.properties[option.label].uri }}
              </span>
              </div>

              <div class="clearfix smaller font-italic text-info pt-1">
                <ul class="inline-list px-0">
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
        </div>

        <div v-else-if="readOnly" class="property-pill property-prop read-only"
             :title="prop.properties[prop.property].uri" v-bind:class="{'sm': small}">
          {{ getPropertyLabel(prop.properties[prop.property], prop.property) }}
        </div>

        <button v-else type="button" class="property-pill property-prop"
                :title="prop.properties[prop.property].uri" v-bind:class="{'sm': small}"
                @click="resetProperty(prop.propIdx)">
          {{ getPropertyLabel(prop.properties[prop.property], prop.property) }}
        </button>
      </template>
    </template>

    <button v-if="notDownloaded.length > 0" type="button" class="property-pill property-download"
            v-bind:class="{'sm': small}" @click="startDownloading">
      Start downloading missing entities
    </button>

    <template v-if="!entityTypeSelectionInfo && !singular && !readOnly">
      <button-add @click="$emit('clone')" size="sm" title="Add another property"/>
      <button-delete v-if="allowDelete" class="ml-2" @click="$emit('delete')"
                     size="sm" title="Remove this property"/>
    </template>
  </div>
</template>

<script>
    import {EventBus} from "@/eventbus";
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

            getCollectionLabel(collection, collectionId) {
                return collection.title || collection.shortenedUri || collectionId;
            },

            getPropertyLabel(property, propertyId) {
                return property.shortenedUri ? (property.isInverse ? '← ' : '') + property.shortenedUri : propertyId;
            },

            getPropertiesForIndex(index) {
                const collectionId = index === 0 ? this.collectionId : this.property[index - 1];
                return this.getPropertiesForCollection(collectionId);
            },

            isSameShortenedAndLongUri(props) {
                return props.uri && props.shortenedUri !== props.uri;
            },

            getPropertiesForCollection(collectionId) {
                if (!this.dataset.collections.hasOwnProperty(collectionId))
                    return null;

                return Object.fromEntries(
                    Object
                        .entries(this.dataset.collections[collectionId].properties)
                        .sort(([idA, propA], [idB, propB]) => {
                            if (idA === 'uri')
                                return -1;
                            if (idB === 'uri')
                                return 1;

                            if (propA.shortenedUri && propB.shortenedUri) {
                                if (propA.shortenedUri === propA.uri && propB.shortenedUri !== propB.uri)
                                    return 1;

                                if (propB.shortenedUri === propB.uri && propA.shortenedUri !== propA.uri)
                                    return -1;

                                if (propA.shortenedUri === propB.shortenedUri)
                                    return propB.isInverse ? -1 : 1;

                                return propA.shortenedUri < propB.shortenedUri ? -1 : 1;
                            }

                            return idA < idB ? -1 : 1;
                        })
                );
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

                this.$nextTick(_ => {
                    if (this.$refs.select[0])
                        this.$refs.select[0].$el.querySelector('input').focus();
                });
            },

            async startDownloading() {
                const downloads = this.notDownloaded.map(async collection => this.$root.startDownload(
                    this.entityTypeSelection.dataset.dataset_id,
                    collection,
                    this.entityTypeSelection.dataset.timbuctoo_graphql,
                    this.entityTypeSelection.dataset.timbuctoo_hsid
                ));

                await Promise.all(downloads);
                EventBus.$emit('refreshDownloadsInProgress');
            },
        },
    };
</script>
