<template>
  <div class="row pl-5">
    <div class="col">
      <div class="my-3 ml-5">
        <condition-method v-if="configureMatching && method.items.length > 0" class="config-group"
                          :id="'method_' + id" :method="method" :condition="condition"
                          config-key="method_config" ref="methodConfig"/>

        <div v-if="useFuzzyLogic && configureTConorms" class="config-group">
          <div class="form-group row">
            <label :for="'t_conorm_' + id" class="col-sm-3 col-form-label">
              T-conorm
            </label>

            <div class="col-sm-3">
              <select :id="'t_conorm_' + id" class="form-control form-control-sm" v-model="condition.t_conorm">
                <option v-for="(description, key) in tConorms" :value="key">
                  {{ description }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-group row">
            <label :for="'threshold_' + id" class="col-sm-3 col-form-label">
              Threshold
            </label>

            <div class="col-sm-2">
              <range :id="'threshold_' + id" v-model.number="condition.threshold" :allow-zero="false"/>
            </div>
          </div>
        </div>

        <div v-if="applySimMethod && method.items.length > 0 && method.acceptsSimilarityMethod" class="config-group">
          <div class="form-group row">
            <label :for="'sim_method_' + id" class="col-sm-3 col-form-label">
              Apply similarity method
            </label>

            <div class="col-sm-3">
              <select :id="'sim_method_' + id" class="form-control form-control-sm"
                      v-bind:class="{'is-invalid': errors.includes('sim_method_name')}"
                      v-model="condition.method_sim_name" @change="$emit('sim-method-change', $event)">
                <option disabled selected value="">Select a similarity method</option>
                <option v-for="(method, methodName) in similarityMethods" :value="methodName">
                  {{ method.description }}
                </option>
              </select>
            </div>
          </div>

          <condition-method v-if="simMethod.items.length > 0" :id="'sim_method_' + id"
                            :method="simMethod" :condition="condition" config-key="method_sim_config"
                            ref="methodSimConfig"/>

          <div v-if="condition.method_sim_name" class="form-group row">
            <div class="col">
              <div class="form-check">
                <input class="form-check-input" type="checkbox"
                       :id="'method_sim_normalized_' + id" v-model="condition.method_sim_normalized">
                <label class="form-check-label" :for="'method_sim_normalized_' + id">
                  Apply similarity method on normalized value?
                </label>
              </div>
            </div>
          </div>
        </div>

        <div v-if="applyListMatching" class="config-group">
          <div class="form-group row">
            <label :for="'list_links_threshold_' + id" class="col-sm-3 col-form-label">
              Minimum matches
            </label>

            <div class="col-sm-1">
              <input :id="'list_links_threshold_' + id" class="form-control form-control-sm"
                     type="number" step="1"
                     v-model.number="condition.list_matching.links_threshold"
                     v-bind:class="{'is-invalid': errors.includes('links_threshold') || errors.includes('list_matching')}">
            </div>

            <div class="col-sm-1">
              <div class="form-check">
                <input class="form-check-input" type="radio" :id="'list_links_threshold_items_' + id"
                       v-model="condition.list_matching.links_is_percentage" :value="false">
                <label class="form-check-label" :for="'list_links_threshold_items_' + id">
                  matches
                </label>
              </div>
            </div>

            <div class="col-sm-1">
              <div class="form-check">
                <input class="form-check-input" type="radio" :id="'list_links_threshold_percentage_' + id"
                       v-model="condition.list_matching.links_is_percentage" :value="true">
                <label class="form-check-label" :for="'list_links_threshold_percentage_' + id">
                  %
                </label>
              </div>
            </div>

            <div class="col-auto" v-show="errors.includes('links_threshold')">
              <div class="invalid-feedback inline-feedback"
                   v-bind:class="{'is-invalid': errors.includes('links_threshold')}">
                Please specify a valid value
              </div>
            </div>
          </div>

          <div class="form-group row">
            <label :for="'list_source_threshold_' + id" class="col-sm-3 col-form-label">
              Minimum source values
            </label>

            <div class="col-sm-1">
              <input :id="'list_source_threshold_' + id" class="form-control form-control-sm"
                     type="number" step="1"
                     v-model.number="condition.list_matching.source_threshold"
                     v-bind:class="{'is-invalid': errors.includes('source_threshold') || errors.includes('list_matching')}">
            </div>

            <div class="col-sm-1">
              <div class="form-check">
                <input class="form-check-input" type="radio" :id="'list_source_threshold_items_' + id"
                       v-model="condition.list_matching.source_is_percentage" :value="false">
                <label class="form-check-label" :for="'list_source_threshold_items_' + id">
                  values
                </label>
              </div>
            </div>

            <div class="col-sm-1">
              <div class="form-check">
                <input class="form-check-input" type="radio" :id="'list_source_threshold_percentage_' + id"
                       v-model="condition.list_matching.source_is_percentage" :value="true">
                <label class="form-check-label" :for="'list_source_threshold_percentage_' + id">
                  %
                </label>
              </div>
            </div>

            <div class="col-auto" v-show="errors.includes('source_threshold')">
              <div class="invalid-feedback inline-feedback"
                   v-bind:class="{'is-invalid': errors.includes('source_threshold')}">
                Please specify a valid value
              </div>
            </div>
          </div>

          <div class="form-group row">
            <label :for="'list_target_threshold_' + id" class="col-sm-3 col-form-label">
              Minimum target values
            </label>

            <div class="col-sm-1">
              <input :id="'list_target_threshold_' + id" class="form-control form-control-sm"
                     type="number" step="1"
                     v-model.number="condition.list_matching.target_threshold"
                     v-bind:class="{'is-invalid': errors.includes('target_threshold') || errors.includes('list_matching')}">
            </div>

            <div class="col-sm-1">
              <div class="form-check">
                <input class="form-check-input" type="radio" :id="'list_target_threshold_items_' + id"
                       v-model="condition.list_matching.target_is_percentage" :value="false">
                <label class="form-check-label" :for="'list_target_threshold_items_' + id">
                  values
                </label>
              </div>
            </div>

            <div class="col-sm-1">
              <div class="form-check">
                <input class="form-check-input" type="radio" :id="'list_target_threshold_percentage_' + id"
                       v-model="condition.list_matching.target_is_percentage" :value="true">
                <label class="form-check-label" :for="'list_target_threshold_percentage_' + id">
                  %
                </label>
              </div>
            </div>

            <div class="col-auto" v-show="errors.includes('target_threshold')">
              <div class="invalid-feedback inline-feedback"
                   v-bind:class="{'is-invalid': errors.includes('target_threshold')}">
                Please specify a valid value
              </div>
            </div>
          </div>

          <div class="invalid-feedback mb-2" v-bind:class="{'is-invalid': errors.includes('list_matching')}">
            Please specify at least a minimum number of matches or a minimum number of source or target values
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import props from "@/utils/props";
    import ValidationMixin from "@/mixins/ValidationMixin";

    import ConditionMethod from "./ConditionMethod";

    export default {
        name: "ConditionConfiguration",
        components: {
            ConditionMethod,
        },
        mixins: [ValidationMixin],
        data() {
            return {
                tConorms: props.tConorms,
                similarityMethods: Object.keys(props.matchingMethods)
                    .filter(key => props.matchingMethods[key].isSimilarityMethod)
                    .reduce((obj, key) => ({
                        ...obj,
                        [key]: props.matchingMethods[key]
                    }), {}),
            };
        },
        props: {
            id: String,
            condition: Object,
            method: Object,
            simMethod: Object,
            useFuzzyLogic: Boolean,
            configureMatching: Boolean,
            configureTConorms: Boolean,
            applySimMethod: Boolean,
            applyListMatching: Boolean,
        },
        methods: {
            validateConditionConfiguration() {
                const simMethodNameValid = this.validateField('sim_method_name',
                    !this.applySimMethod || this.condition.method_sim_name);

                const methodConfigValid = this.validateField('method_config',
                    this.$refs.methodConfig ? this.$refs.methodConfig.validateConditionMethod() : true);
                const methodSimConfigValid = this.validateField('method_sim_config',
                    this.$refs.methodSimConfig ? this.$refs.methodSimConfig.validateConditionMethod() : true);

                const listMatchingValid = this.validateField('list_matching', !this.applyListMatching
                    || this.condition.list_matching.links_threshold > 0
                    || this.condition.list_matching.source_threshold > 0
                    || this.condition.list_matching.target_threshold > 0);

                const linksThresholdValid = this.validateField('links_threshold', !this.applyListMatching
                    || (this.condition.list_matching.links_threshold >= 0
                        && (!this.condition.list_matching.links_is_percentage
                            || this.condition.list_matching.links_threshold <= 100)));

                const sourceThresholdValid = this.validateField('source_threshold', !this.applyListMatching
                    || (this.condition.list_matching.source_threshold >= 0
                        && (!this.condition.list_matching.source_is_percentage
                            || this.condition.list_matching.source_threshold <= 100)));

                const targetThresholdValid = this.validateField('target_threshold', !this.applyListMatching
                    || (this.condition.list_matching.target_threshold >= 0
                        && (!this.condition.list_matching.target_is_percentage
                            || this.condition.list_matching.target_threshold <= 100)));

                return simMethodNameValid && methodConfigValid && methodSimConfigValid
                    && listMatchingValid && linksThresholdValid && sourceThresholdValid && targetThresholdValid;
            },
        },
    };
</script>
