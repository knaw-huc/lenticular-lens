<template>
  <div class="border p-3 mb-4" v-bind:class="[bgColor]">
    <div class="row align-items-center flex-nowrap">
      <div class="col-auto d-flex flex-column align-items-center">
        <div class="col-auto">
          <span class="font-weight-bold font-italic"># {{ index + 1 }}</span>
        </div>

        <div class="col-auto">
          <div class="btn btn-sm bg-secondary-light border border-secondary text-secondary read-only m-1">
            <span class="font-weight-bold">Similarity</span><br>
            {{ similarity }}
          </div>
        </div>
      </div>

      <div class="col">
        <div class="text-break-all">
          <span class="font-weight-bold">Source URI:</span>

          <span class="text-secondary">
            {{ switchSourceAndTarget ? link.target : link.source }}
          </span>

          <button type="button" class="btn btn-sm ml-2" @click="copySourceUriToClipboard">
            <fa-icon icon="copy"/>
          </button>
        </div>

        <div class="text-break-all">
          <span class="font-weight-bold">Target URI:</span>

          <span class="text-secondary">
            {{ switchSourceAndTarget ? link.source : link.target }}
          </span>

          <button type="button" class="btn btn-sm ml-2" @click="copyTargetUriToClipboard">
            <fa-icon icon="copy"/>
          </button>
        </div>

        <div v-if="sourceValues.length > 0 || targetValues.length > 0" class="row flex-nowrap border-top mt-2 pt-2">
          <div class="col">
            <div class="font-weight-bold mb-2">Source properties:</div>
            <property-values v-for="(prop, idx) in (switchSourceAndTarget ? targetValues : sourceValues)"
                             :key="idx" v-if="prop.values && prop.values.length > 0"
                             :graphql-endpoint="prop.graphql_endpoint" :dataset-id="prop.dataset_id"
                             :collection-id="prop.collection_id" :property="prop.property" :values="prop.values"/>
          </div>

          <div class="col">
            <div class="font-weight-bold mb-2">Target properties:</div>
            <property-values v-for="(prop, idx) in (switchSourceAndTarget ? sourceValues : targetValues)"
                             :key="idx" v-if="prop.values && prop.values.length > 0"
                             :graphql-endpoint="prop.graphql_endpoint" :dataset-id="prop.dataset_id"
                             :collection-id="prop.collection_id" :property="prop.property" :values="prop.values"/>
          </div>
        </div>
      </div>

      <div class="col-auto">
        <div class="row flex-column align-items-center">
          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-success m-1" :disabled="isUpdating"
                    @click="$emit('accepted')">
              <fa-icon icon="check"/>
              Accept
            </button>
          </div>

          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-danger m-1" :disabled="isUpdating"
                    @click="$emit('rejected')">
              <fa-icon icon="times"/>
              Reject
            </button>
          </div>

          <div class="col-auto">
            <button type="button" class="btn btn-sm btn-warning m-1" :disabled="isUpdating"
                    @click="$emit('not_sure')">
              <fa-icon icon="question"/>
              Not sure
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    import PropertyValues from "../../helpers/PropertyValues";

    export default {
        name: "Link",
        components: {
            PropertyValues
        },
        props: {
            index: Number,
            link: Object,
        },
        computed: {
            similarity() {
                return this.link.similarity && !isNaN(this.link.similarity)
                    ? this.link.similarity.toFixed(3) : '1.000';
            },

            switchSourceAndTarget() {
                return this.link.link_order === 'target_source';
            },

            sourceValues() {
                return this.link.source_values || [];
            },

            targetValues() {
                return this.link.target_values || [];
            },

            isUpdating() {
                return this.link.updating;
            },

            bgColor() {
                if (this.link.valid === 'accepted')
                    return 'bg-success';

                if (this.link.valid === 'rejected')
                    return 'bg-danger';

                if (this.link.valid === 'not_sure')
                    return 'bg-warning';

                if (this.link.valid === 'mixed')
                    return 'bg-warning';

                return 'bg-white';
            },
        },
        methods: {
            async copySourceUriToClipboard() {
                await navigator.clipboard.writeText(
                    this.switchSourceAndTarget ? this.link.target : this.link.source);
            },

            async copyTargetUriToClipboard() {
                await navigator.clipboard.writeText(
                    this.switchSourceAndTarget ? this.link.source : this.link.target);
            },
        },
    };
</script>
