<template>
  <div class="property">
    <div v-if="resourceInfo" class="property-resource resource-pills">
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
        <div v-if="!Array.isArray(prop.resources) && prop.inPath" class="mx-2">
          <fa-icon icon="arrow-right"/>
        </div>

        <v-select v-if="prop.value[0] === '' && !readOnly" :value="prop.value[0]"
                  :clearable="false" autocomplete="off" placeholder="Choose a referenced collection"
                  :options="['__value__', ...Object.keys(prop.resources).sort()]"
                  v-bind:class="{'is-invalid': errors.includes(`value_${prop.idx}`)}"
                  @input="updateProperty($event, prop.idx)">
          <div slot="option" slot-scope="option">
            <div v-if="option.label === '__value__'">
              <span class="text-success pr-2">Value</span>
              <span class="font-italic text-muted small">Do not follow reference</span>
            </div>

            <template v-else>
              <div>
                <span class="pr-2">{{ prop.resources[option.label].title || option.label }}</span>
                <span class="font-italic text-muted small">{{ prop.resources[option.label].total }}</span>
              </div>

              <div class="small pt-1">
                <download-progress :dataset-id="resource.dataset.dataset_id" :collection-id="option.label"/>
              </div>
            </template>
          </div>
        </v-select>

        <template v-else-if="!Array.isArray(prop.resources) && prop.inPath">
          <div v-if="readOnly" class="property-pill read-only" v-bind:class="{'sm': small}">
            {{ prop.resources[prop.value[0]].title || prop.value[0] }}

            <download-progress :dataset-id="datasetId" :collection-id="prop.value[0]" :small="true" class="pl-2"/>
          </div>

          <button v-else type="button" class="property-pill" v-bind:class="{'sm': small}"
                  @click="$emit('resetProperty', prop.idx)">
            {{ prop.resources[prop.value[0]].title || prop.value[0] }}

            <download-progress :dataset-id="datasetId" :collection-id="prop.value[0]" :small="true" class="pl-2"/>
          </button>
        </template>

        <template v-if="prop.value[0] !== '' && prop.value[0] !== '__value__'">
          <div v-if="!Array.isArray(prop.resources)" class="mx-2">
            <fa-icon icon="arrow-right"/>
          </div>

          <v-select v-if="!prop.value[1] && !readOnly"
                    :clearable="false" autocomplete="off" placeholder="Choose a property"
                    :options="Object.keys(prop.properties).sort()" @input="updateProperty($event, prop.idx + 1)"
                    v-bind:class="{'is-invalid': errors.includes(`value_${prop.idx}`)}">
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
            {{ prop.value[1] }}
          </div>

          <button v-else type="button" class="property-pill" v-bind:class="{'sm': small}"
                  @click="$emit('resetProperty', prop.idx + 1)">
            {{ prop.value[1] }}
          </button>
        </template>
      </template>

      <button v-if="notDownloaded.length > 0" type="button" class="property-pill download-pill ml-4"
              v-bind:class="{'sm': small}" @click="startDownloading">
        Start downloading missing entities
      </button>
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
            resourceInfo: {
                type: Boolean,
                default: true,
            }
        },
        computed: {
            resource() {
                return this.$root.getResourceById(this.property[0]);
            },

            datasetId() {
                return this.resource.dataset.dataset_id;
            },

            collectionId() {
                return this.resource.dataset.collection_id;
            },

            dataset() {
                const datasets = this.$root.getDatasets(
                    this.resource.dataset.timbuctoo_graphql, this.resource.dataset.timbuctoo_hsid);
                return datasets[this.datasetId];
            },

            collection() {
                return this.dataset['collections'][this.collectionId];
            },

            entities() {
                return [
                    this.collectionId,
                    ...this.property.filter((_, idx) => idx > 0 && idx % 2 === 0)
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
                return new Array(Math.floor(this.property.length / 2))
                    .fill(null)
                    .map((_, idx) => {
                        const propertyIdx = idx * 2;
                        return {
                            idx: propertyIdx,
                            value: this.property.slice(propertyIdx, propertyIdx + 2),
                            resources: this.getResourcesForIndex(propertyIdx),
                            properties: this.getPropertiesForIndex(propertyIdx),
                            inPath: this.readOnly || this.property[propertyIdx] !== '__value__',
                        };
                    });
            },
        },
        methods: {
            validateProperty() {
                this.errors = [];
                return !this.props.map(prop => {
                    const valid = (prop.value[0] === '__value__')
                        || (prop.value.find(value => value === '') === undefined);
                    return this.validateField(`value_${prop.idx}`, valid);
                }).includes(false);
            },

            getReferencedCollections(referencedCollections) {
                const collections = {};
                referencedCollections.forEach(collectionId =>
                    collections[collectionId] = this.dataset.collections[collectionId]);
                return collections;
            },

            getPropertiesForCollection(collectionId) {
                return this.dataset.collections.hasOwnProperty(collectionId)
                    ? this.dataset.collections[collectionId].properties : {};
            },

            getResourcesForIndex(index) {
                if (index === 0)
                    return this.$root.resources;

                const collectionId = index > 2 ? this.property[index - 2] : this.collectionId;
                const property = this.getPropertiesForCollection(collectionId)[this.property[index - 1]];
                return this.getReferencedCollections(property.referencedCollections);
            },

            getPropertiesForIndex(index) {
                const collectionId = index === 0 ? this.collectionId : this.property[index];
                return this.getPropertiesForCollection(collectionId);
            },

            updateProperty(newValue, index) {
                this.$set(this.property, index, newValue);

                const collectionId = this.property.length > 2
                    ? this.property.slice(-2)[0]
                    : this.collectionId;

                const prop = this.property.slice(-1)[0];
                const properties = prop ? this.getPropertiesForCollection(collectionId)[prop] : null;
                if (properties && properties.referencedCollections.length > 0)
                    this.property.push('', '');
            },

            async startDownloading() {
                const downloads = this.notDownloaded.map(async collection => {
                    return this.$root.startDownload(this.resource.dataset.dataset_id, collection,
                        this.resource.dataset.timbuctoo_graphql, this.resource.dataset.timbuctoo_hsid);
                });

                await Promise.all(downloads);
                EventBus.$emit('refreshDownloadsInProgress');
            },
        },
    };
</script>
