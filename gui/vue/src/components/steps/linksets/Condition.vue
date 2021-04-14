<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-center justify-content-between mb-2">
      <div class="col-auto">
        <fa-icon icon="chevron-down" size="lg" v-b-toggle="id"/>
      </div>

      <div class="col-auto mr-auto">
        <div class="input-group input-group-sm">
          <select-box v-model="condition.method.name" @input="handleMethodChange"
                      v-bind:class="{'is-invalid': errors.includes('method_name')}">
            <option disabled selected value="">Select a method</option>
            <option v-for="(method, methodName) in matchingMethods" :value="methodName">
              {{ method.description }}
            </option>
          </select-box>

          <div class="input-group-append">
            <div class="btn-group btn-group-toggle">
              <label v-if="method.items.length > 0" class="btn btn-secondary btn-sm"
                     v-bind:class="{'active': configureMatching}" @click="configureMatching = !configureMatching">
                Configure
              </label>

              <label v-if="allowFuzzyLogic" class="btn btn-secondary btn-sm"
                     v-bind:class="{'active': configureFuzzyLogic}" @click="configureFuzzyLogic = !configureFuzzyLogic">
                Configure fuzzy logic
              </label>

              <label v-if="method.items.length > 0 && method.acceptsSimilarityMethod" class="btn btn-secondary btn-sm"
                     v-bind:class="{'active': applySimMethod}">
                <input type="checkbox" autocomplete="off" v-model="applySimMethod"/>
                Apply similarity method
              </label>

              <label class="btn btn-secondary btn-sm" v-bind:class="{'active': applyListMatching}">
                <input type="checkbox" autocomplete="off" v-model="applyListMatching"/>
                Apply list matching
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="col-auto">
        <button-delete @click="$emit('remove')" title="Delete this method" class="pt-1 pr-0"/>
      </div>

      <div class="col-auto">
        <button-add v-on:click="$emit('add')" title="Add method and create group"/>
      </div>
    </div>

    <condition-configuration
        v-if="showConfiguration" :id="id" :condition="condition" :method="method" :sim-method="simMethod"
        :use-fuzzy-logic="allowFuzzyLogic" :configure-matching="configureMatching"
        :configure-fuzzy-logic="configureFuzzyLogic" :apply-sim-method="applySimMethod"
        :apply-list-matching="applyListMatching"
        @sim-method-change="handleSimMethodChange" ref="conditionConfiguration"/>

    <b-collapse :id="id" :visible="visible">
      <sub-card v-for="key in ['sources', 'targets']"
                :key="key" :label="key === 'sources' ? 'Source' : 'Target'" size="sm">
        <div class="row pl-3 pt-3">
          <div class="col">
            <div class="row my-2">
              <div class="h5 col-auto m-0">Properties</div>

              <div v-if="unusedEntityTypeSelections[key].length > 0" class="col-auto form-group">
                <select-box @input="addProperty(key, $event, -1)">
                  <option value="" disabled selected>Add property for entity-type selection:</option>
                  <option v-for="entityTypeSelection in unusedEntityTypeSelections[key]" :value="entityTypeSelection">
                    {{ $root.getEntityTypeSelectionById(entityTypeSelection).label }}
                  </option>
                </select-box>
              </div>
            </div>

            <template v-for="(conditionProperties, etsId, etsIdx) in condition[key].properties">
              <condition-property v-for="(conditionProperty, index) in conditionProperties"
                                  :key="etsIdx + '_' + index" :id="`${id}_${key}_${etsIdx}_${index}`"
                                  :entity-type-selection="$root.getEntityTypeSelectionById(etsId)"
                                  :condition-property="conditionProperty"
                                  :allow-delete="index > 0"
                                  :is-first="etsIdx === 0 && index === 0"
                                  @clone="addProperty(key, etsId, index)"
                                  @delete="condition[key].properties[etsId].splice(index, 1)"
                                  ref="conditionProperties"/>
            </template>

            <div class="invalid-feedback mb-2" v-bind:class="{'is-invalid': errors.includes(key)}">
              Please specify at least one property
            </div>

            <div class="row my-2">
              <div class="h5 col-auto m-0">Transformers</div>

              <div class="col-auto p-0">
                <button-add @click="addTransformer(key, $event)" title="Add transformer" size="sm"/>
              </div>
            </div>

            <div class="ml-4">
              <div class="col-auto">
                <div v-if="condition[key].transformers.length === 0" class="row align-items-center mb-1">
                  <div class="col-auto pr-0 form-inline font-italic">
                    No transformers added
                  </div>
                </div>

                <draggable v-model="condition[key].transformers" :group="`transformers_${id}_${key}`" handle=".handle">
                  <transformer v-for="(transformer, idx) in condition[key].transformers" :key="idx"
                               :id="`${id}_${key}_${idx}`" :transformer="transformer"
                               @remove="condition[key].transformers.splice(idx, 1)" ref="transformers"/>
                </draggable>
              </div>
            </div>
          </div>
        </div>
      </sub-card>
    </b-collapse>
  </div>
</template>

