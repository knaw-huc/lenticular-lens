<template>
    <div v-if="filter_object.conditions" :class="'p-3 border border-dark mb-3 ' + style_class">
        <div class="row">
            <div class="form-group col">
                <select class="form-control" v-model="filter_object.type">
                    <option v-if="is_root" value="" selected>No filter</option>
                    <option value="AND">All conditions must be met (AND)</option>
                    <option value="OR">At least one of the conditions must be met (OR)</option>
                </select>
            </div>

            <div v-if="!is_root" class="form-group col-1">
                <button @click="$emit('remove')" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
            </div>
        </div>

        <template v-if="filter_object.type">
            <resource-filter-group-component
                    v-for="(condition, condition_index) in filter_object.conditions"
                    :filter_object="condition"
                    :index="condition_index"
                    @remove="filter_object.conditions.splice(condition_index, 1)"
            />

            <div class="form-group">
                <button v-on:click="addFilterCondition" type="button"
                        class="form-control btn btn-primary w-25">+ Add condition
                </button>
            </div>
            <div class="form-group">
                <button v-on:click="addFilterGroup" type="button"
                        class="form-control btn btn-primary w-25">+ Add filter group
                </button>
            </div>
        </template>
    </div>
    <div v-else-if="!filter_object.conditions">
        <filter-condition-component :condition="filter_object" :index="index" @remove="$emit('remove')"/>
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
                return this.is_root || this.$parent.style_class === 'bg-white' ? 'bg-dark' : 'bg-white'
            },
            datasets() {
                return this.$parent.datasets
            },
            resource() {
                return this.$parent.resource
            },
            resources() {
                return this.$parent.resources
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
        },
        name: 'resource-filter-group-component',
        props: {
            filter_object: {},
            index: Number,
            is_root: false,
        }
    }
</script>