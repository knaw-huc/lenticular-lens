<template>
  <div class="border p-3 mb-2" v-bind:class="[selected ? 'bg-primary-light' : 'bg-white']" :data-index="index">
    <div class="row align-items-center justify-content-between">
      <div class="col-auto">
        <div class="row">
          <div class="col-auto font-weight-bold font-italic">
            # {{ cluster.id }}
          </div>

          <div class="col-auto ml-4">
            Extended:
            <span :class="'ext_' + (cluster.extended ? 'yes' : 'no')">
              {{ cluster.extended ? 'yes' : 'no' }}
            </span>
          </div>

          <div class="col-auto">
            Reconciled:
            <span :class="'ext_' + (cluster.reconciled ? 'yes' : 'no')">
              {{ cluster.reconciled ? 'yes' : 'no' }}
            </span>
          </div>

          <div class="col-auto">
            All validated:
            <span :class="'ext_' + (isAllValidated ? 'yes' : 'no')">
              {{ isAllValidated ? 'yes' : 'no' }}
            </span>
          </div>
        </div>
      </div>

      <div class="col-auto">
        <button class="btn btn-sm btn-secondary" v-bind:class="{'active': selected}" @click="$emit('select')">
          <template v-if="selected">Remove from selection</template>
          <template v-else>Include in selection</template>
        </button>
      </div>
    </div>

    <div class="row border-top mt-3 pt-3">
      <div class="col">
        <div class="row small">
          <div class="col-8 font-weight-bold">
            Number of nodes (size):
          </div>

          <div class="col">
            <loading v-if="isLoadingStats" :inline="true"/>
            <template v-else>
              {{ cluster.sizeFiltered.toLocaleString('en') }}
            </template>
            / {{ cluster.size.toLocaleString('en') }}
          </div>
        </div>

        <div class="row small">
          <div class="col-8 font-weight-bold">
            Number of links:
          </div>

          <div class="col">
            <loading v-if="isLoadingStats" :inline="true"/>
            <template v-else>
              {{ Object.values(cluster.linksFiltered).reduce((a, b) => a + b, 0).toLocaleString('en') }}
            </template>
            / {{ Object.values(cluster.links).reduce((a, b) => a + b, 0).toLocaleString('en') }}
          </div>
        </div>

        <div class="row small mt-3">
          <div class="col-8 font-weight-bold">
            Accepted:
          </div>

          <div class="col">
            <loading v-if="isLoadingStats" :inline="true"/>
            <template v-else>
              {{ cluster.linksFiltered.accepted.toLocaleString('en') }}
            </template>
            / {{ cluster.links.accepted.toLocaleString('en') }}
          </div>
        </div>

        <div class="row small">
          <div class="col-8 font-weight-bold">
            Rejected:
          </div>

          <div class="col">
            <loading v-if="isLoadingStats" :inline="true"/>
            <template v-else>
              {{ cluster.linksFiltered.rejected.toLocaleString('en') }}
            </template>
            / {{ cluster.links.rejected.toLocaleString('en') }}
          </div>
        </div>

        <div class="row small">
          <div class="col-8 font-weight-bold">
            Not sure:
          </div>

          <div class="col">
            <loading v-if="isLoadingStats" :inline="true"/>
            <template v-else>
              {{ cluster.linksFiltered.not_sure.toLocaleString('en') }}
            </template>
            / {{ cluster.links.not_sure.toLocaleString('en') }}
          </div>
        </div>

        <div class="row small">
          <div class="col-8 font-weight-bold">
            Not validated:
          </div>

          <div class="col">
            <loading v-if="isLoadingStats" :inline="true"/>
            <template v-else>
              {{ cluster.linksFiltered.not_validated.toLocaleString('en') }}
            </template>
            / {{ cluster.links.not_validated.toLocaleString('en') }}
          </div>
        </div>

        <div v-if="isLens" class="row small">
          <div class="col-8 font-weight-bold">
            Mixed:
          </div>

          <div class="col">
            <loading v-if="isLoadingStats" :inline="true"/>
            <template v-else>
              {{ cluster.linksFiltered.mixed.toLocaleString('en') }}
            </template>
            / {{ cluster.links.mixed.toLocaleString('en') }}
          </div>
        </div>
      </div>

      <div class="col-8 border-left">
        <loading v-if="isLoadingValues" class="mt-4"/>

        <template v-else>
          <property-values v-for="(prop, idx) in cluster.values"
                           :key="idx" v-if="prop.values && prop.values.length > 0"
                           :graphql-endpoint="prop.graphql_endpoint" :dataset-id="prop.dataset_id"
                           :collection-id="prop.collection_id" :property="prop.property" :values="prop.values"/>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
    import PropertyValues from "../../helpers/PropertyValues";

    export default {
        name: "Cluster",
        components: {
            PropertyValues,
        },
        props: {
            index: Number,
            cluster: Object,
            selected: false,
            isLens: false,
            isLoadingStats: false,
            isLoadingValues: false,
        },
        computed: {
            isAllValidated() {
                return !this.cluster.links.hasOwnProperty('not_validated') || this.cluster.links.not_validated === 0;
            },
        },
        mounted() {
            this.$emit('mounted', this.$el);
        },
    };
</script>