<script>
    import Draggable from 'vuedraggable';

    import props from "@/utils/props";
    import ValidationMixin from "@/mixins/ValidationMixin";

    import ConditionConfiguration from "./ConditionConfiguration";
    import ConditionProperty from "./ConditionProperty";
    import Transformer from "./Transformer";

    export default {
        name: "Condition",
        components: {
            Draggable,
            ConditionConfiguration,
            ConditionProperty,
            Transformer,
        },
        mixins: [ValidationMixin],
        data() {
            return {
                visible: true,
                configureMatching: true,
                configureFuzzyLogic: false,
                applySimMethod: false,
                applyListMatching: false,
                matchingMethods: props.matchingMethods,
            };
        },
        props: {
            id: String,
            condition: Object,
            useFuzzyLogic: Boolean,
        },
        computed: {
            method() {
                if (this.condition.method.name && this.matchingMethods.hasOwnProperty(this.condition.method.name))
                    return this.matchingMethods[this.condition.method.name];

                return {description: '', acceptSimilarityMethod: false, isSimilarityMethod: false, items: []};
            },

            simMethod() {
                if (this.condition.sim_method.name && this.matchingMethods.hasOwnProperty(this.condition.sim_method.name))
                    return this.matchingMethods[this.condition.sim_method.name];

                return {description: '', acceptSimilarityMethod: false, isSimilarityMethod: false, items: []};
            },

            allowFuzzyLogic() {
                return this.useFuzzyLogic && (this.method.isSimilarityMethod || this.simMethod.isSimilarityMethod);
            },

            unusedEntityTypeSelections() {
                const entityTypeSelectionKeys = ['sources', 'targets'];
                const unusedEntityTypeSelections = {};

                entityTypeSelectionKeys.forEach(key => {
                    unusedEntityTypeSelections[key] = Object.keys(this.condition[key].properties)
                        .filter(id => this.condition[key].properties[id].length < 1);
                });

                return unusedEntityTypeSelections;
            },

            showConfiguration() {
                return (this.configureMatching && this.method.items.length > 0) ||
                    (this.allowFuzzyLogic && this.configureFuzzyLogic) ||
                    (this.applySimMethod && this.method.items.length > 0 && this.method.acceptsSimilarityMethod) ||
                    this.applyListMatching;
            },
        },
        methods: {
            validateCondition() {
                const methodNameValid = this.validateField('method_name', this.condition.method.name);
                const configValid = this.$refs.conditionConfiguration
                    ? this.$refs.conditionConfiguration.validateConditionConfiguration() : true;

                const sourcesValid = this.validateField('sources',
                    Object.keys(this.condition.sources).length > 0);
                const targetsValid = this.validateField('targets',
                    Object.keys(this.condition.targets).length > 0);

                const conditionPropertiesValid = this.$refs.conditionProperties
                    ? !this.$refs.conditionProperties
                        .map(propertyComponent => propertyComponent.validateConditionProperty())
                        .includes(false)
                    : true;

                const transformersValid = this.$refs.transformers
                    ? !this.$refs.transformers
                        .map(transformer => transformer.validateTransformer())
                        .includes(false)
                    : true;

                return methodNameValid && configValid && sourcesValid && targetsValid
                    && conditionPropertiesValid && transformersValid;
            },

            handleMethodChange() {
                this.$set(this.condition.method, 'config', {});
                this.$set(this.condition.sim_method, 'name', null);
                this.$set(this.condition.sim_method, 'config', {});
                this.method.items.forEach(item =>
                    this.$set(this.condition.method.config, item.key, item.defaultValue));
            },

            handleSimMethodChange() {
                this.$set(this.condition.sim_method, 'config', {});
                this.simMethod.items.forEach(item =>
                    this.$set(this.condition.sim_method.config, item.key, item.defaultValue));
            },

            addProperty(key, etsId, index) {
                this.condition[key].properties[etsId].splice(index + 1, 0, {
                    property: [''],
                    transformers: [],
                });
            },

            addTransformer(key, name = '') {
                this.condition[key].transformers.push({name, parameters: {}});
            },

            getTransformerTemplate(key, transformer) {
                if (this.condition[key].transformers.hasOwnProperty(transformer.name))
                    return this.transformers[transformer.name];

                return {label: '', items: []};
            },

            handleTransformerIndexChange(key, transformer) {
                transformer.parameters = {};
                this.getTransformerTemplate(key, transformer).items.forEach(valueItem => {
                    transformer.parameters[valueItem.key] = valueItem.defaultValue;
                });
            },
        },
        mounted() {
            this.applySimMethod = !!this.condition.sim_method.name;
            this.applyListMatching = this.condition.list_matching.threshold > 0;
        },
        watch: {
            applySimMethod() {
                if (!this.applySimMethod) {
                    this.condition.sim_method.name = null;
                    this.condition.sim_method.config = {};
                }
            },
            applyListMatching() {
                if (!this.applyListMatching) {
                    this.condition.list_matching.threshold = 0;
                    this.condition.list_matching.is_percentage = false;
                }
            },
        },
    };
</script>