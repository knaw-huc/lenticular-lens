<template>
    <div v-if="filter_object.conditions" :class="'shadow p-3 border mb-3 ' + style_class">
        <div class="row align-items-center">
            <div class="col-auto">
                <octicon name="chevron-down" scale="2" v-b-toggle="uid"></octicon>
            </div>

            <div v-if="filter_object.conditions.length > 1" class="col">
                <v-select v-model="filter_object.type">
                    <option value="AND">All conditions must be met (AND)</option>
                    <option value="OR">At least one of the conditions must be met (OR)</option>
                </v-select>
            </div>

            <div v-if="filter_object.conditions.length < 1" class="col">
                No filter
            </div>

            <div class="col-auto">
                <div class="row">
                    <div v-if="!is_root" class="col-auto">
                        <button-delete @click="$emit('remove')" title="Delete this Group" class="pt-1 pr-0"/>
                    </div>

                    <div v-if="!is_root" class="col-auto">
                        <button-add v-on:click="addFilterCondition" title="Add Filter Condition"/>
                    </div>
                </div>
            </div>
        </div>

        <b-collapse visible :id="uid" :ref="uid">
            <resource-filter-group-component
                v-if="filter_object.type"
                v-for="(condition, condition_index) in filter_object.conditions"
                :filter_object="condition"
                :index="condition_index"
                :uid="uid + '_' + condition_index"
                :datasets="datasets"
                :resource="resource"
                :resources="resources"
                @remove="removeCondition(condition_index)"
                @promote-condition="$emit('promote-condition', $event)"
                @demote-filter-group="$emit('demote-filter-group', $event)"
                ref="filterGroupComponents"
            />
        </b-collapse>
    </div>

    <filter-condition-component
        v-else-if="!filter_object.conditions"
        :condition="filter_object"
        :index="index"
        @remove="$emit('remove')"
        @add-condition="$emit('promote-condition', {'filter_object': $parent.$parent.filter_object, 'index': index})"
        ref="filterConditionComponent"
    />
</template>
<script>
    import ResourceFilterCondition from './ResourceFilterCondition';
    import ValidationMixin from "../mixins/ValidationMixin";

    export default {
        mixins: [ValidationMixin],
        components: {
            'filter-condition-component': ResourceFilterCondition,
        },
        computed: {
            style_class() {
                let styleClass = this.is_root ? '' : 'mt-3 ';
                if (this.is_root || this.$parent.$parent.style_class.includes('bg-primary-light'))
                    styleClass += 'bg-info-light border-info';
                else
                    styleClass += 'bg-primary-light border-primary';

                return styleClass;
            },
        },
        methods: {
            validateFilterGroup() {
                if (this.filter_object.conditions && this.filter_object.conditions.length > 0) {
                    const valid = !this.$refs.filterGroupComponents
                        .map(filterGroupComponent => filterGroupComponent.validateFilterGroup())
                        .includes(false);

                    const isShown = this.$refs[this.uid].show;
                    if (!valid && !isShown)
                        this.$root.$emit('bv::toggle::collapse', this.uid);

                    return valid;
                }

                if (!this.filter_object.conditions)
                    return this.$refs.filterConditionComponent.validateFilterCondition();

                return true;
            },

            addFilterCondition(event) {
                if (event) {
                    event.target.blur();
                }
                let condition = {
                    'type': '',
                    'property': [this.resource.id, ''],
                };
                this.filter_object.conditions.push(condition);
            },
            removeCondition(condition_index) {
                this.filter_object.conditions.splice(condition_index, 1);

                if (!this.is_root && this.filter_object.conditions.length === 1) {
                    this.$emit('demote-filter-group', {'filter_object': this.$parent.$parent.filter_object, 'index': this.index})
                }
            },
        },
        name: 'resource-filter-group-component',
        props: {
            datasets: {},
            filter_object: {},
            index: Number,
            is_root: false,
            uid: '',
            resource: {},
            resources: {},
        }
    }
</script>