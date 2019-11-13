<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-start justify-content-between mb-2">
      <div class="col-auto mr-auto">
        <div class="row">
          <label class="h4 col-auto">Method</label>

          <div class="col-auto">
            <select-box v-model="condition.method_name" @input="handleMethodIndexChange"
                        v-bind:class="{'is-invalid': errors.includes('method_name')}">
              <option disabled selected value="">Select a method</option>
              <option v-for="(method, name) in matchingMethods" :value="name">{{ method.label }}</option>
            </select-box>

            <div class="invalid-feedback" v-show="errors.includes('method_name')">
              Please specify a matching method
            </div>
          </div>
        </div>
      </div>

      <div class="col-auto">
        <div class="form-inline">
          <template v-for="item in methodValueTemplate.items">
            <label class="small mr-2" v-if="item.label" :for="item.key + '_' + index">{{ item.label }}</label>

            <input v-if="typeof item.type === 'number'" :id="item.key + '_' + index"
                   class="form-control form-control-sm mr-2" type="number" step="0.1"
                   v-model.number="condition.method_value[item.key]"
                   v-bind:class="{'is-invalid': errors.includes(`method_value_${item.key}`)}">

            <select v-if="item.choices" :id="item.key + '_' + index"
                    class="form-control h-auto mr-2" v-model="condition.method_value[item.key]"
                    v-bind:class="{'is-invalid': errors.includes(`method_value_${item.key}`)}">
              <option disabled selected value="">Select an option</option>
              <option v-for="(choice_value, choice_label) in item.choices"
                      :value="choice_value">{{ choice_label }}
              </option>
            </select>

            <div class="invalid-feedback" v-show="errors.includes(`method_value_${item.key}`)">
              Please specify a valid value
            </div>
          </template>
        </div>
      </div>

      <div class="col-auto ml-auto">
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

    <sub-card v-if="['=', 'LEVENSHTEIN'].includes(condition.method_name)" class="max-overflow small mb-4">
      <exact-match-info v-if="condition.method_name === '='"/>
      <levenshtein-info v-else-if="condition.method_name === 'LEVENSHTEIN'"/>
    </sub-card>

    <div class="row pl-5 mb-3" v-for="resourcesKey in ['sources', 'targets']">
      <div class="col">
        <div class="row">
          <div class="h4 col-auto">{{ resourcesKey | capitalize }} properties</div>
          <div v-if="unusedResources[resourcesKey].length > 0" class="col-auto form-group">
            <select-box @input="condition[resourcesKey][$event].push({'property': [$event, '']})">
              <option value="" disabled selected>Add property for Collection:</option>
              <option v-for="resource in unusedResources[resourcesKey]" :value="resource">
                {{ $root.getResourceById(resource).label }}
              </option>
            </select-box>
          </div>
        </div>

        <template v-for="collectionProperties in condition[resourcesKey]">
          <div v-for="(resource, index) in collectionProperties" class="row">
            <div class="col ml-5 p-3 border-top">
              <property
                  v-if="resource.property"
                  :property="resource.property"
                  @clone="collectionProperties.splice(index + 1, 0, {property: [collectionProperties[index]['property'][0], ''], transformers: []})"
                  @delete="$delete(collectionProperties, index)"
                  @resetProperty="resetProperty(collectionProperties, index, $event)"
                  ref="propertyComponents"/>

              <div class="row align-items-top mt-2">
                <div class="col-auto h5">Transformers</div>

                <div class="col-auto p-0 pb-1">
                  <button-add @click="addTransformer(resource)" size="sm" title="Add Transformer" class="btn-sm"/>
                </div>

                <div class="col-auto">
                  <div v-for="transformer in resource.transformers" class="row align-items-center mb-1">
                    <div class="col-auto pr-0 form-inline">
                      <select-box v-model="transformer.name" @input="handleTransformerIndexChange(transformer)"
                                  v-bind:class="{'is-invalid': errors.includes(`transformer_${resourcesKey}_${index}`)}">
                        <option disabled selected value="">Select a transformer</option>
                        <option v-for="(obj, name) in transformers" :value="name">{{ obj.label }}</option>
                      </select-box>

                      <div class="invalid-feedback inline-feedback ml-2"
                           v-show="errors.includes(`transformer_${resourcesKey}_${index}`)">
                        Please specify a transformer or remove the transformer
                      </div>
                    </div>

                    <div v-if="getTransformerTemplate(transformer).items.length > 0" class="col-auto pr-0 form-inline">
                      <template v-for="item in getTransformerTemplate(transformer).items">
                        <label class="small mr-2" v-if="item.label"
                               :for="`transformer_${resourcesKey}_${index}_${item.key}`">
                          {{ item.label }}
                        </label>

                        <input :id="`transformer_${resourcesKey}_${index}_${item.key}`"
                               class="form-control form-control-sm mr-2" v-model="transformer.parameters[item.key]"
                               v-bind:class="{'is-invalid': errors.includes(`transformer_value_${resourcesKey}_${index}_${item.key}`)}">

                        <div class="invalid-feedback inline-feedback"
                             v-show="errors.includes(`transformer_value_${resourcesKey}_${index}_${item.key}`)">
                          Please specify a valid value
                        </div>
                      </template>
                    </div>

                    <div class="col-auto p-0 pb-1 ml-2">
                      <button-delete @click="resource.transformers.splice(index, 1)" size="sm" class="btn-sm"/>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <div class="invalid-feedback d-block">
          <template v-if="errors.includes(resourcesKey)">
            Please specify at least one property
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import ExactMatchInfo from "../../info/ExactMatchInfo";
    import LevenshteinInfo from "../../info/LevenshteinInfo";

    import props from "../../../utils/props";
    import ValidationMixin from "../../../mixins/ValidationMixin";

    export default {
        name: "MatchCondition",
        components: {
            ExactMatchInfo,
            LevenshteinInfo,
        },
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
                const resourceKeys = ['sources', 'targets'];
                const unusedResources = {};

                resourceKeys.forEach(resourceKey => {
                    unusedResources[resourceKey] = Object.keys(this.condition[resourceKey]).filter(
                        resource_id => this.condition[resourceKey][resource_id].length < 1
                    );
                });

                return unusedResources;
            },
        },
        methods: {
            validateMatchCondition() {
                const methodNameValid = this.validateField('method_name', this.condition.method_name.length > 0);

                let methodValueValid = true;
                this.errors = this.errors.filter(err => !err.startsWith('method_value_'));
                this.methodValueTemplate.items.forEach(valueItem => {
                    const value = this.condition.method_value[valueItem.key];

                    let valueValid = true;
                    if (valueItem.hasOwnProperty('minValue') && (isNaN(parseFloat(value)) || (parseFloat(value) < valueItem.minValue)))
                        valueValid = false;
                    if (valueItem.hasOwnProperty('maxValue') && (isNaN(parseFloat(value)) || (parseFloat(value) > valueItem.maxValue)))
                        valueValid = false;
                    if (valueItem.hasOwnProperty('choices') && !Object.values(valueItem.choices).includes(value))
                        valueValid = false;
                    if ((this.condition.method_name === 'IS_IN_SET') && (value === undefined || value === ''))
                        valueValid = false;

                    if (!this.validateField(`method_value_${valueItem.key}`, valueValid))
                        methodValueValid = false;
                });

                const propertiesValid = !this.$refs.propertyComponents
                    .map(propertyComponent => propertyComponent.validateProperty())
                    .includes(false);

                let sourcesTargetsValid = true;
                this.errors = this.errors.filter(err => !err.startsWith('transformer_'));
                ['sources', 'targets'].forEach(resourcesKey => {
                    Object.keys(this.condition[resourcesKey]).forEach(resourceId => {
                        if (!this.validateField(resourcesKey, this.condition[resourcesKey][resourceId].length > 0))
                            sourcesTargetsValid = false;

                        this.condition[resourcesKey][resourceId].forEach(values => {
                            if (values.hasOwnProperty('transformers')) {
                                values.transformers.forEach(transformer => {
                                    if (!this.validateField(`transformer_${resourcesKey}_${resourceId}`,
                                        transformer.name && transformer.name.length > 0)) {
                                        sourcesTargetsValid = false;
                                    }
                                    else {
                                        this.getTransformerTemplate(transformer).items.forEach(transformerItem => {
                                            const field = `transformer_value_${resourcesKey}_${resourceId}_${transformerItem.key}`;
                                            const value = transformer.parameters[transformerItem.key];
                                            if (!this.validateField(field, value && value.length > 0))
                                                sourcesTargetsValid = false;
                                        });
                                    }
                                });
                            }
                        });
                    });
                });

                return methodNameValid && methodValueValid && propertiesValid && sourcesTargetsValid;
            },

            handleMethodIndexChange() {
                this.condition.method_value = {};
                this.methodValueTemplate.items.forEach(valueItem => {
                    this.condition.method_value[valueItem.key] = valueItem.type;
                });
            },

            addTransformer(resource) {
                if (!resource.hasOwnProperty('transformers'))
                    resource.transformers = [];

                resource.transformers.push({
                    name: '',
                    parameters: {},
                })
            },

            getTransformerTemplate(transformer) {
                if (this.transformers.hasOwnProperty(transformer.name))
                    return this.transformers[transformer.name];

                return {label: '', items: []};
            },

            handleTransformerIndexChange(transformer) {
                transformer.parameters = {};
                this.getTransformerTemplate(transformer).items.forEach(valueItem => {
                    transformer.parameters[valueItem.key] = valueItem.type;
                });
            },

            resetProperty(properties, resourceIndex, propertyIndex) {
                const property = properties[resourceIndex].property;
                const newProperty = property.slice(0, propertyIndex);

                newProperty.push('');
                if (newProperty.length % 2 > 0)
                    newProperty.push('');

                this.$set(properties[resourceIndex], 'property', newProperty);
            },
        },
    };
</script>