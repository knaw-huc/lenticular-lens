<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-start justify-content-between mb-2">
      <div class="col-auto mr-auto">
        <div class="row">
          <label class="h4 col-auto">Method</label>

          <div class="col-auto">
            <select-box v-model="condition.method_name" @input="handleMethodChange"
                        v-bind:class="{'is-invalid': errors.includes('method_name')}">
              <option disabled selected value="">Select a method</option>
              <option v-for="(method, methodName) in matchingMethods" :value="methodName">
                {{ method.description }}
              </option>
            </select-box>

            <div class="invalid-feedback" v-show="errors.includes('method_name')">
              Please specify a matching method
            </div>
          </div>
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

    <div class="row pl-5">
      <div class="col">
        <div class="row">
          <div class="h4 col-auto">Configuration</div>
        </div>

        <div class="my-3 ml-5">
          <div class="form-group row">
            <div class="col">
              <div class="form-check">
                <input class="form-check-input" type="checkbox"
                       :id="'list_matching_' + index" v-model="useListMatching" @change="handleListMatchingChange">
                <label class="form-check-label" :for="'list_matching_' + index">
                  Apply list matching?
                </label>
              </div>
            </div>
          </div>

          <div v-if="useListMatching" class="form-group row">
            <label :for="'list_threshold_' + index" class="col-sm-3 col-form-label">
              Minimum matches
            </label>

            <div class="col-sm-1">
              <input :id="'list_threshold_' + index" class="form-control form-control-sm"
                     type="number" step="1"
                     v-model.number="condition.list_threshold"
                     v-bind:class="{'is-invalid': errors.includes('list_threshold')}">

              <div class="invalid-feedback" v-show="errors.includes('list_threshold')">
                Please specify a valid value
              </div>
            </div>

            <div class="col-sm-1">
              <div class="form-check">
                <input class="form-check-input" type="radio" :id="'list_threshold_items_' + index"
                       v-model="condition.list_threshold_unit" value="matches">
                <label class="form-check-label" :for="'list_threshold_items_' + index">
                  matches
                </label>
              </div>
            </div>

            <div class="col-sm-1">
              <div class="form-check">
                <input class="form-check-input" type="radio" :id="'list_threshold_percentage_' + index"
                       v-model="condition.list_threshold_unit" value="percentage">
                <label class="form-check-label" :for="'list_threshold_percentage_' + index">
                  %
                </label>
              </div>
            </div>
          </div>

          <template v-if="method.items.length > 0">
            <condition-method :method="method" :condition="condition" config-key="method_config" ref="methodConfig"/>

            <div v-if="method.acceptsSimilarityMethod" class="form-group row">
              <label :for="'sim_method_' + index" class="col-sm-3 col-form-label">
                Apply similarity method
              </label>

              <div class="col-sm-3">
                <select :id="'sim_method_' + index" class="form-control form-control-sm"
                        v-model="condition.method_sim_name" @change="handleSimMethodChange">
                  <option :value="null">No similarity method</option>
                  <option v-for="(method, methodName) in similarityMethods" :value="methodName">
                    {{ method.description }}
                  </option>
                </select>
              </div>
            </div>

            <condition-method v-if="simMethod.items.length > 0"
                              :method="simMethod" :condition="condition" config-key="method_sim_config"
                              ref="methodSimConfig"/>

            <div v-if="condition.method_sim_name" class="form-group row">
              <div class="col">
                <div class="form-check">
                  <input class="form-check-input" type="checkbox"
                         :id="'method_sim_normalized_' + index" v-model="condition.method_sim_normalized">
                  <label class="form-check-label" :for="'method_sim_normalized_' + index">
                    Apply similarity method on normalized value?
                  </label>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!--        <div class="mt-2 mb-4 ml-5 pt-2 border-top">-->
        <!--          <div class="form-group row">-->
        <!--            <label :for="'t_conorm_' + index" class="col-sm-3 col-form-label">-->
        <!--              T-conorm-->
        <!--            </label>-->

        <!--            <div class="col-sm-3">-->
        <!--              <select :id="'t_conorm_' + index" class="form-control form-control-sm" v-model="condition.t_conorm">-->
        <!--                <option v-for="(description, key) in tConorms" :value="key">-->
        <!--                  {{ description }}-->
        <!--                </option>-->
        <!--              </select>-->
        <!--            </div>-->
        <!--          </div>-->
        <!--        </div>-->
      </div>
    </div>

    <div v-for="key in ['sources', 'targets']" class="row pl-5">
      <div class="col">
        <div class="row">
          <div class="h4 col-auto">{{ key | capitalize }} properties</div>
          <div v-if="unusedEntityTypeSelections[key].length > 0" class="col-auto form-group">
            <select-box @input="condition[key][$event].push({'property': [$event, '']})">
              <option value="" disabled selected>Add property for Entity-type selection:</option>
              <option v-for="entityTypeSelection in unusedEntityTypeSelections[key]" :value="entityTypeSelection">
                {{ $root.getEntityTypeSelectionById(entityTypeSelection).label }}
              </option>
            </select-box>
          </div>
        </div>

        <condition-property v-for="(conditionProperty, index) in condition[key]"
                            :key="index" :condition-property="conditionProperty"
                            :allow-delete="allowDeleteForIndex(index, conditionProperty, key)"
                            :is-first="index === 0"
                            @clone="cloneProperty(key, index, conditionProperty)"
                            @delete="condition[key].splice(index, 1)"
                            ref="conditionProperties"/>

        <div class="invalid-feedback mb-2" v-bind:class="{'is-invalid': errors.includes(key)}">
          Please specify at least one property
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import props from "../../../utils/props";
    import ValidationMixin from "../../../mixins/ValidationMixin";

    import ConditionMethod from "./ConditionMethod";
    import ConditionProperty from "./ConditionProperty";

    export default {
        name: "Condition",
        components: {
            ConditionMethod,
            ConditionProperty,
        },
        mixins: [ValidationMixin],
        data() {
            return {
                useListMatching: false,
                tConorms: props.tConorms,
                transformers: props.transformers,
                matchingMethods: props.matchingMethods,
                similarityMethods: Object.keys(props.matchingMethods)
                    .filter(key => props.matchingMethods[key].isSimilarityMethod)
                    .reduce((obj, key) => ({
                        ...obj,
                        [key]: props.matchingMethods[key]
                    }), {}),
            };
        },
        props: ['condition', 'index'],
        computed: {
            method() {
                if (this.condition.method_name && this.matchingMethods.hasOwnProperty(this.condition.method_name))
                    return this.matchingMethods[this.condition.method_name];

                return {description: '', acceptSimilarityMethod: false, isSimilarityMethod: false, items: []};
            },

            simMethod() {
                if (this.condition.method_sim_name && this.matchingMethods.hasOwnProperty(this.condition.method_sim_name))
                    return this.matchingMethods[this.condition.method_sim_name];

                return {description: '', acceptSimilarityMethod: false, isSimilarityMethod: false, items: []};
            },

            unusedEntityTypeSelections() {
                const entityTypeSelectionKeys = ['sources', 'targets'];
                const unusedEntityTypeSelections = {};

                entityTypeSelectionKeys.forEach(key => {
                    unusedEntityTypeSelections[key] = Object.keys(this.condition[key])
                        .filter(id => this.condition[key][id].length < 1);
                });

                return unusedEntityTypeSelections;
            },

            conditionProperties() {
                return this.condition['sources'].concat(this.condition['targets']);
            },
        },
        methods: {
            validateCondition() {
                const methodNameValid = this.validateField('method_name', this.condition.method_name);

                const methodConfigValid = this.validateField('method_config',
                    this.$refs.methodConfig ? this.$refs.methodConfig.validateConditionMethod() : true);
                const methodSimConfigValid = this.validateField('method_sim_config',
                    this.$refs.methodSimConfig ? this.$refs.methodSimConfig.validateConditionMethod() : true);

                const listThresholdValid = this.validateField('list_threshold',
                    !this.useListMatching || (this.condition.list_threshold > 0 &&
                    (this.condition.list_threshold_unit === 'matches' || this.condition.list_threshold <= 100)));

                const sourcesValid = this.validateField('sources', this.condition.sources.length > 0);
                const targetsValid = this.validateField('targets', this.condition.targets.length > 0);

                const conditionPropertiesValid = !this.$refs.conditionProperties
                    .map(propertyComponent => propertyComponent.validateConditionProperty())
                    .includes(false);

                return methodNameValid && methodConfigValid && methodSimConfigValid && listThresholdValid
                    && sourcesValid && targetsValid && conditionPropertiesValid;
            },

            handleMethodChange() {
                this.condition.method_config = {};
                this.condition.method_sim_name = null;
                this.condition.method_sim_config = {};
                this.method.items
                    .filter(item => item.hasOwnProperty('defaultValue'))
                    .forEach(item => this.condition.method_config[item.key] = item.defaultValue);
            },

            handleSimMethodChange() {
                this.condition.method_sim_config = {};
                this.simMethod.items
                    .filter(item => item.hasOwnProperty('defaultValue'))
                    .forEach(item => this.condition.method_sim_config[item.key] = item.defaultValue);
            },

            handleListMatchingChange() {
                this.condition.list_threshold = 0;
                this.condition.list_threshold_unit = 'matches';
            },

            getParametersForTransformer(transformer) {
                if (this.transformers.hasOwnProperty(transformer))
                    return this.transformers[transformer].items.reduce((acc, item) => {
                        acc[item.key] = item.type;
                        return acc;
                    }, {});

                return {};
            },

            allowDeleteForIndex(index, prop, key) {
                return this.condition[key]
                    .findIndex(p => p.entity_type_selection === prop.entity_type_selection) !== index;
            },

            cloneProperty(key, index, conditionProperty) {
                this.condition[key].splice(index + 1, 0, {
                    entity_type_selection: conditionProperty.entity_type_selection,
                    property: [''],
                    transformers: []
                });
            },
        },
        mounted() {
            this.useListMatching = !!this.condition.list_threshold;
        },
    };
</script>