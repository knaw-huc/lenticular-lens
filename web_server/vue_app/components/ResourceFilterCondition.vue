<template>
<div class="border-bottom p-3 mb-3 bg-primary">
    <div class="row">
        <property-component
                :property="condition.property"
                :singular="true"
                @resetProperty="resetProperty(condition.property, $event)"
        />
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
    export default {
        computed: {
            datasets() {
                return this.$parent.datasets
            },
            properties() {
                return this.$parent.datasets[this.$parent.resource.dataset_id]['collections'][this.$parent.resource.collection_id];
            },
            resource() {
                return this.$parent.resource;
            },
        },
        methods: {
            resetProperty(property, property_index) {
                let new_property = property.slice(0, property_index);
                new_property.push('');
                if (new_property.length % 2 > 0) {
                    new_property.push('');
                }

                this.$set(this.condition, 'property', new_property);
            },
        },
        props: ['condition', 'index'],
    }
</script>
