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
        <select-box @input="updateProperty($event, prop.idx)"
                    v-bind:class="{'is-invalid': errors.includes(`value_${prop.idx}`), 'form-control-sm': small}">
          <template v-if="Array.isArray(prop.resources)">
            <option v-for="collection in prop.resources" :key="collection.id" :value="collection.id">
              {{ collection.label }}
            </option>
          </template>

          <template v-else>
            <option value="" disabled selected>Choose a referenced collection</option>
            <option value="__value__">Value (do not follow reference)</option>
            <option v-for="collection in Object.keys(prop.resources).sort()" :key="collection" :value="collection">
              {{ collection }}
            </option>
          </template>
        </select-box>
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
          <select-box :value="prop.value[1]" @input="updateProperty($event, prop.idx + 1)"
                      v-bind:class="{'is-invalid': errors.includes(`value_${prop.idx}`), 'form-control-sm': small}">
            <option value="" selected disabled>Choose a property</option>
            <option v-for="propertyOpt in Object.keys(prop.properties).sort()" :value="propertyOpt">
              {{ propertyOpt }}
            </option>
          </select-box>
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
