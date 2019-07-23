<template>
  <div v-if="matching_method_group.conditions" class="shadow p-3 border mt-3"
       v-bind:class="[{'is-invalid': errors.length > 0}, ...styleClass]">
    <div class="row align-items-center">
      <div class="col-auto">
        <octicon name="chevron-down" scale="2" v-b-toggle="uid"></octicon>
      </div>

      <div v-if="matching_method_group.conditions.length > 1" class="col">
        <v-select v-model="matching_method_group.type">
          <option value="AND">All conditions must be met (AND)</option>
          <option value="OR">At least one of the conditions must be met (OR)</option>
        </v-select>
      </div>

      <div v-if="matching_method_group.conditions.length < 1" class="col">
        No matching methods

        <div class="invalid-feedback d-block">
          <template v-if="errors.includes('conditions')">
            Please provide at least one matching method
          </template>
        </div>
      </div>

      <div class="col-auto">
        <div class="row">
          <div v-if="!is_root" class="col-auto">
            <button-delete @click="$emit('remove')" title="Delete this Group" class="pt-1 pr-0"/>
          </div>

          <div v-if="!is_root" class="col-auto">
            <button-add v-on:click="addCondition" title="Add Matching Method Group"/>
          </div>
        </div>
      </div>
    </div>

    <b-collapse visible :id="uid" :ref="uid">
      <matching-method-group
          v-for="(condition, condition_index) in matching_method_group.conditions"
          :matching_method_group="condition"
          :index="condition_index"
          :uid="uid + '_' + condition_index"
          :sources="sources"
          :targets="targets"
          @remove="removeCondition(condition_index)"
          @promote-matching-method="$emit('promote-matching-method', $event)"
          @demote-matching-method-group="$emit('demote-matching-method-group', $event)"
          ref="matchingMethodGroupComponents"
      />
    </b-collapse>
  </div>

  <match-condition
      v-else-if="!matching_method_group.conditions"
      :condition="matching_method_group"
      @remove="$emit('remove')"
      @add-matching-method="$emit('promote-matching-method', {'group': $parent.$parent.matching_method_group, 'index': index})"
      ref="matchConditionComponent"
  ></match-condition>
</template>
<script>
    import MatchCondition from './MatchCondition';
    import ValidationMixin from '../mixins/ValidationMixin';

    export default {
        name: 'MatchingMethodGroup',
        mixins: [ValidationMixin],
        components: {
            MatchCondition
        },
        props: {
            matching_method_group: {},
            sources: Array,
            targets: Array,
            is_root: false,
            uid: '',
            index: Number,
        },
        computed: {
            styleClass() {
                const styleClass = [];

                if (this.is_root)
                    styleClass.push('mt-3');

                if (this.is_root || this.$parent.$parent.styleClass.includes('bg-primary-light'))
                    styleClass.push('bg-info-light', 'border-info');
                else
                    styleClass.push('bg-primary-light', 'border-primary');

                return styleClass;
            },
        },
        methods: {
            validateMatchingGroup() {
                if (this.matching_method_group.conditions && this.matching_method_group.conditions.length > 0) {
                    const valid = !this.$refs.matchingMethodGroupComponents
                        .map(matchingMethodGroupComponent => matchingMethodGroupComponent.validateMatchingGroup())
                        .includes(false);

                    this.validateField(this.uid, valid);
                    return valid;
                }

                if (!this.matching_method_group.conditions) {
                    const valid = this.$refs.matchConditionComponent.validateMatchCondition();

                    this.validateField(this.uid, valid);
                    return valid;
                }

                const valid = this.validateField('conditions', this.matching_method_group.conditions.length > 0);

                this.validateField(this.uid, valid);
                return valid;
            },

            addCondition() {
                let condition = {
                    'method_name': '',
                    'method_value': {},
                    'sources': this.sources.reduce((acc, from_resource) => {
                        acc[from_resource] = [{'property': [from_resource, '']}];
                        return acc;
                    }, {}),
                    'targets': this.targets.reduce((acc, from_resource) => {
                        acc[from_resource] = [{'property': [from_resource, '']}];
                        return acc;
                    }, {}),
                };

                this.matching_method_group.conditions.push(condition);
            },

            removeCondition(condition_index) {
                this.matching_method_group.conditions.splice(condition_index, 1);

                if (!this.is_root && this.matching_method_group.conditions.length === 1) {
                    this.$emit('demote-matching-method-group', {
                        'group': this.$parent.$parent.matching_method_group,
                        'index': this.index
                    })
                }
            },
        },
    }
</script>