<template>
  <div v-if="showResourceInfo">
    <div class="row m-0" v-for="propInfo in propsGrouped">
      <div class="col-auto">
        <div class="row mb-1">
          <div class="property-resource btn-sm read-only">
            {{ propInfo.title }}
          </div>

          <div class="property-resource btn-sm read-only mx-2">
            {{ propInfo.collectionId }}
          </div>
        </div>

        <div class="row">
          <div v-for="propAndValues in propInfo.propsAndValues" class="col-auto ml-4">
            <div class="property-path btn-sm read-only">
              {{ propAndValues.property[1] }}
            </div>

            <div v-for="value in propAndValues.values" class="property-value btn-sm read-only ml-2">
              {{ value }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else>
    <div class="row m-0" v-for="(values, property) in propsGrouped">
      <div class="property-path btn-sm read-only">
        {{ property }}
      </div>

      <div v-for="value in values" class="property-value btn-sm read-only ml-2">
        {{ value }}
      </div>
    </div>
  </div>
</template>

<script>
    export default {
        name: "Properties",
        props: {
            properties: Array,
            showResourceInfo: {
                type: Boolean,
                default: true,
            },
        },
        computed: {
            propsGrouped() {
                return this.showResourceInfo ? this.propsByResource() : this.propsByName();
            }
        },
        methods: {
            propsByResource() {
                return this.properties.reduce((acc, propAndValues) => {
                    if (!acc.hasOwnProperty(propAndValues.property[0])) {
                        const resource = this.$root.getResourceById(propAndValues.property[0]);
                        const collection = this.$root.datasets[resource.dataset_id];

                        acc[propAndValues.property[0]] = {
                            collectionId: resource.collection_id,
                            title: collection.title,
                            propsAndValues: [],
                        };
                    }

                    acc[propAndValues.property[0]].propsAndValues.push(propAndValues);
                    return acc;
                }, {});
            },

            propsByName() {
                return this.properties.reduce((acc, propAndValues) => {
                    if (!acc.hasOwnProperty(propAndValues.property[1]))
                        acc[propAndValues.property[1]] = [];

                    acc[propAndValues.property[1]].push(...propAndValues.values);
                    return acc;
                }, {});
            },
        },
    }
</script>