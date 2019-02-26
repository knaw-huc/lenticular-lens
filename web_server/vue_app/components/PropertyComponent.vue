<template>
    <div class="row">
        <div class="form-group col-3">
            <select class="form-control" :value="value" @input="$emit('input', $event.target.value)">
                <option value="" selected disabled>Choose a property</option>
                <option v-for="(property_info, property_opt) in properties" :value="property_opt">{{ property_opt }}</option>
            </select>
        </div>
    </div>
</template>
<script>
    export default {
        name: 'property-component',
        props: {
            properties: {},
            value: String,
        },
    }
</script>