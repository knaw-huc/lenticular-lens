<template>
  <div class="property">
    <span class="first-el"/>

    <template v-if="showInfo">
      <div class="property-pill property-resource read-only" :title="dataset.uri" v-bind:class="{'sm': small}">
        {{ dataset.title }}
      </div>

      <div class="property-pill property-resource read-only" :title="collection.uri" v-bind:class="{'sm': small}">
        {{ getCollectionLabel(collection, collectionId) }}

        <download-progress :dataset-id="datasetId" :collection-id="collectionId" :small="true" class="pl-2"/>
      </div>

      <span v-if="(!singular && !readOnly) || hasAdditionalButtons" class="property-part">
        <template v-if="!singular && !readOnly">
          <button-add size="sm" title="Add another property" @click="$emit('clone')"/>
          <button-delete v-if="allowDelete" class="ml-2" size="sm" title="Remove this property"
                         @click="$emit('delete')"/>
        </template>

        <slot v-if="hasAdditionalButtons"/>
      </span>
    </template>

    <template v-for="prop in props">
      <template v-if="prop.collections">
        <fa-icon icon="arrow-right" class="property-part"/>

        <div v-if="prop.collection === '' && !readOnly" class="property-part">
          <v-select :value="prop.collection" :clearable="false" autocomplete="off"
                    placeholder="Choose a referenced collection"
                    :options="['__value__', ...Object.keys(prop.collections)]" :filter-by="prop.collectionFilterBy"
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
                  <download-progress :dataset-id="datasetId" :collection-id="option.label"/>
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
                    :options="Object.keys(prop.properties)" :filter-by="prop.propertyFilterBy"
                    @input="updateProperty($event, prop.propIdx)"
                    v-bind:class="{'is-invalid': errors.includes(`value_${prop.propIdx}`)}" ref="select">
            <div slot="option" slot-scope="option">
              <div>
                {{ getPropertyLabel(prop.properties[option.label], option.label) }}

                <span v-if="isSameShortenedAndLongUri(prop.properties[option.label])"
                      class="smaller font-italic text-muted ml-1">
                {{ prop.properties[option.label].uri }}
              </span>
              </div>

              <div class="clearfix smaller font-italic text-secondary pt-1">
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

    <template v-if="!showInfo && !singular && !readOnly">
      <button-add size="sm" title="Add another property" @click="$emit('clone')"/>
      <button-delete v-if="allowDelete" class="ml-2" size="sm" title="Remove this property"
                     @click="$emit('delete')"/>
    </template>

    <slot v-if="!showInfo && hasAdditionalButtons"/>
  </div>
</template>

<script>
    import {EventBus} from "@/eventbus";
    import ValidationMixin from "@/mixins/ValidationMixin";
    import {getPropertyInfo, getPropertiesForCollection} from "@/utils/property";

    export default {
        name: "Property",
        mixins: [ValidationMixin],
        props: {
            graphqlEndpoint: String,
            datasetId: String,
            collectionId: String,
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
            hasAdditionalButtons: {
                type: Boolean,
                default: false,
            },
            allowDelete: {
                type: Boolean,
                default: true,
            },
            showInfo: {
                type: Boolean,
                default: true,
            },
        },
        computed: {
            dataset() {
                const datasets = this.$root.getDatasets(this.graphqlEndpoint);
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
                return getPropertyInfo(this.property, this.collectionId, this.dataset.collections).map(prop => ({
                    ...prop,
                    collectionFilterBy: this.collectionFilterBy(prop.collections),
                    propertyFilterBy: this.propertyFilterBy(prop.properties),
                }));
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

            collectionFilterBy(collections) {
                return function (option, label, search) {
                    const s = search.toLowerCase();
                    const collection = collections.hasOwnProperty(option) ? collections[option] : null;

                    const optionMatches = (option || '').toLowerCase().indexOf(s) > -1;
                    const shortUriMatches = collection && (collection.shortenedUri || '').toLowerCase().indexOf(s) > -1;
                    const uriMatches = collection && (collection.uri || '').toLowerCase().indexOf(s) > -1;

                    return optionMatches || shortUriMatches || uriMatches;
                };
            },

            propertyFilterBy(properties) {
                return function (option, label, search) {
                    const s = search.toLowerCase();
                    const property = properties.hasOwnProperty(option) ? properties[option] : null;

                    const optionMatches = (option || '').toLowerCase().indexOf(s) > -1;
                    const shortUriMatches = property && (property.shortenedUri || '').toLowerCase().indexOf(s) > -1;
                    const uriMatches = property && (property.uri || '').toLowerCase().indexOf(s) > -1;

                    return optionMatches || shortUriMatches || uriMatches;
                };
            },

            isSameShortenedAndLongUri(props) {
                return props.uri && props.shortenedUri !== props.uri;
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

                const properties = prop
                    ? getPropertiesForCollection(collectionId, this.dataset.collections)[prop] : null;
                if (properties && properties.referencedCollections.length > 0)
                    this.property.push('', '');

                this.$nextTick(_ => {
                    if (this.$refs.select[0])
                        this.$refs.select[0].$el.querySelector('input').focus();
                });
            },

            async startDownloading() {
                const downloads = this.notDownloaded.map(async collection =>
                    this.$root.startDownload(this.datasetId, collection, this.graphqlEndpoint));

                await Promise.all(downloads);
                EventBus.$emit('refreshDownloadsInProgress');
            },
        },
    };
</script>
