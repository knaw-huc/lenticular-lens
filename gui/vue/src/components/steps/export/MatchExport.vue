<template>
  <card :id="'export_match_' + type + '_' + match.id" type="export-matches" :label="match.label" :has-collapse="false">
    <div class="row justify-content-center">
      <div class="col-auto">
        <div class="btn-toolbar" role="toolbar" aria-label="Toolbar">
          <div class="btn-group btn-group-toggle">
            <a class="btn btn-secondary btn-sm" :href="exportCSVLink(true, true, true, true)">
              <fa-icon icon="file-export"/>
              CSV export all
            </a>

            <a class="btn btn-secondary btn-sm" :href="exportCSVLink(true, false, false, false)">
              <fa-icon icon="file-export"/>
              CSV export accepted only
            </a>

            <a class="btn btn-secondary btn-sm" :href="exportCSVLink(false, true, false, false)">
              <fa-icon icon="file-export"/>
              CSV export rejected only
            </a>

            <a class="btn btn-secondary btn-sm" :href="exportCSVLink(false, false, true, false)">
              <fa-icon icon="file-export"/>
              CSV export not validated only
            </a>

            <a v-if="isLens" class="btn btn-secondary btn-sm" :href="exportCSVLink(false, false, false, true)">
              <fa-icon icon="file-export"/>
              CSV export mixed only
            </a>
          </div>
        </div>
      </div>
    </div>
  </card>
</template>

<script>
    export default {
        name: "MatchExport",
        props: {
            type: String,
            match: Object,
        },
        computed: {
            isLens() {
                return this.type === 'lens';
            },
        },
        methods: {
            exportCSVLink(exportAccepted, exportRejected, exportNotValidated, exportMixed) {
                return this.$root.exportCsvLink(this.type, this.match.id, exportAccepted, exportRejected, exportNotValidated, exportMixed);
            },
        },
    };
</script>
