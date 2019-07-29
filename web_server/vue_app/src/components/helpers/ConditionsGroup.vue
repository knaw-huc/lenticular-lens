<template>
  <div v-if="conditionsGroup.conditions" class="shadow p-3 border mt-3"
       v-bind:class="[{'is-invalid': errors.length > 0}, ...styleClass]">
    <div class="row align-items-center">
      <div class="col-auto">
        <octicon name="chevron-down" scale="2" v-b-toggle="uid"></octicon>
      </div>

      <div v-if="conditionsGroup.conditions.length > 0" class="col">
        <v-select v-model="conditionsGroup.type">
          <option value="AND">All conditions must be met (AND)</option>
          <option value="OR">At least one of the conditions must be met (OR)</option>
        </v-select>
      </div>

      <div v-if="conditionsGroup.conditions.length < 1" class="col font-italic">
        No conditions

        <div class="invalid-feedback d-block">
          <template v-if="errors.includes('conditions')">
            Please provide at least one condition
          </template>
        </div>
      </div>

      <div class="col-auto" v-if="conditionsGroup.conditions.length > 0">
        <div class="row">
          <div class="col-auto" v-if="!isRoot">
            <button-delete @click="$emit('remove', index)" title="Delete this group" class="pt-1 pr-0"/>
          </div>

          <div class="col-auto">
            <button-add @click="$emit('add', conditionsGroup)" title="Add condition"/>
          </div>
        </div>
      </div>
    </div>

    <b-collapse visible :id="uid" :ref="uid">
      <conditions-group
          v-for="(condition, conditionIndex) in conditionsGroup.conditions"
          :key="conditionIndex"
          :index="conditionIndex"
          :uid="uid + '_' + conditionIndex"
          :conditions-group="condition"
          @add="$emit('add', $event)"
          @remove="removeCondition($event)"
          @promote="promoteConditionGroup($event)"
          @demote="demoteConditionGroup($event)"
          v-slot="slotProps"
          ref="conditionGroupComponents">
        <slot v-bind="slotProps"/>
      </conditions-group>
    </b-collapse>
  </div>

  <div v-else>
    <slot v-bind:index="index" v-bind:condition="conditionsGroup"
          v-bind:add="() => $emit('promote', index)" v-bind:remove="() => $emit('remove', index)"/>
  </div>
</template>

<script>
    import ValidationMixin from "../../mixins/ValidationMixin";

    export default {
        name: "ConditionsGroup",
        mixins: [ValidationMixin],
        props: {
            uid: '',
            index: 0,
            conditionsGroup: {},
            isRoot: {
                type: Boolean,
                default: false,
            },
        },
        computed: {
            styleClass() {
                const styleClass = [];

                if (this.isRoot)
                    styleClass.push('mt-3');

                if (this.isRoot || this.$parent.$parent.styleClass.includes('bg-primary-light'))
                    styleClass.push('bg-info-light', 'border-info');
                else
                    styleClass.push('bg-primary-light', 'border-primary');

                return styleClass;
            },
        },
        methods: {
            validateConditionsGroup() {
                if (this.conditionsGroup.conditions && this.conditionsGroup.conditions.length > 0) {
                    const valid = !this.$refs.conditionGroupComponents
                        .map(conditionGroupComponent => conditionGroupComponent.validateConditionsGroup())
                        .includes(false);

                    this.validateField(this.uid, valid);
                    return valid;
                }

                const valid = this.validateField('conditions', this.conditionsGroup.conditions.length > 0);
                this.validateField(this.uid, valid);

                return valid;
            },

            removeCondition(index) {
                this.conditionsGroup.conditions.splice(index, 1);

                if (!this.isRoot && this.conditionsGroup.conditions.length === 1)
                    this.$emit('demote', this.index);
            },

            promoteConditionGroup(index) {
                const condition = this.conditionsGroup.conditions[index];
                const conditionCopy = JSON.parse(JSON.stringify(condition));

                const conditionGroup = {
                    type: 'AND',
                    conditions: [conditionCopy],
                };

                this.$set(this.conditionsGroup.conditions, index, conditionGroup);
                this.$emit('add', this.conditionsGroup.conditions[index]);
            },

            demoteConditionGroup(index) {
                const condition = this.conditionsGroup.conditions[index].conditions[0];
                const conditionCopy = JSON.parse(JSON.stringify(condition));

                this.$set(this.conditionsGroup.conditions, index, conditionCopy);
            },
        }
    }
</script>