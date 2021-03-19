<template>
  <div class="border border-dark p-3 mt-3">
    <div class="row align-items-center justify-content-between mb-2">
      <label class="h5 col-auto">Method</label>

      <div class="col-auto mr-auto">
        <div class="input-group input-group-sm">
          <select-box v-model="condition.method_name" @input="handleMethodChange"
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
                     v-bind:class="{'active': configureTConorms}" @click="configureTConorms = !configureTConorms">
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
        <button-delete @click="$emit('remove', index)" title="Delete this Method" class="pt-1 pr-0"/>
      </div>

      <div class="col-auto">
        <button-add v-on:click="$emit('add')" title="Add Method and Create Group"/>
      </div>
    </div>

    <condition-configuration :id="id" :condition="condition" :method="method" :sim-method="simMethod"
                             :use-fuzzy-logic="allowFuzzyLogic" :configure-matching="configureMatching"
                             :configure-t-conorms="configureTConorms" :apply-sim-method="applySimMethod"
                             :apply-list-matching="applyListMatching" @sim-method-change="handleSimMethodChange"
                             ref="conditionConfiguration"/>

    <div v-for="key in ['sources', 'targets']" class="row pl-5">
      <div class="col">
        <div class="row">
          <div v-if="key === 'sources'" class="h4 col-auto">Source properties</div>
          <div v-else class="h4 col-auto">Target properties</div>

          <div v-if="unusedEntityTypeSelections[key].length > 0" class="col-auto form-group">
            <select-box @input="addProperty(key, $event, -1)">
              <option value="" disabled selected>Add property for Entity-type selection:</option>
              <option v-for="entityTypeSelection in unusedEntityTypeSelections[key]" :value="entityTypeSelection">
                {{ $root.getEntityTypeSelectionById(entityTypeSelection).label }}
              </option>
            </select-box>
          </div>
        </div>

        <template v-for="(conditionProperties, etsId, etsIdx) in condition[key]">
          <condition-property v-for="(conditionProperty, index) in conditionProperties"
                              :key="etsIdx + '_' + index"
                              :entity-type-selection="$root.getEntityTypeSelectionById(etsId)"
                              :condition-property="conditionProperty"
                              :allow-delete="index > 0"
                              :is-first="etsIdx === 0 && index === 0"
                              @clone="addProperty(key, etsId, index)"
                              @delete="condition[key][etsId].splice(index, 1)"
                              ref="conditionProperties"/>
        </template>

        <div class="invalid-feedback mb-2" v-bind:class="{'is-invalid': errors.includes(key)}">
          Please specify at least one property
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import props from "@/utils/props";
    import ValidationMixin from "@/mixins/ValidationMixin";

    import ConditionConfiguration from "./ConditionConfiguration";
    import ConditionProperty from "./ConditionProperty";

    export default {
        name: "Condition",
        components: {
            ConditionConfiguration,
            ConditionProperty,
        },
        mixins: [ValidationMixin],
        data() {
            return {
                configureMatching: true,
                configureTConorms: false,
                applySimMethod: false,
                applyListMatching: false,
                transformers: props.transformers,
                matchingMethods: props.matchingMethods,
            };
        },
        props: {
            id: String,
            index: Number,
            condition: Object,
            useFuzzyLogic: Boolean,
        },
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

            allowFuzzyLogic() {
                return this.useFuzzyLogic && (this.method.isSimilarityMethod || this.simMethod.isSimilarityMethod);
            },

            unusedEntityTypeSelections() {
                const entityTypeSelectionKeys = ['sources', 'targets'];
                const unusedEntityTypeSelections = {};

                entityTypeSelectionKeys.forEach(key => {
                    unusedEntityTypeSelections[key] =
                        Object.keys(this.condition[key]).filter(id => this.condition[key][id].length < 1);
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
                const configValid = this.$refs.conditionConfiguration.validateConditionConfiguration();

                const sourcesValid = this.validateField('sources',
                    Object.keys(this.condition.sources).length > 0);
                const targetsValid = this.validateField('targets',
                    Object.keys(this.condition.targets).length > 0);

                const conditionPropertiesValid = !this.$refs.conditionProperties
                    .map(propertyComponent => propertyComponent.validateConditionProperty())
                    .includes(false);

                return methodNameValid && configValid && sourcesValid && targetsValid && conditionPropertiesValid;
            },

            handleMethodChange() {
                this.$set(this.condition, 'method_config', {});
                this.$set(this.condition, 'method_sim_name', null);
                this.$set(this.condition, 'method_sim_config', {});
                this.method.items.forEach(item =>
                    this.$set(this.condition.method_config, item.key, item.defaultValue));
            },

            handleSimMethodChange() {
                this.$set(this.condition, 'method_sim_config', {});
                this.simMethod.items.forEach(item =>
                    this.$set(this.condition.method_sim_config, item.key, item.defaultValue));
            },

            addProperty(key, etsId, index) {
                this.condition[key][etsId].splice(index + 1, 0, {
                    property: [''],
                    transformers: [],
                    stopwords: {
                        dictionary: '',
                        additional: []
                    }
                });
            },
        },
        mounted() {
            this.applySimMethod = !!this.condition.method_sim_name;
            this.applyListMatching = this.condition.list_matching.links_threshold > 0
                || this.condition.list_matching.source_threshold > 0
                || this.condition.list_matching.target_threshold > 0;
        },
        watch: {
            applySimMethod() {
                if (!this.applySimMethod) {
                    this.condition.method_sim_name = null;
                    this.condition.method_sim_config = {};
                }
            },
            applyListMatching() {
                if (!this.applyListMatching) {
                    this.condition.list_matching.links_threshold = 0;
                    this.condition.list_matching.links_is_percentage = false;
                    this.condition.list_matching.source_threshold = 0;
                    this.condition.list_matching.source_is_percentage = false;
                    this.condition.list_matching.target_threshold = 0;
                    this.condition.list_matching.target_is_percentage = false;
                }
            },
        },
    };
</script>