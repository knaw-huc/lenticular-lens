<template>
  <card :id="'export_match_' + match.id" type="export-matches" :label="match.label" :has-collapse="false">
    <div class="row justify-content-center">
      <div class="col-auto">
        <div class="btn-toolbar" role="toolbar" aria-label="Toolbar">
          <div class="btn-group btn-group-toggle">
            <a class="btn btn-secondary btn-sm" :href="exportCSVLink(true, true, true)">
              <fa-icon icon="file-export"/>
              CSV export all
            </a>

            <a class="btn btn-secondary btn-sm" :href="exportCSVLink(true, false, false)">
              <fa-icon icon="file-export"/>
              CSV export accepted only
            </a>

            <a class="btn btn-secondary btn-sm" :href="exportCSVLink(false, true, false)">
              <fa-icon icon="file-export"/>
              CSV export declined only
            </a>

            <a class="btn btn-secondary btn-sm" :href="exportCSVLink(false, false, true)">
              <fa-icon icon="file-export"/>
              CSV export not validated only
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
            match: Object,
        },
        methods: {
            exportCSVLink(exportAccepted, exportDeclined, exportNotValidated) {
                return this.$root.exportCsvLink(this.match.id, exportAccepted, exportDeclined, exportNotValidated);
            },
        },
    };
</script>
