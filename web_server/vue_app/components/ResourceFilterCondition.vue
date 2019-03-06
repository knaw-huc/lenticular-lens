<template>
<div class="border-bottom pt-3 mb-3">
    <div class="row">
        <property-component v-model="condition.property" :resources="$parent.resources" :value_index.number="0"/>
    </div>

    <div class="row">
        <div class="form-group col-3">
            <select class="form-control" v-model="condition.type">
                <option value="" disabled selected>Choose a filter type</option>
                <option value="=">=</option>
                <option value="!=">!=</option>
                <option value="date_is_within">date is within</option>
                <option value="appearances">appearances of property</option>
                <option value="ilike">Contains (use % for wildcard)</option>
                <option value="not_null">Is not null</option>
            </select>
        </div>

        <div v-if="['=', '!=', 'date_is_within', 'ilike'].indexOf(condition.type) > -1" class="form-group col-3">
            <input class="form-control" type="text" v-model="condition.value" placeholder="Enter a value">
        </div>

        <div v-if="condition.type == 'appearances'" class="form-group col-2">
            <select v-model="condition.operator" class="form-control">
                <option value="<=" selected>Max.</option>
                <option value=">=" selected>Min.</option>
                <option value="=" selected>Exactly</option>
            </select>
        </div>
        <div v-if="condition.type == 'appearances'" class="form-group col-1">
            <input class="form-control" type="number" min="0" step="1" v-model.number="condition.value">
        </div>

        <div class="form-check">
            <input v-model.boolean="condition.invert" type="checkbox" class="form-check-input" :id="'resource_' + resource.id + '_condition_' + index + '_invert'">
            <label class="form-check-label" :for="'resource_' + resource.id + '_condition_' + index + '_invert'">Invert</label>
        </div>

        <div class="form-group col-1">
            <button @click="$emit('remove')" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
        </div>
    </div>
</div>
</template>

<script>
    import PropertyComponent from "./PropertyComponent";

    export default {
        components: {PropertyComponent},
        computed: {
            datasets() {
                return this.$parent.datasets
            },
            properties() {
                return this.datasets[this.resource.dataset_id][this.resource.collection_id];
            },
            resource() {
                return this.$parent.resource;
            },
        },
        props: ['condition', 'index'],
    }
</script>
