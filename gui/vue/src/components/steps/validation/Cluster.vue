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
            Size:
          </div>

          <div class="col">
            {{ cluster.sizeFiltered.toLocaleString('en') }} /
            {{ cluster.size.toLocaleString('en') }}
          </div>
        </div>

        <div class="row small">
          <div class="col-8 font-weight-bold">
            Links:
          </div>

          <div class="col">
            {{ Object.values(cluster.linksFiltered).reduce((a, b) => a + b, 0).toLocaleString('en') }} /
            {{ Object.values(cluster.links).reduce((a, b) => a + b, 0).toLocaleString('en') }}
          </div>
        </div>

        <div class="row small mt-3">
          <div class="col-8 font-weight-bold">
            Accepted:
          </div>

          <div class="col">
            {{
              cluster.linksFiltered.hasOwnProperty('accepted') ? cluster.linksFiltered.accepted.toLocaleString('en') : 0
            }} /
            {{
              cluster.links.hasOwnProperty('accepted') ? cluster.links.accepted.toLocaleString('en') : 0
            }}
          </div>
        </div>

        <div class="row small">
          <div class="col-8 font-weight-bold">
            Rejected:
          </div>

          <div class="col">
            {{
              cluster.linksFiltered.hasOwnProperty('rejected') ? cluster.linksFiltered.rejected.toLocaleString('en') : 0
            }} /
            {{
              cluster.links.hasOwnProperty('rejected') ? cluster.links.rejected.toLocaleString('en') : 0
            }}
          </div>
        </div>

        <div class="row small">
          <div class="col-8 font-weight-bold">
            Not sure:
          </div>

          <div class="col">
            {{
              cluster.linksFiltered.hasOwnProperty('not_sure') ? cluster.linksFiltered.not_sure.toLocaleString('en') : 0
            }} /
            {{
              cluster.links.hasOwnProperty('not_sure') ? cluster.links.not_sure.toLocaleString('en') : 0
            }}
          </div>
        </div>

        <div class="row small">
          <div class="col-8 font-weight-bold">
            Not validated:
          </div>

          <div class="col">
            {{
              cluster.linksFiltered.hasOwnProperty('not_validated') ? cluster.linksFiltered.not_validated.toLocaleString('en') : 0
            }} /
            {{
              cluster.links.hasOwnProperty('not_validated') ? cluster.links.not_validated.toLocaleString('en') : 0
            }}
          </div>
        </div>

        <div v-if="isLens" class="row small">
          <div class="col-8 font-weight-bold">
            Mixed:
          </div>

          <div class="col">
            {{
              cluster.linksFiltered.hasOwnProperty('mixed') ? cluster.linksFiltered.mixed.toLocaleString('en') : 0
            }} /
            {{
              cluster.links.hasOwnProperty('mixed') ? cluster.linksFiltered.mixed.toLocaleString('en') : 0
            }}
          </div>
        </div>
      </div>

      <div class="col-8 border-left">
        <property-values v-for="(prop, idx) in cluster.values"
                         :key="idx" v-if="prop.values && prop.values.length > 0"
                         :graphql-endpoint="prop.graphql_endpoint" :dataset-id="prop.dataset_id"
                         :collection-id="prop.collection_id" :property="prop.property" :values="prop.values"/>
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
            isLens: {
                type: Boolean,
                default: false
            }
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
