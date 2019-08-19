<template>
  <div class="row align-items-center">
    <template v-if="resourceInfo">
      <div class="col-auto btn border border-info bg-white rounded-pill py-0 my-1"
           v-bind:class="small ? 'btn-sm' : {}">
        {{ dataset.title }}
      </div>

      <div class="col-auto btn border border-info bg-white rounded-pill py-0 my-1 mx-2"
           v-bind:class="small ? 'btn-sm' : {}">
        {{ resource.collection_id }}
      </div>

      <div class="col-auto pl-0 ml-0 my-1" v-if="!singular && !readOnly">
        <button-add @click="$emit('clone')" size="sm" title="Add another property"/>
        <button-delete v-if="allowDelete" class="ml-2" @click="$emit('delete')" size="sm" title="Remove this property"/>
      </div>
    </template>

    <template v-for="prop in props">
      <div
          v-if="!Array.isArray(prop.resources) && (followReferencedCollection || readOnly || prop.value[0] !== '__value__')"
          class="col-auto">
        <fa-icon icon="arrow-right"/>
      </div>

      <div v-if="prop.value[0] === '' && !readOnly" :value="prop.value[0]" class="col-auto p-0 my-1">
        <v-select @input="updateProperty($event, prop.idx)"
                  v-bind:class="{'is-invalid': errors.includes(`value_${prop.idx}`), 'form-control-sm': small}">
          <template v-if="Array.isArray(prop.resources)">
            <option v-for="collection in prop.resources" :key="collection.id" :value="collection.id">
              {{ collection.label }}
            </option>
          </template>

          <template v-else>
            <option value="" disabled selected>Choose a referenced collection</option>
            <option value="__value__">Value (do not follow reference)</option>
            <option v-for="collection in Object.keys(prop.resources)" :key="collection" :value="collection">
              {{ collection }}
            </option>
          </template>
        </v-select>
      </div>

      <template
          v-else-if="!Array.isArray(prop.resources) && (followReferencedCollection || readOnly || prop.value[0] !== '__value__')">
        <div v-if="readOnly" class="col-auto btn bg-info text-white rounded-pill py-0 my-1"
             v-bind:class="small ? 'btn-sm' : {}">
          {{ prop.value[0] }}
        </div>

        <button v-else type="button" class="col-auto btn btn-info rounded-pill py-0 my-1"
                v-bind:class="small ? 'btn-sm' : {}" @click="!readOnly ? $emit('resetProperty', prop.idx) : {}">
          {{ prop.value[0] }}
        </button>
      </template>

      <template v-if="prop.value[0] !== '' && prop.value[0] !== '__value__'">
        <div v-if="!Array.isArray(prop.resources)" class="col-auto">
          <fa-icon icon="arrow-right"/>
        </div>

        <div v-if="!prop.value[1] && !readOnly" class="col-auto p-0 my-1">
          <v-select :value="prop.value[1]" @input="updateProperty($event, prop.idx + 1)"
                    v-bind:class="{'is-invalid': errors.includes(`value_${prop.idx}`), 'form-control-sm': small}">
            <option value="" selected disabled>Choose a property</option>
            <option v-for="propertyOpt in Object.keys(prop.properties)" :value="propertyOpt">
              {{ propertyOpt }}
            </option>
          </v-select>
        </div>

        <div v-else-if="readOnly" class="col-auto btn bg-info text-white rounded-pill py-0 my-1"
             v-bind:class="small ? 'btn-sm' : {}">
          {{ prop.value[1] }}
        </div>

        <button v-else type="button" class="col-auto btn btn-info rounded-pill py-0 my-1"
                v-bind:class="small ? 'btn-sm' : {}" @click="!readOnly ? $emit('resetProperty', prop.idx + 1) : {}">
          {{ prop.value[1] }}
        </button>
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
            },
            followReferencedCollection: {
                type: Boolean,
                default: true
            },
        },
        computed: {
            resource() {
                return this.$root.getResourceById(this.property[0]);
            },

            dataset() {
                return this.$root.datasets[this.resource.dataset_id];
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
                            properties: this.getPropertiesForIndex(propertyIdx)
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

            getResourcesForIndex(index) {
                if (index === 0)
                    return this.$root.resources;

                const collectionId = index > 2 ? this.property[index - 2] : this.resource.collection_id;
                return this.dataset.collections[collectionId][this.property[index - 1]].referencedCollections;
            },

            getPropertiesForIndex(index) {
                const property = index === 0 ? this.resource.collection_id : this.property[index];
                return this.dataset.collections[property];
            },

            updateProperty(newValue, index) {
                this.$set(this.property, index, newValue);

                const collectionId = this.property.length > 2 ? this.property.slice(-2)[0] : this.resource.collection_id;
                const referencedCollections = this.$utilities.getOrCreate(this.$set,
                    this.dataset.collections[collectionId][this.property.slice(-1)[0]], 'referencedCollections', []);

                if (this.property.slice(-1)[0] && Object.keys(referencedCollections).length > 0) {
                    if (!this.followReferencedCollection)
                        this.property.push('__value__', '');
                    else
                        this.property.push('', '');
                }
            },
        },
    }
</script>
