<template>
  <div class="row align-items-center">
    <div v-if="!matchResource" class="col-auto pr-0" @mouseenter="hovering = true" @mouseleave="hovering = false">
      <select-box
          :id="'match_' + match.id + '_resource_label_' + matchResourceId"
          :value="matchResource"
          v-bind:class="{'is-invalid': errors.includes('resource')}"
          @input="selectResource">
        <option disabled selected value="">Choose a collection</option>
        <option v-for="rootResource in resources" :value.number="rootResource.id">
          {{ rootResource.label }}
        </option>
      </select-box>

      <div class="invalid-feedback" v-show="errors.includes('resource')">
        Please select a collection
      </div>
    </div>

    <div v-else @mouseenter="hovering = true" @mouseleave="hovering = false" class="ml-3">
      {{ matchResource.label }}
    </div>

    <div class="col-auto pl-0 ml-3" @mouseenter="hovering = true" @mouseleave="hovering = false">
      <button-delete size="sm" class="btn-sm" v-bind:class="{'invisible': !hovering}" @click="$emit('remove')"/>
    </div>
  </div>
</template>

<script>
    import ValidationMixin from "../../../mixins/ValidationMixin";

    export default {
        name: "MatchResource",
        mixins: [ValidationMixin],
        data() {
            return {
                hovering: false,
            };
        },
        props: {
            match: Object,
            matchResource: Object,
            matchResourceId: String,
            resourcesKey: String,
        },
        computed: {
            resources() {
                return this.$root.resources.filter(resource => {
                    return !this.match[this.resourcesKey].includes(resource.id.toString());
                });
            },
        },
        methods: {
            validateResource() {
                return this.validateField('resource', this.matchResource && this.matchResource !== '');
            },

            selectResource(resourceId) {
                this.hovering = false;
                this.$emit('input', parseInt(resourceId));
            },
        },
    };
</script>