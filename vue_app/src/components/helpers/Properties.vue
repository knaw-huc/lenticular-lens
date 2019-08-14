<template>
  <div>
    <div class="row m-0" v-for="propInfo in propsByResource">
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
          <div v-for="propAndValues in propInfo.propAndValues" class="col-auto ml-4">
            <property :property="propAndValues.property" :small="true" :read-only="true" :resource-info="false">
              <div v-for="value in propAndValues.values"
                   class="col-auto btn btn-sm border border-info bg-white text-info rounded-pill mx-2 py-0">
                {{ value }}
              </div>
            </property>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
    export default {
        name: "Properties",
        props: {
            properties: Array,
        },
        computed: {
            propsByResource() {
                return this.properties.reduce((acc, propAndValues) => {
                    if (!acc.hasOwnProperty(propAndValues.property[0])) {
                        const resource = this.$root.getResourceById(propAndValues.property[0]);
                        const collection = this.$root.datasets[resource.dataset_id];

                        acc[propAndValues.property[0]] = {
                            collectionId: resource.collection_id,
                            title: collection.title,
                            propAndValues: [],
                        };
                    }

                    acc[propAndValues.property[0]].propAndValues.push(propAndValues);
                    return acc;
                }, {});
            },
        },
    }
</script>