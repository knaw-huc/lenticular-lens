<template>
  <card :id="'export_' + type + '_' + spec.id" type="export" :res-id="spec.id" :label="spec.label">
    <div class="row align-items-stretch justify-content-around">
      <sub-card label="Format" class="col-export">
        <div class="custom-control custom-switch mt-3">
          <input type="radio" class="custom-control-input" autocomplete="off"
                 :id="'export_csv_' + type + '_' + spec.id" value="csv"
                 v-model="format" @change="updateState('export_csv')"/>
          <label class="custom-control-label" :for="'export_csv_' + type + '_' + spec.id">
            CSV
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="radio" class="custom-control-input" autocomplete="off"
                 :id="'export_turtle_' + type + '_' + spec.id" value="turtle"
                 v-model="format" @change="updateState('export_turtle')"/>
          <label class="custom-control-label" :for="'export_turtle_' + type + '_' + spec.id">
            RDF Turtle
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="radio" class="custom-control-input" autocomplete="off"
                 :id="'export_trig_' + type + '_' + spec.id" value="trig"
                 v-model="format" @change="updateState('export_trig')"/>
          <label class="custom-control-label" :for="'export_trig_' + type + '_' + spec.id">
            RDF TriG
          </label>
        </div>
      </sub-card>

      <sub-card label="Data" class="col-export">
        <div class="custom-control custom-switch mt-3">
          <input type="checkbox" class="custom-control-input" autocomplete="off"
                 :id="'export_linkset_' + type + '_' + spec.id"
                 v-model="exportLinkset" @change="updateState('export_linkset')"/>
          <label class="custom-control-label" :for="'export_linkset_' + type + '_' + spec.id">
            Linkset
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="checkbox" class="custom-control-input" autocomplete="off"
                 :id="'export_links_md_' + type + '_' + spec.id" :disabled="format === 'csv'"
                 v-model="exportLinksMd" @change="updateState('export_links_md')"/>
          <label class="custom-control-label" :for="'export_links_md_' + type + '_' + spec.id">
            Links metadata
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="checkbox" class="custom-control-input" autocomplete="off"
                 :id="'export_generic_md_' + type + '_' + spec.id" :disabled="format === 'csv'"
                 v-model="exportGenericMd" @change="updateState('export_generic_md')"/>
          <label class="custom-control-label" :for="'export_generic_md_' + type + '_' + spec.id">
            Generic metadata
          </label>
        </div>
      </sub-card>

      <sub-card label="Restrictions" class="col-export">
        <div class="custom-control custom-switch mt-3">
          <input type="checkbox" class="custom-control-input" autocomplete="off"
                 :id="'export_all_links_' + type + '_' + spec.id"
                 v-model="exportAllLinks" @change="updateState('export_all_links')"/>
          <label class="custom-control-label" :for="'export_all_links_' + type + '_' + spec.id">
            All links
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="checkbox" class="custom-control-input" autocomplete="off"
                 :id="'export_validated_links_' + type + '_' + spec.id"
                 v-model="exportValidatedLinks" @change="updateState('export_validated_links')"/>
          <label class="custom-control-label" :for="'export_validated_links_' + type + '_' + spec.id">
            Validated links
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="checkbox" class="custom-control-input" autocomplete="off"
                 :id="'export_not_validated_links_' + type + '_' + spec.id"
                 v-model="exportNotValidatedLinks" @change="updateState('export_not_validated_links')"/>
          <label class="custom-control-label" :for="'export_not_validated_links_' + type + '_' + spec.id">
            Not validated links
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="checkbox" class="custom-control-input" autocomplete="off"
                 :id="'export_accepted_links_' + type + '_' + spec.id"
                 v-model="exportAcceptedLinks" @change="updateState('export_accepted_links')"/>
          <label class="custom-control-label" :for="'export_accepted_links_' + type + '_' + spec.id">
            Accepted links
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="checkbox" class="custom-control-input" autocomplete="off"
                 :id="'export_rejected_links_' + type + '_' + spec.id"
                 v-model="exportRejectedLinks" @change="updateState('export_rejected_links')"/>
          <label class="custom-control-label" :for="'export_rejected_links_' + type + '_' + spec.id">
            Rejected links
          </label>
        </div>
      </sub-card>

      <sub-card label="RDF reification" class="col-export">
        <div class="custom-control custom-switch mt-3">
          <input type="radio" class="custom-control-input" autocomplete="off"
                 :id="'export_standard_reif_' + type + '_' + spec.id" value="standard" :disabled="format === 'csv'"
                 v-model="reification" @change="updateState('export_standard_reif')"/>
          <label class="custom-control-label" :for="'export_standard_reif_' + type + '_' + spec.id">
            Standard RDF reification
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="radio" class="custom-control-input" autocomplete="off"
                 :id="'export_rdf_star_reif_' + type + '_' + spec.id" value="star" :disabled="format === 'csv'"
                 v-model="reification" @change="updateState('export_rdf_star_reif')"/>
          <label class="custom-control-label" :for="'export_rdf_star_reif_' + type + '_' + spec.id">
            RDF*
          </label>
        </div>

        <div class="custom-control custom-switch">
          <input type="radio" class="custom-control-input" autocomplete="off"
                 :id="'export_singleton_reif_' + type + '_' + spec.id" value="singleton"
                 :disabled="true && format === 'csv'"
                 v-model="reification" @change="updateState('export_singleton_reif')"/>
          <label class="custom-control-label" :for="'export_singleton_reif_' + type + '_' + spec.id">
            Singleton
          </label>
        </div>
      </sub-card>

      <sub-card label="RDF link predicate" class="col-export">
        <v-select :value="selectedLinkPredicate" :options="linkPredicatesList"
                  :clearable="false" :disabled="format === 'csv'"
                  class="mt-3" autocomplete="off" placeholder="Select a link predicate" @input="selectLinkPredicate">
          <div slot="option" slot-scope="option">
            <div v-if="!option.predicate" class="text-secondary text-bold font-italic">
              Provide another link predicate
            </div>

            <template v-else>
              <div class="font-weight-bold">{{ option.label }}</div>
              <div class="text-muted text-wrap font-italic smaller pt-1">
                {{ option.uri + option.predicate }}
              </div>
            </template>
          </div>
        </v-select>

        <template v-if="!predicate">
          <div class="input-group input-group-sm mt-3">
            <div class="input-group-prepend">
              <span class="input-group-text">Namespace</span>
            </div>
            <input type="text" class="form-control" placeholder="Prefix" style="max-width:80px;"
                   v-model="prefix" :disabled="format === 'csv'"/>
            <input type="text" class="form-control" placeholder="URI"
                   v-model="uri" :disabled="format === 'csv'"/>
          </div>

          <div class="input-group input-group-sm mt-3">
            <div class="input-group-prepend">
              <span class="input-group-text">{{ prefix }}:</span>
            </div>
            <input type="text" class="form-control" placeholder="Match predicate"
                   v-model="predicate" :disabled="format === 'csv'"/>
          </div>
        </template>
      </sub-card>

      <sub-card label="Metadata" class="col-export">
        <div class="row form-group mt-3">
          <label :for="'creator_' + type + '_' + spec.id" class="col-auto">Creator:</label>
          <div class="col-auto">
            <input type="text" class="form-control form-control-sm" :id="'creator_' + type + '_' + spec.id"
                   v-model="creator" :disabled="format === 'csv'"/>
          </div>
        </div>

        <div class="row form-group mt-3">
          <label :for="'publisher_' + type + '_' + spec.id" class="col-auto">Publisher:</label>
          <div class="col-auto">
            <input type="text" class="form-control form-control-sm" :id="'publisher_' + type + '_' + spec.id"
                   v-model="publisher" :disabled="format === 'csv'"/>
          </div>
        </div>
      </sub-card>
    </div>

    <div class="row justify-content-end align-items-center pt-3 mb-0">
      <div class="col-auto">
        <b-button @click="doExport" variant="secondary">Export</b-button>
      </div>
    </div>
  </card>
