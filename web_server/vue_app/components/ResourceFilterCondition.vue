<template>
<div>
    <div class="row">
        <div class="form-group col-2">
            <select class="form-control" v-model="condition.property[0]">
                <option v-for="collection in resources" :key="collection.id" :value="collection.id">{{ collection.label }}
                </option>
            </select>
        </div>
    </div>
    <property-component v-model="condition.property[1]" :properties="properties"/>

    <div class="row">
        <div class="form-group col-3">
            <select class="form-control" v-model="condition.type">
                <option value="" disabled selected>Choose a filter type</option>
                <option value="=">=</option>
                <option value="!=">!=</option>
                <option value="date_is_within">date is within</option>
                <option value="appearances">appearances of property</option>
            </select>
        </div>

        <div v-if="['=', '!=', 'date_is_within'].indexOf(condition.type) > -1" class="form-group col-2">
            <input class="form-control" type="text" v-model="condition.value" placeholder="Enter a value">
        </div>

        <div v-if="condition.type == 'appearances'" class="form-group col-2">
            <select v-model="condition.value_type" class="form-control">
                <option value="max" selected>Max.</option>
            </select>
        </div>
        <div v-if="condition.type == 'appearances'" class="form-group col-1">
            <input class="form-control" type="number" min="0" step="1" v-model.number="condition.value">
        </div>

        <div class="form-group col-1">
            <button v-on:click="resource.filter.conditions.splice(index, 1)" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
        </div>
    </div>
</div>
</template>

<script>
    import PropertyComponent from "./PropertyComponent";

    export default {
        components: {PropertyComponent},
        computed: {
            properties() {
                let resource = this.get_resource_by_id(this.condition.property[0]);
                return this.datasets[resource.dataset_id][resource.collection_id];
            },
            resource() {
                return this.get_resource_by_id(this.resource_id);
            },
        },
        methods: {
            get_resource_by_id(resource_id) {
                for (let i = 0; i < this.resources.length; i++) {
                    if (this.resources[i].id == resource_id)
                        return this.resources[i];
                }
            },
        },
        props: ['condition', 'resource_id', 'index', 'datasets', 'resources'],
    }
</script>
