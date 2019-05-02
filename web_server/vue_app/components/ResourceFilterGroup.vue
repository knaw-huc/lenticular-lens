<template>
    <div v-if="filter_object.conditions" :class="'p-5 border border-dark mb-3 ' + style_class">
        <div class="row">
            <div class="col-auto">
                <octicon name="chevron-down" scale="2" v-b-toggle="uid"></octicon>
            </div>

            <div v-if="filter_object.conditions.length > 1" class="form-group col">
                <v-select v-model="filter_object.type">
                    <option value="AND">All conditions must be met (AND)</option>
                    <option value="OR">At least one of the conditions must be met (OR)</option>
                </v-select>
            </div>

            <div v-if="filter_object.conditions.length < 1" class="col">
                No filter
            </div>

            <div v-if="!is_root" class="form-group col-1">
                <button-delete @click="$emit('remove')"/>
            </div>
        </div>

        <b-collapse visible :id="uid">
            <template v-if="filter_object.type">
                <resource-filter-group-component
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
                />

                <div class="form-group">
                    <button-add v-on:click="addFilterCondition" title="Add Filter Condition"/>
                </div>
            </template>
        </b-collapse>
    </div>
    <div v-else-if="!filter_object.conditions">
        <filter-condition-component
                :condition="filter_object"
                :index="index"
                @remove="$emit('remove')"
                @add-condition="$emit('promote-condition', {'filter_object': $parent.$parent.filter_object, 'index': index})"
        />
    </div>
</template>
<script>
    import ResourceFilterCondition from './ResourceFilterCondition'

    export default {
        components: {
            'filter-condition-component': ResourceFilterCondition,
        },
        computed: {
            style_class() {
                return this.is_root || this.$parent.$parent.style_class === 'bg-primary-light' ? 'bg-info-light' : 'bg-primary-light'
            },
        },
        methods: {
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
            addFilterGroup(event) {
                if (event) {
                    event.target.blur();
                }
                let condition = {
                    'type': 'AND',
                    'conditions': [],
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