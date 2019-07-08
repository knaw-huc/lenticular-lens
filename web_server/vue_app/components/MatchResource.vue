<template>
    <div class="bg-white row align-items-center">
        <div v-if="!match_resource" class="col-auto pr-0" @mouseenter="hovering = true" @mouseleave="hovering = false">
            <v-select
                    @input="$emit('input', $event); hovering = false"
                    :value="match_resource"
                    :id="'match_' + match.id + '_resource_label_' + match_resource_id"
                    v-bind:class="{'is-invalid': errors.includes('resource')}"
            >
                <option disabled selected value="">Choose a collection</option>
                <option v-for="(root_resource, index) in resources" :value.number="root_resource.id">{{ root_resource.label }}</option>
            </v-select>

            <div class="invalid-feedback" v-show="errors.includes('resource')">
                Please select a collection
            </div>
        </div>
        <div v-else @mouseenter="hovering = true" @mouseleave="hovering = false" class="ml-3 pt-2">
            {{ match_resource.label }}
        </div>

        <div class="col-auto pl-0" @mouseenter="hovering = true" @mouseleave="hovering = false">
            <button-delete @click="$emit('remove')" :scale="1.4" :class="'pt-1' + showOnHover"/>
        </div>
    </div>
</template>

<script>
    import ValidationMixin from "../mixins/ValidationMixin";

    export default {
        mixins: [ValidationMixin],
        computed: {
            resources() {
                return this.$root.$children[0].resources.filter(resource => {
                    return !this.match[this.resources_key].includes(resource.id.toString());
                })
            },
            showOnHover() {
                return this.hovering ? '' : ' invisible';
            },
        },
        data() {
            return {
                hovering: false,
            }
        },
        props: ['match', 'match_resource', 'match_resource_id', 'resources_key'],
        methods: {
            validateResource() {
                return this.validateField('resource', this.match_resource && this.match_resource !== '');
            }
        },
    }
</script>