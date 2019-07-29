<template>
  <div class="col-auto">
    <div class="row align-items-center">
      <div v-if="showReferencedPropertyButton" class="col-auto p-1">
        <octicon name="arrow-right"/>
      </div>

      <div v-if="selectReferencedCollection || showResourceInfo || showReferencedPropertyButton" class="col-auto">
        <div v-if="selectReferencedCollection" class="row align-items-center">
          <v-select :value="value[0]" @input="updateInput($event, 0)" class="my-1"
                    v-bind:class="{'is-invalid': errors.includes('value'), 'form-control-sm': small}">
            <template v-if="Array.isArray(resources)">
              <option v-for="collection in resources" :key="collection.id" :value="collection.id">{{ collection.label }}
              </option>
            </template>
            <template v-else>
              <option value="" disabled selected>Choose a referenced collection</option>
              <option value="__value__">Value (do not follow reference)</option>
              <option v-for="collection in Object.keys(resources)" :key="collection" :value="collection">
                {{ collection }}
              </option>
            </template>
          </v-select>
        </div>

        <div v-else-if="showResourceInfo" class="row align-items-center">
          <div class="col-auto btn border border-info bg-white rounded-pill my-1 py-0"
               v-bind:class="small ? 'btn-sm' : {}">
            {{ $root.datasets[$root.getResourceById(value[0], resources).dataset_id].title }}
          </div>

          <div class="col-auto btn border border-info bg-white rounded-pill mx-2 my-1 py-0"
               v-bind:class="small ? 'btn-sm' : {}">
            {{ $root.getResourceById(value[0], resources).collection_id }}
          </div>

          <div class="col-auto ml-0 pl-0" v-if="!singular && !readOnly">
            <button-add
                @click="$emit('clone')"
                :scale="0.8"
                title="Add another property for this Collection"/>
            <button-delete @click="$emit('delete')" scale="1.3" title="Remove this property"/>
          </div>
        </div>

        <div v-else-if="showReferencedPropertyButton" class="row align-items-center">
          <div v-if="readOnly" class="col-auto btn bg-info text-white rounded-pill my-1 py-0"
               v-bind:class="small ? 'btn-sm' : {}">
            {{ value[0] }}
          </div>

          <button v-else type="button" class="col-auto btn btn-info rounded-pill my-1 py-0"
                  v-bind:class="small ? 'btn-sm' : {}" @click="!readOnly ? $emit('reset', 0) : {}">
            {{ value[0] }}
          </button>
        </div>
      </div>

      <template v-if="value[0] !== '' && value[0] !== '__value__'">
        <div v-if="!Array.isArray(resources)" class="col-auto p-1">
          <octicon name="arrow-right"/>
        </div>

        <div class="col-auto">
          <div class="row align-items-center">
            <template v-if="!value[1] && !readOnly">
              <v-select class="col-auto my-1" :value="value[1]" @input="updateInput($event, 1)"
                        v-bind:class="{'is-invalid': errors.includes('value'), 'form-control-sm': small}">
                <option value="" selected disabled>Choose a property</option>
                <option v-for="property_opt in Object.keys(properties)" :value="property_opt">{{ property_opt }}
                </option>
              </v-select>
            </template>

            <div v-else-if="readOnly" class="col-auto btn bg-info text-white rounded-pill my-1 py-0"
                 v-bind:class="small ? 'btn-sm' : {}">
              {{ value[1] }}
            </div>

            <button v-else type="button" class="col-auto btn btn-info rounded-pill my-1 py-0"
                    v-bind:class="small ? 'btn-sm' : {}" @click="!readOnly ? $emit('reset', 1) : {}">
              {{ value[1] }}
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
<script>
    import ValidationMixin from "../../mixins/ValidationMixin";

    export default {
        name: 'propertyComponent',
        mixins: [ValidationMixin],
        props: {
            properties: Object,
            resources: [Array, Object],
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
            singularResourceInfo: {
                type: Boolean,
                default: false,
            },
            followReferencedCollection: {
                type: Boolean,
                default: true
            },
            value: Array,
        },
        computed: {
            selectReferencedCollection() {
                return this.value[0] === '' && !this.readOnly;
            },

            showResourceInfo() {
                return Array.isArray(this.resources) && (!this.singular || this.singularResourceInfo || this.readOnly);
            },

            showReferencedPropertyButton() {
                return !Array.isArray(this.resources)
                    && (this.followReferencedCollection || this.readOnly || this.value[0] !== '__value__');
            }
        },
        methods: {
            validatePropertyComponent() {
                return this.validateField('value', (this.value[0] === '__value__') ||
                    (this.value.find(value => value === '') === undefined));
            },

            updateInput(new_value, index) {
                this.$emit('input', [index, new_value]);
            },
        },
    }
</script>