</template>

<script>
    import props from "@/utils/props";

    const linkPredicates = Object.values(props.linkPredicates)
        .flatMap(linkPredicateScope => linkPredicateScope.predicates.map(pred => ({
            label: `${linkPredicateScope.prefix}:${pred}`,
            prefix: linkPredicateScope.prefix,
            uri: linkPredicateScope.uri,
            predicate: pred
        })))
        .sort((lpA, lpB) => {
            const prefixCmp = lpA.prefix.localeCompare(lpB.prefix);
            if (prefixCmp === 0)
                return lpA.predicate.localeCompare(lpB.predicate);

            return prefixCmp;
        });

    linkPredicates.push({
        label: 'Provide another link predicate',
        prefix: null,
        uri: null,
        predicate: null
    });

    export default {
        name: "Export",
        data() {
            return {
                format: 'turtle',
                exportLinkset: true,
                exportLinksMd: false,
                exportGenericMd: false,
                exportAllLinks: true,
                exportValidatedLinks: true,
                exportNotValidatedLinks: true,
                exportAcceptedLinks: true,
                exportRejectedLinks: true,
                reification: 'standard',
                linkPredicatesList: linkPredicates,
                selectedLinkPredicate: linkPredicates[0],
                prefix: linkPredicates[0].prefix,
                uri: linkPredicates[0].uri,
                predicate: linkPredicates[0].predicate,
                creator: null,
                publisher: null,
            }
        },
        props: {
            type: String,
            spec: Object,
        },
        computed: {
            isLensSpec() {
                return this.type === 'lens';
            },
        },
        methods: {
            updateState(type) {
                switch (type) {
                    case 'export_links_md':
                        if (this.exportLinksMd)
                            this.exportLinkset = true;
                        break;
                    case 'export_all_links':
                        this.exportValidatedLinks = this.exportAllLinks;
                        this.exportNotValidatedLinks = this.exportAllLinks;
                        this.exportAcceptedLinks = this.exportAllLinks;
                        this.exportRejectedLinks = this.exportAllLinks;
                        break;
                    case 'export_validated_links':
                        this.exportAcceptedLinks = this.exportValidatedLinks;
                        this.exportRejectedLinks = this.exportValidatedLinks;
                        this.exportAllLinks = this.exportValidatedLinks && this.exportNotValidatedLinks;
                        break;
                    case 'export_not_validated_links':
                        this.exportAllLinks = this.exportValidatedLinks && this.exportNotValidatedLinks;
                        break;
                    case 'export_accepted_links':
                    case 'export_rejected_links':
                        this.exportValidatedLinks = this.exportAcceptedLinks && this.exportRejectedLinks;
                        break;
                    case 'export_csv':
                        this.exportLinksMd = false;
                        this.exportGenericMd = false;
                        this.reification = 'standard';
                        break;
                }
            },

            selectLinkPredicate(linkPredicate) {
                this.selectedLinkPredicate = linkPredicate;
                this.prefix = linkPredicate.prefix;
                this.uri = linkPredicate.uri;
                this.predicate = linkPredicate.predicate;
            },

            doExport() {
                if (this.format === 'csv')
                    this.doCsvExport();
                else
                    this.doRdfExport();
            },

            doCsvExport() {
                const params = [];

                if (this.exportAcceptedLinks) params.push('valid=accepted');
                if (this.exportRejectedLinks) params.push('valid=rejected');
                if (this.exportNotValidatedLinks) params.push('valid=not_validated');
                if (this.exportAcceptedLinks && this.exportRejectedLinks) params.push('valid=mixed');

                this.$root.exportCsv(this.type, this.spec.id, params);
            },

            doRdfExport() {
                const params = [];

                params.push(`export_metadata=${this.exportGenericMd}`);
                params.push(`export_link_metadata=${this.exportLinksMd}`);
                params.push(`export_linkset=${this.exportLinkset}`);

                if (this.exportAcceptedLinks) params.push('valid=accepted');
                if (this.exportRejectedLinks) params.push('valid=rejected');
                if (this.exportNotValidatedLinks) params.push('valid=not_validated');
                if (this.exportAcceptedLinks && this.exportRejectedLinks) params.push('valid=mixed');

                params.push(`rdf_star=${this.reification === 'star'}`);
                params.push(`use_graphs=${this.format === 'trig'}`);

                params.push(`link_pred_namespace=${encodeURIComponent(this.uri)}`);
                params.push(`link_pred_shortname=${encodeURIComponent(this.prefix + ':' + this.predicate)}`);

                if (this.creator) params.push(`creator=${encodeURIComponent(this.creator)}`);
                if (this.publisher) params.push(`publisher=${encodeURIComponent(this.publisher)}`);

                this.$root.exportRdf(this.type, this.spec.id, params);
            }
        },
    };
</script>
