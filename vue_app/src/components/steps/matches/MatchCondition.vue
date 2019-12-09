<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-start justify-content-between mb-2">
      <div class="col-auto mr-auto">
        <div class="row">
          <label class="h4 col-auto">Method</label>

          <div class="col-auto">
            <select-box v-model="condition.method_name" @input="handleMethodIndexChange"
                        v-bind:class="{'is-invalid': errors.includes('method_name') || errors.includes('transformers')}">
              <option disabled selected value="">Select a method</option>
              <option v-for="(method, name) in matchingMethods" :value="name">{{ method.label }}</option>
            </select-box>

            <div class="invalid-feedback" v-show="errors.includes('method_name')">
              Please specify a matching method
            </div>

            <div class="invalid-feedback" v-show="errors.includes('transformers')">
              Matching method '{{ methodValueTemplate.label }}' requires that all properties apply the transformer(s):
              {{ requiredTransformers.join(', ') }}
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

    <div v-for="resourcesKey in ['sources', 'targets']" class="row pl-5">
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

        <match-condition-property v-for="(conditionProperty, index) in condition[resourcesKey]"
                                  :key="index" :condition-property="conditionProperty"
                                  :allow-delete="allowDeleteForIndex(index, conditionProperty, resourcesKey)"
                                  @clone="cloneProperty(resourcesKey, index, conditionProperty)"
                                  @delete="condition[resourcesKey].splice(index, 1)"
                                  ref="matchConditionProperties"/>

        <div class="invalid-feedback mb-2" v-bind:class="{'is-invalid': errors.includes(resourcesKey)}">
          Please specify at least one property
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

    import MatchConditionProperty from "./MatchConditionProperty";

    export default {
        name: "MatchCondition",
        components: {
            ExactMatchInfo,
            LevenshteinInfo,
            MatchConditionProperty,
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

            conditionProperties() {
                return this.condition['sources'].concat(this.condition['targets']);
            },

            requiredTransformers() {
                if (!this.methodValueTemplate.hasOwnProperty('transformers'))
                    return [];

                return Object.entries(this.transformers)
                    .filter(([key]) => this.methodValueTemplate.transformers.includes(key))
                    .map(([_, transformer]) => transformer.label);
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

                const sourcesValid = this.validateField('sources', this.condition.sources.length > 0);
                const targetsValid = this.validateField('targets', this.condition.targets.length > 0);

                const matchConditionPropertiesValid = !this.$refs.matchConditionProperties
                    .map(propertyComponent => propertyComponent.validateMatchConditionProperty())
                    .includes(false);

                let transformersValid = true;
                if (this.methodValueTemplate.hasOwnProperty('transformers')) {
                    this.conditionProperties.forEach(conditionProperty => {
                        const transformers = conditionProperty.transformers.map(transformer => transformer.name);
                        this.methodValueTemplate.transformers.forEach(transformer => {
                            if (!transformers.includes(transformer))
                                transformersValid = false;
                        });
                    });
                }
                this.validateField('transformers', transformersValid);

                return methodNameValid && methodValueValid && sourcesValid && targetsValid
                    && matchConditionPropertiesValid && transformersValid;
            },

            handleMethodIndexChange() {
                this.condition.method_value = {};
                this.methodValueTemplate.items.forEach(valueItem => {
                    this.condition.method_value[valueItem.key] = valueItem.type;
                });

                if (this.methodValueTemplate.hasOwnProperty('transformers')) {
                    this.methodValueTemplate.transformers.forEach(transformer => {
                        this.conditionProperties.forEach(conditionProp => {
                            if (!conditionProp.hasOwnProperty('transformers'))
                                conditionProp.transformers = [];

                            if (!conditionProp.transformers.find(obj => obj.name === transformer))
                                conditionProp.transformers.push({
                                    name: transformer,
                                    parameters: this.getParametersForTransformer(transformer)
                                });
                        });
                    });
                }
            },

            getParametersForTransformer(transformer) {
                if (this.transformers.hasOwnProperty(transformer))
                    return this.transformers[transformer].items.reduce((acc, item) => {
                        acc[item.key] = item.type;
                        return acc;
                    }, {});

                return {};
            },

            allowDeleteForIndex(index, prop, resourcesKey) {
                return this.condition[resourcesKey].findIndex(p => p.resource === prop.resource) !== index;
            },

            cloneProperty(resourcesKey, index, conditionProperty) {
                const transformers = [];
                if (this.methodValueTemplate.hasOwnProperty('transformers'))
                    this.methodValueTemplate.transformers.forEach(transformer => {
                        transformers.push({
                            name: transformer,
                            parameters: this.getParametersForTransformer(transformer)
                        });
                    });

                this.condition[resourcesKey].splice(index + 1, 0, {
                    resource: conditionProperty.resource,
                    property: [''],
                    transformers
                });
            },
        },
    };
</script>