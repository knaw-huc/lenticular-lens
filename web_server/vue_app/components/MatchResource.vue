<template>
    <div class="bg-white row">
        <div v-if="!match_resource" class="form-group col-auto pr-0" @mouseenter="hovering = true" @mouseleave="hovering = false">
            <select class="border-0 btn-outline-info col-auto form-control h-auto shadow"
                    @input="$emit('input', $event.target.value); hovering = false"
                    :value="match_resource" :id="'match_' + match.id + '_resource_label_' + match_resource_id"
            >
                <option disabled selected value="">Choose a collection</option>
                <option v-for="(root_resource, index) in $root.$children[0].resources" :value.number="root_resource.id">{{ root_resource.label }}</option>
            </select>
        </div>
        <div v-else @mouseenter="hovering = true" @mouseleave="hovering = false" class="ml-3 pt-2">
            {{ match_resource.label }}
        </div>

        <div class="form-group col-auto pl-0" @mouseenter="hovering = true" @mouseleave="hovering = false">
            <button-delete @click="$emit('remove')" :scale="1.4" :class="'pt-1' + showOnHover"/>
        </div>
    </div>
</template>

<script>
    export default {
        computed: {
            showOnHover() {
                return this.hovering ? '' : ' invisible';
            },
        },
        data() {
            return {
                hovering: false,
            }
        },
        props: ['match', 'match_resource', 'match_resource_id'],
    }
</script>