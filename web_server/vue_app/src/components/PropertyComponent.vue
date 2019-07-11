<template>
  <div class="col-auto">
    <div class="row align-items-center">
      <div v-if="showReferencedPropertyButton" class="col-auto p-1">
        <octicon name="arrow-right"/>
      </div>

      <div v-if="selectReferencedCollection || showResourceInfo || showReferencedPropertyButton" class="col-auto">
        <div v-if="selectReferencedCollection" class="row align-items-center">
          <v-select :value="value[0]" @input="updateInput($event, 0)" class="my-1"
                    v-bind:class="{'is-invalid': errors.includes('value')}">
            <template v-if="Array.isArray(resources)">
              <option v-for="collection in resources" :key="collection.id" :value="collection.id">{{ collection.label }}
              </option>
            </template>
            <template v-else>
              <option value="" disabled selected>Choose a referenced collection</option>
              <option value="__value__">Value (do not follow reference)</option>
              <option v-for="collection in Object.keys(resources)" :key="collection" :value="collection">{{ collection
                }}
              </option>
            </template>
          </v-select>
        </div>

        <div v-else-if="showResourceInfo" class="row align-items-center">
          <div class="col-auto border border-info p-1 rounded-pill my-1 pl-2 pr-2 bg-white">
            {{ $root.datasets[$root.getResourceById(value[0], resources).dataset_id].title }}
          </div>
          <div class="col-auto border border-info p-1 rounded-pill my-1 ml-2 mr-2 pl-2 pr-2 bg-white">
            {{ $root.getResourceById(value[0], resources).collection_id }}
          </div>

          <div class="col-auto ml-0 pl-0" v-if="!singular">
            <button-add
                @click="$emit('clone')"
                :scale="0.8"
                title="Add another property for this Collection"/>
            <button-delete @click="$emit('delete')" scale="1.3" title="Remove this property"/>
          </div>
        </div>

        <div v-else-if="showReferencedPropertyButton" class="row align-items-center">
          <button type="button" class="btn-info btn col-auto my-1 pb-0 pt-0 rounded-pill" @click="$emit('reset', 0)">
            {{ value[0] }}
          </button>
        </div>
      </div>

      <template v-if="value[0] && value[0] !== '__value__'">
        <div v-if="!Array.isArray(resources)" class="col-auto p-1">
          <octicon name="arrow-right"/>
        </div>
        <div class="col-auto">
          <div class="row align-items-center">
            <template v-if="!value[1]">
              <v-select class="col-auto my-1" :value="value[1]" @input="updateInput($event, 1)"
                        v-bind:class="{'is-invalid': errors.includes('value')}">
                <option value="" selected disabled>Choose a property</option>
                <option v-for="property_opt in Object.keys(properties)" :value="property_opt">{{ property_opt }}
                </option>
              </v-select>
            </template>
            <button v-else type="button" class="my-1 col-auto btn-info btn pb-0 pt-0 rounded-pill"
                    @click="$emit('reset', 1)">
              {{ value[1] }}
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
<script>
    import ValidationMixin from "../mixins/ValidationMixin";

    export default {
        name: 'propertyComponent',
        mixins: [ValidationMixin],
        props: {
            properties: Object,
            resources: [Array, Object],
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
                return !this.value[0];
            },

            showResourceInfo() {
                return Array.isArray(this.resources) && (!this.singular || this.singularResourceInfo);
            },

            showReferencedPropertyButton() {
                return !Array.isArray(this.resources) && (this.followReferencedCollection || this.value[0] !== '__value__');
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