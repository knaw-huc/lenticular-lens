<template>
  <div class="ml-4 py-2" v-bind:class="{'border-top': !isFirst}">
    <ets-property :entity-type-selection="entityTypeSelection"
                  :property="conditionProperty.property" :allow-delete="allowDelete" :has-additional-buttons="true"
                  @clone="$emit('clone')" @delete="$emit('delete')" ref="propertyComponent">
      <button type="button" class="btn text-secondary p-0 ml-2" title="Add transformer"
              @click="addTransformer" ref="button">
        <fa-icon icon="text-width" size="sm"/>
      </button>
    </ets-property>

    <div v-if="conditionProperty.transformers.length > 0" class="row align-items-baseline mt-2 ml-2">
      <div class="col-auto">
        <div class="custom-control custom-switch">
          <input type="checkbox" class="custom-control-input" autocomplete="off" :id="id + '_transformer_priority'"
                 v-model="conditionProperty.property_transformer_first"/>
          <label class="custom-control-label" :for="id + '_transformer_priority'">
            Apply property transformers first
          </label>
        </div>
      </div>
    </div>

    <div v-if="conditionProperty.transformers.length > 0" class="row align-items-baseline mt-2 ml-2">
      <div class="col-auto h6">Property transformers</div>

      <div class="col-auto">
        <draggable v-model="conditionProperty.transformers" :group="`transformers_${id}`" handle=".handle">
          <transformer v-for="(transformer, idx) in conditionProperty.transformers" :key="idx"
                       :id="`${id}_${idx}`" :transformer="transformer"
                       @remove="conditionProperty.transformers.splice(idx, 1)" ref="transformers"/>
        </draggable>
      </div>
    </div>
  </div>
</template>

<script>
    import Draggable from 'vuedraggable';

    import Transformer from "./Transformer";
    import ValidationMixin from "@/mixins/ValidationMixin";

    export default {
        name: "ConditionProperty",
        mixins: [ValidationMixin],
        components: {
            Draggable,
            Transformer,
        },
        props: {
            id: String,
            conditionProperty: Object,
            entityTypeSelection: Object,
            allowDelete: {
                type: Boolean,
                default: true,
            },
            isFirst: {
                type: Boolean,
                default: false,
            },
        },
        methods: {
            validateConditionProperty() {
                const propertyValid = this.$refs.propertyComponent.validateProperty();
                const transformersValid = this.$refs.transformers
                    ? !this.$refs.transformers
                        .map(transformer => transformer.validateTransformer())
                        .includes(false)
                    : true;

                return propertyValid && transformersValid;
            },

            addTransformer(name = '') {
                this.conditionProperty.transformers.push({name, parameters: {}});
            },
        },
    };
</script>