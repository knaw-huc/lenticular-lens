<template>
  <div class="row align-items-center">
    <template v-if="resourceInfo">
      <div class="col-auto p-0">
        <div class="property-resource read-only" v-bind:class="{'btn-sm': small}">
          {{ dataset.title }}
        </div>
      </div>

      <div class="col-auto p-0">
        <div class="property-resource read-only mx-2" v-bind:class="{'btn-sm': small}">
          {{ resource.dataset.collection_id }}
        </div>
      </div>

      <div v-if="!singular && !readOnly" class="col-auto pl-0 ml-0 my-1">
        <button-add @click="$emit('clone')" size="sm" title="Add another property"/>
        <button-delete v-if="allowDelete" class="ml-2" @click="$emit('delete')" size="sm" title="Remove this property"/>
      </div>
    </template>

    <template v-for="prop in props">
      <div v-if="!Array.isArray(prop.resources) && prop.inPath" class="col-auto">
        <fa-icon icon="arrow-right"/>
      </div>

      <div v-if="prop.value[0] === '' && !readOnly" :value="prop.value[0]" class="col-auto p-0 my-1">
        <v-select :clearable="false" autocomplete="off" placeholder="Choose a referenced collection"
                  :options="['__value__', ...Object.keys(prop.resources).sort()]"
                  @input="updateProperty($event, prop.idx)"
                  v-bind:class="{'is-invalid': errors.includes(`value_${prop.idx}`)}">
          <div slot="option" slot-scope="option">
            <div v-if="option.label === '__value__'">
              <span class="text-success pr-2">Value</span>
              <span class="font-italic text-muted small">Do not follow reference</span>
            </div>

            <template v-else>
              <div>
                <span class="pr-2">{{ option.label }}</span>
                <span class="font-italic text-muted small">{{ prop.resources[option.label].total }}</span>
              </div>

              <div class="small pt-1">
                <download-progress :dataset-id="resource.dataset.dataset_id" :collection-id="option.label"/>
              </div>
            </template>
          </div>
        </v-select>
      </div>

      <template v-else-if="!Array.isArray(prop.resources) && prop.inPath">
        <div v-if="readOnly" class="col-auto p-0">
          <div class="property-path read-only" v-bind:class="{'btn-sm': small}">
            {{ prop.value[0] }}
          </div>
        </div>

        <div v-else class="col-auto p-0">
          <button type="button" class="property-path" v-bind:class="{'btn-sm': small}"
                  @click="$emit('resetProperty', prop.idx)">
            {{ prop.value[0] }}
          </button>
        </div>
      </template>

      <template v-if="prop.value[0] !== '' && prop.value[0] !== '__value__'">
        <div v-if="!Array.isArray(prop.resources)" class="col-auto">
          <fa-icon icon="arrow-right"/>
        </div>

        <div v-if="!prop.value[1] && !readOnly" class="col-auto p-0 my-1">
          <v-select :clearable="false" autocomplete="off" placeholder="Choose a property"
                    :options="Object.keys(prop.properties).sort()" @input="updateProperty($event, prop.idx + 1)"
                    v-bind:class="{'is-invalid': errors.includes(`value_${prop.idx}`)}">
            <div slot="option" slot-scope="option">
              <div>{{ option.label }}</div>

              <div class="clearfix">
                <ul class="small font-italic text-info inline-list px-0 pt-1">
                  <li>Density: {{ prop.properties[option.label].density }}&percnt;</li>
                  <li v-if="prop.properties[option.label].isValueType">Has values</li>
                  <li v-if="prop.properties[option.label].isLink">Has links to another collection</li>
                </ul>
              </div>
            </div>
          </v-select>
        </div>

        <div v-else-if="readOnly" class="col-auto p-0">
          <div class="property-path read-only" v-bind:class="{'btn-sm': small}">
            {{ prop.value[1] }}
          </div>
        </div>

        <div v-else class="col-auto p-0">
          <button type="button" class="property-path" v-bind:class="{'btn-sm': small}"
                  @click="$emit('resetProperty', prop.idx + 1)">
            {{ prop.value[1] }}
          </button>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
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

            dataset() {
                const datasets = this.$root.getDatasets(
                    this.resource.dataset.timbuctoo_graphql, this.resource.dataset.timbuctoo_hsid);
                return datasets[this.resource.dataset.dataset_id];
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
                    const valid =
                        (prop.value[0] === '__value__') || (prop.value.find(value => value === '') === undefined);
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

                const collectionId = index > 2 ? this.property[index - 2] : this.resource.dataset.collection_id;
                const property = this.getPropertiesForCollection(collectionId)[this.property[index - 1]];
                return this.getReferencedCollections(property.referencedCollections);
            },

            getPropertiesForIndex(index) {
                const collectionId = index === 0 ? this.resource.dataset.collection_id : this.property[index];
                return this.getPropertiesForCollection(collectionId);
            },

            updateProperty(newValue, index) {
                this.$set(this.property, index, newValue);

                const collectionId = this.property.length > 2
                    ? this.property.slice(-2)[0]
                    : this.resource.dataset.collection_id;

                const prop = this.property.slice(-1)[0];
                const properties = prop ? this.getPropertiesForCollection(collectionId)[prop] : null;
                if (properties && properties.referencedCollections.length > 0)
                    this.property.push('', '');
            },
        },
    };
</script>
