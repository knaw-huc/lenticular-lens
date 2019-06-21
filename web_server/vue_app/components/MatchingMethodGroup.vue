<template>
  <div v-if="matching_method_group.conditions" :class="'shadow p-3 border mb-3 ' + style_class">
    <div class="row">
      <div class="col-auto">
        <octicon name="chevron-down" scale="2" v-b-toggle="uid"></octicon>
      </div>

      <div v-if="matching_method_group.conditions.length > 1" class="form-group col">
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

      <div v-if="!is_root" class="form-group col-auto">
        <button-delete @click="$emit('remove')" title="Delete this Group" class="pt-1 pr-0"/>
      </div>

      <div v-if="!is_root" class="form-group col-auto">
        <button-add v-on:click="addCondition" title="Add Matching Method Group"/>
      </div>
    </div>

    <b-collapse visible :id="uid" :ref="uid">
      <matching-method-group-component
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
  <div v-else-if="!matching_method_group.conditions">
    <div class="row pl-5">
      <div class="col">
        <match-condition
            :condition="matching_method_group"
            @remove="$emit('remove')"
            @add-matching-method="$emit('promote-matching-method', {'group': $parent.$parent.matching_method_group, 'index': index})"
            ref="matchConditionComponent"
        ></match-condition>
      </div>
    </div>
  </div>
</template>
<script>
    import MatchCondition from './MatchCondition';
    import ValidationMixin from '../mixins/ValidationMixin';

    export default {
        mixins: [ValidationMixin],
        components: {
            'match-condition': MatchCondition
        },
        computed: {
            style_class() {
                return this.is_root || this.$parent.$parent.style_class === 'bg-primary-light border-primary' ? 'bg-info-light border-info' : 'bg-primary-light border-primary'
            },
        },
        methods: {
            validateMatchingGroup() {
                if (this.matching_method_group.conditions && this.matching_method_group.conditions.length > 0) {
                    const valid = !this.$refs.matchingMethodGroupComponents
                        .map(matchingMethodGroupComponent => matchingMethodGroupComponent.validateMatchingGroup())
                        .includes(false);

                    const isShown = this.$refs[this.uid].show;
                    if (!valid && !isShown)
                        this.$root.$emit('bv::toggle::collapse', this.uid);

                    return valid;
                }

                if (!this.matching_method_group.conditions)
                    return this.$refs.matchConditionComponent.validateMatchCondition();

                return this.validateField('conditions', this.matching_method_group.conditions.length > 0);
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
                    this.$emit('demote-matching-method-group', {'group': this.$parent.$parent.matching_method_group, 'index': this.index})
                }
            },
        },
        name: 'matching-method-group-component',
        props: {
            matching_method_group: {},
            sources: Array,
            targets: Array,
            is_root: false,
            uid: '',
            index: Number,
        }
    }
</script>