<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-start justify-content-between mb-2">
      <div class="col-auto">
        <div class="row">
          <label class="h4 col-auto">Method</label>

          <div class="col-auto">
            <v-select v-model="condition.method_name" @input="handleMethodIndexChange"
                      v-bind:class="{'is-invalid': errors.includes('method_name')}">
              <option disabled selected value="">Select a method</option>
              <option v-for="(method, name) in matchingMethods" :value="name">{{ method.label }}</option>
            </v-select>

            <div class="invalid-feedback" v-show="errors.includes('method_name')">
              Please specify a matching method
            </div>
          </div>
        </div>
      </div>

      <div class="col-4">
        <div class="row">
          <div v-for="(item, index) in methodValueTemplate.items" class="col">
            <div class="form-group">
              <label>
                                <span>
                                    {{ item.label }}
                                </span>

                <input v-if="typeof item.type === 'number'"
                       class="form-control" type="number" step="0.1"
                       v-model.number="condition.method_value[item.key]"
                       v-bind:class="{'is-invalid': errors.includes(`method_value_${item.key}`)}">

                <select v-if="item.type.hasOwnProperty('type') && item.type.type === 'matching_label'"
                        class="form-control" v-model="condition.method_value[item.key].value"
                        v-bind:class="{'is-invalid': errors.includes(`method_value_${item.key}`)}">
                  <option disabled selected value="">Select a Mapping</option>
                  <option v-for="match in $root.matches" :value="match.id">{{ match.label }}</option>
                </select>

                <select v-if="item.choices"
                        class="form-control" v-model="condition.method_value[item.key]"
                        v-bind:class="{'is-invalid': errors.includes(`method_value_${item.key}`)}">
                  <option disabled selected value="">Select an option</option>
                  <option v-for="(choice_value, choice_label) in item.choices"
                          :value="choice_value">{{ choice_label }}
                  </option>
                </select>

                <div class="invalid-feedback" v-show="errors.includes(`method_value_${item.key}`)">
                  Please specify a valid value
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="col-auto">
        <div class="row">
          <div class="col-auto">
            <button-delete @click="$emit('remove', index)" title="Delete this Method" class="pt-1 pr-0"/>
          </div>

          <div class="col-auto">
            <button-add v-on:click="$emit('add')" title="Add Method and Create Group"/>
          </div>
        </div>
      </div>
    </div>

    <div class="row pl-5 mb-3" v-for="resources_key in ['sources', 'targets']">
      <div class="col">
        <div class="row">
          <div class="h4 col-auto">{{ resources_key | capitalize }} properties</div>
          <div v-if="unusedResources[resources_key].length > 0" class="col-auto form-group">
            <v-select @input="condition[resources_key][$event].push({'property': [$event, '']})">
              <option value="" disabled selected>Add property for Collection:</option>
              <option v-for="resource in unusedResources[resources_key]" :value="resource">
                {{ $root.getResourceById(resource).label }}
              </option>
            </v-select>
          </div>
        </div>
        <template v-for="collection_properties in condition[resources_key]">
          <div v-for="(resource, index) in collection_properties" class="row">
            <div class="col ml-5 p-3 border-top">
              <property
                  v-if="resource.property"
                  :property="resource.property"
                  @clone="collection_properties.splice(index + 1, 0, {'property': [collection_properties[index]['property'][0], '']})"
                  @delete="$delete(collection_properties, index)"
                  @resetProperty="resetProperty(collection_properties, index, $event)"
                  ref="propertyComponents"
              />

              <div class="row align-items-center">
                <div class="col-auto h5">Transformers</div>

                <div class="col-auto p-0">
                  <button-add @click="$utilities.getOrCreate($set, resource, 'transformers', []).push('')"
                              size="sm" title="Add Transformer" class="btn-sm"/>
                </div>

                <div v-for="(_, index) in resource.transformers" class="col-auto">
                  <div class="row align-items-center">
                    <div class="col-auto pr-0">
                      <v-select v-model="resource.transformers[index]"
                                v-bind:class="{'is-invalid': errors.includes(`${resources_key}_transformers`)}">
                        <option value="" selected disabled>Select a function</option>
                        <option v-for="av_transformer in transformers" :value="av_transformer">{{ av_transformer }}
                        </option>
                      </v-select>

                      <div class="invalid-feedback" v-show="errors.includes(`${resources_key}_transformers`)">
                        Please specify a transformer or remove the transformer
                      </div>
                    </div>

                    <div class="col-auto p-0">
                      <button-delete @click="resource.transformers.splice(index, 1)" size="sm" class="btn-sm"/>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <div class="invalid-feedback d-block">
          <template v-if="errors.includes(resources_key)">
            Please specify at least one property
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import ValidationMixin from "../../../mixins/ValidationMixin";
    import props from "../../../utils/props";

    export default {
        name: "MatchCondition",
        mixins: [ValidationMixin],
        data() {
            return {
                transformers: props.transformers,
                matchingMethods: props.matchingMethods,
            };
        },
        props: ['condition', 'index'],
        computed: {
            methodValueTemplate() {
                if (this.matchingMethods.hasOwnProperty(this.condition.method_name))
                    return this.matchingMethods[this.condition.method_name];

                return {label: '', items: []};
            },

            unusedResources() {
                let resource_keys = ['sources', 'targets'];
                let unused_resources = {};

                resource_keys.forEach(resource_key => {
                    unused_resources[resource_key] = Object.keys(this.condition[resource_key]).filter(
                        resource_id => this.condition[resource_key][resource_id].length < 1
                    );
                });

                return unused_resources;
            },
        },
        methods: {
            validateMatchCondition() {
                const methodNameValid = this.validateField('method_name', this.condition.method_name.length > 0);

                let methodValueValid = true;
                this.errors = this.errors.filter(err => !err.startsWith('method_value_'));
                this.methodValueTemplate.items.forEach(value_item => {
                    const value = this.condition.method_value[value_item.key];

                    let valueValid = true;
                    if (value_item.hasOwnProperty('minValue') && (isNaN(parseFloat(value)) || (parseFloat(value) < value_item.minValue)))
                        valueValid = false;
                    if (value_item.hasOwnProperty('maxValue') && (isNaN(parseFloat(value)) || (parseFloat(value) > value_item.maxValue)))
                        valueValid = false;
                    if (value_item.hasOwnProperty('choices') && !Object.values(value_item.choices).includes(value))
                        valueValid = false;
                    if ((this.condition.method_name === 'IS_IN_SET') && (value.value === undefined || value.value === ''))
                        valueValid = false;

                    if (!this.validateField(`method_value_${value_item.key}`, valueValid))
                        methodValueValid = false;
                });

                const propertiesValid = !this.$refs.propertyComponents
                    .map(propertyComponent => propertyComponent.validateProperty())
                    .includes(false);

                let sourcesTargetsValid = true;
                ['sources', 'targets'].forEach(resources_key => {
                    Object.keys(this.condition[resources_key]).forEach(resource_id => {
                        if (!this.validateField(resources_key, this.condition[resources_key][resource_id].length > 0))
                            sourcesTargetsValid = false;

                        this.condition[resources_key][resource_id].forEach(values => {
                            if (values.hasOwnProperty('transformers') && !this.validateField(
                                `${resources_key}_transformers`, !values.transformers.includes('')))
                                sourcesTargetsValid = false;
                        });
                    });
                });

                return methodNameValid && methodValueValid && propertiesValid && sourcesTargetsValid;
            },

            handleMethodIndexChange() {
                this.condition.method_value = {};
                this.methodValueTemplate.items.forEach(value_item => {
                    this.condition.method_value[value_item.key] = value_item.type;
                });
            },

            resetProperty(properties, resource_index, property_index) {
                let property = properties[resource_index].property;
                let new_property = property.slice(0, property_index);
                new_property.push('');
                if (new_property.length % 2 > 0) {
                    new_property.push('');
                }

                this.$set(properties[resource_index], 'property', new_property);
            },
        },
    }
</script>