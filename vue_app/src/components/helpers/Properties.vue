<template>
  <div v-if="showResourceInfo">
    <div class="row m-0" v-for="propInfo in propsGrouped">
      <div class="col-auto">
        <div class="row mb-1">
          <div class="col-auto btn btn-sm border border-info bg-white rounded-pill py-0 my-1">
            {{ propInfo.title }}
          </div>

          <div class="col-auto btn btn-sm border border-info bg-white rounded-pill py-0 my-1 mx-2">
            {{ propInfo.collectionId }}
          </div>
        </div>

        <div class="row">
          <div v-for="propAndValues in propInfo.propsAndValues" class="col-auto ml-4">
            <div class="col-auto btn btn-sm bg-info text-white rounded-pill py-0 my-1">
              {{ propAndValues.property[1] }}
            </div>

            <div v-for="value in propAndValues.values"
                 class="col-auto btn btn-sm border border-info bg-white text-info rounded-pill ml-2 py-0 my-1">
              {{ value }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else>
    <div class="row m-0" v-for="(values, property) in propsGrouped">
      <div class="col-auto btn btn-sm bg-info text-white rounded-pill py-0 my-1">
        {{ property }}
      </div>

      <div v-for="value in values"
           class="col-auto btn btn-sm border border-info bg-white text-info rounded-pill ml-2 py-0 my-1">
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