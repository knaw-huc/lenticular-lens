<template>
  <div class="border p-3 mb-2"
       v-bind:class="[{'clickable': selectable}, selected ? 'bg-secondary-light' : 'bg-primary-very-light']"
       @click="selectable && $emit('select')">
    <div class="row">
      <div class="col">
        <div class="text-secondary">
          <strong>{{ cluster.id }}</strong>
        </div>

        <div class="row">
          <div class="col">
            <strong>Size: </strong>
            {{ cluster.size.toLocaleString('en') }}
          </div>

          <div class="col">
            <strong>Extended: </strong>
            <span v-bind:class="'ext_' + (cluster.extended ? 'yes' : 'no')">
              {{ cluster.extended ? 'yes' : 'no' }}
            </span>
          </div>
        </div>

        <div class="row">
          <div class="col">
            <strong>Links: </strong>
            {{ cluster.links.toLocaleString('en') }}
          </div>

          <div class="col">
            <strong>Reconciled: </strong>
            <span v-bind:class="'ext_' + (cluster.reconciled ? 'yes' : 'no')">
              {{ cluster.reconciled ? 'yes' : 'no' }}
            </span>
          </div>
        </div>
      </div>

      <div class="col-8">
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
            selectable: {
                type: Boolean,
                default: true
            }
        },
    };
</script>

<style>
.ext_cyc {
    color: purple;
}

.ext_yes {
    color: blue;
}

.ext_no {
    color: red;
}
</style>