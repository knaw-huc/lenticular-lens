<template>
  <div class="container" id="app">
    <form-wizard
        title="Lenticular Lenses"
        subtitle="Reconcile data for Golden Agents"
        color="#efc501"
        shape="square"
        ref="formWizard">
      <tab-content title="Research" :before-change="validateResearchTab">
        <tab-content-structure title="Research" :tab-error="tabError" :is-saved="isSaved">
          <template v-slot:header>
            <div class="col-auto" v-if="$root.job">
              <span class="badge badge-secondary">
                Created {{ $root.job.created_at | moment("MMMM Do YYYY, HH:mm:ss") }}
              </span>
            </div>
          </template>

          <research
              :job-id="jobId"
              :job-title="jobTitle"
              :job-description="jobDescription"
              :job-link="jobLink"
              :research-form="researchForm"
              :is-loading="isLoading"
              :is-updating="isUpdating"
              @load="setJobId($event)"
              @create="createJob($event)"
              @update="updateJob($event)"/>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Entity-type selections" :before-change="validateEntityTypeSelectionsTab">
        <tab-content-structure title="Entity-type selections" :tab-error="tabError" :is-saved="isSaved">
          <template v-slot:header>
            <div v-if="entityTypeSelectionOpen === null" class="col-auto">
              <button-add @click="addEntityTypeSelection" title="Add an Entity-type selection" size="2x"/>
            </div>
          </template>

          <draggable v-model="$root.entityTypeSelections" group="entityTypeSelections" handle=".handle">
            <b-collapse v-for="(entityTypeSelection, index) in $root.entityTypeSelections"
                        :key="entityTypeSelection.id" :id="'entity_type_selection_card_' + entityTypeSelection.id"
                        :visible="entityTypeSelectionOpen === entityTypeSelection.id || entityTypeSelectionOpen === null">
              <entity-type-selection
                  :entity-type-selection="entityTypeSelection"
                  @duplicate="duplicateEntityTypeSelection($event)"
                  @remove="$root.entityTypeSelections.splice(index, 1)"
                  @show="entityTypeSelectionOpen = entityTypeSelection.id"
                  @hide="entityTypeSelectionOpen = null"
                  ref="entityTypeSelectionComponents"/>
            </b-collapse>
          </draggable>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Linkset specs" :before-change="validateLinksetSpecsTab">
        <tab-content-structure title="Linkset specs" :tab-error="tabError" :is-saved="isSaved">
          <template v-slot:header>
            <div v-if="linksetSpecOpen === null" class="col-auto">
              <button-add @click="addLinksetSpec" title="Add a Linkset Spec" size="2x"/>
            </div>
          </template>

          <draggable v-model="$root.linksetSpecs" group="linksetSpecs" handle=".handle">
            <b-collapse v-for="linksetSpec in $root.linksetSpecs"
                        :key="linksetSpec.id" :id="'linkset_spec_card_' + linksetSpec.id"
                        :visible="linksetSpecOpen === linksetSpec.id || linksetSpecOpen === null">
              <linkset
                  :linkset-spec="linksetSpec"
                  :allow-delete="!specsUsedInLens.find(spec => spec.type === 'linkset' && spec.id === linksetSpec.id)"
                  @duplicate="duplicateLinksetSpec($event)"
                  @submit="submit"
                  @remove="removeSpec('linkset', linksetSpec.id)"
                  @update:label="linksetSpec.label = $event"
                  @show="linksetSpecOpen = linksetSpec.id"
                  @hide="linksetSpecOpen = null"
                  ref="linksetSpecComponents"/>
            </b-collapse>
          </draggable>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Lens specs" :before-change="validateLensSpecsTab">
        <tab-content-structure title="Lens specs" :tab-error="tabError" :is-saved="isSaved">
          <template v-slot:header>
            <div v-if="lensSpecOpen === null" class="col-auto">
              <button-add @click="addLensSpec" title="Add a Lens Spec" size="2x"/>
            </div>
          </template>

          <draggable v-model="$root.lensSpecs" group="lensSpecs" handle=".handle">
            <b-collapse v-for="lensSpec in $root.lensSpecs"
                        :key="lensSpec.id" :id="'lens_spec_card_' + lensSpec.id"
                        :visible="lensSpecOpen === lensSpec.id || lensSpecOpen === null">
              <lens
                  :lens-spec="lensSpec"
                  :allow-delete="!specsUsedInLens.find(spec => spec.type === 'lens' && spec.id === lensSpec.id)"
                  @duplicate="duplicateLensSpec($event)"
                  @submit="submit"
                  @remove="removeSpec('lens', lensSpec.id)"
                  @update:label="lensSpec.label = $event"
                  @show="lensSpecOpen = lensSpec.id"
                  @hide="lensSpecOpen = null"
                  ref="lensSpecComponents"/>
            </b-collapse>
          </draggable>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Validation">
        <tab-content-structure title="Validation" :tab-error="tabError" :is-saved="isSaved">
          <b-collapse v-for="spec in specsWithResults"
                      :key="spec.uid" :id="'validation_card_' + spec.uid"
                      :visible="validationOpen === spec.uid || validationOpen === null">
            <validation
                :type="spec.type"
                :spec="spec.spec"
                :key="spec.uid"
                @show="validationOpen = spec.uid"
                @hide="validationOpen = null"/>
          </b-collapse>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Export">
        <tab-content-structure title="Export" :tab-error="tabError" :is-saved="isSaved">
          <export
              v-for="spec in specsWithResults"
              :type="spec.type"
              :spec="spec.spec"
              :key="spec.uid"/>
        </tab-content-structure>
      </tab-content>

      <template v-if="(props.activeTabIndex === 0  && !$root.job) || [1,2,3].includes(props.activeTabIndex)"
                slot="next" slot-scope="props">
        <template v-if="props.activeTabIndex === 0 && !$root.job">
          <wizard-button
              :style="props.fillButtonStyle"
              :disabled="props.loading || researchForm === 'existing'"
              @click.native.prevent.stop="researchForm='existing'">
            Existing research
          </wizard-button>
          &nbsp;
          <wizard-button
              v-if="hasChanges"
              :style="props.fillButtonStyle"
              :disabled="props.loading || researchForm === 'new'"
              @click.native.prevent.stop="researchForm='new'">
            New research
          </wizard-button>
        </template>

        <template v-if="[1,2,3].includes(props.activeTabIndex)">
          <wizard-button
              v-if="hasChanges && [1,2].includes(props.activeTabIndex)"
              :style="props.fillButtonStyle"
              :disabled="props.loading"
              @click.native.stop="validateAndSave(props.activeTabIndex)">
            Save
          </wizard-button>

          <wizard-button
              :style="props.fillButtonStyle"
              :disabled="props.loading">
            Save and next
          </wizard-button>
        </template>
      </template>

      <template slot="finish" slot-scope="props" style="display: none">&#8203;</template>
    </form-wizard>
  </div>
</template>

<script>
    import Draggable from 'vuedraggable';
    import {EventBus} from './eventbus.js';

    import Research from './components/steps/research/Research';
    import EntityTypeSelection from './components/steps/entity_type_selections/EntityTypeSelection';
    import Linkset from './components/steps/linksets/Linkset';
    import Lens from './components/steps/lenses/Lens';
    import Validation from './components/steps/validation/Validation';
    import Export from './components/steps/export/Export';

    import ValidationMixin from "./mixins/ValidationMixin";
    import TabContentStructure from './components/structural/TabContentStructure';

    export default {
        name: 'App',
        mixins: [ValidationMixin],
        components: {
            Draggable,
            TabContentStructure,
            Research,
            EntityTypeSelection,
            Linkset,
            Lens,
            Validation,
            Export,
        },
        data() {
            return {
                tabError: '',
                researchForm: '',
                idToLoad: '',
                jobId: '',
                jobTitle: '',
                jobDescription: '',
                jobLink: '',
                isSaved: true,
                isLoading: false,
                isUpdating: false,
                isDownloading: false,
                entityTypeSelectionOpen: null,
                linksetSpecOpen: null,
                lensSpecOpen: null,
                validationOpen: null,
                steps: ['research', 'entityTypeSelections', 'linksetSpecs', 'lensSpecs', 'validation', 'export'],
            };
        },
        computed: {
            hasChanges() {
                return !Boolean(this.$root.job)
                    || JSON.stringify(this.$root.entityTypeSelections) !== JSON.stringify(this.$root.job['entity_type_selections'])
                    || JSON.stringify(this.$root.linksetSpecs) !== JSON.stringify(this.$root.job['linkset_specs'])
                    || JSON.stringify(this.$root.lensSpecs) !== JSON.stringify(this.$root.job['lens_specs']);
            },

            specsWithResults() {
                const linksetSpecs = this.$root.linksetSpecs.filter(linksetSpec => {
                    return this.$root.linksets.find(linkset => {
                        return linkset.spec_id === linksetSpec.id
                            && linkset.status === 'done' && linkset.distinct_links_count > 0;
                    });
                });

                const lensSpecs = this.$root.lensSpecs.filter(lensSpec => {
                    return this.$root.lenses.find(lens => {
                        return lens.spec_id === lensSpec.id && lens.status === 'done' && lens.distinct_links_count > 0;
                    });
                });

                return [
                    ...linksetSpecs.map(linksetSpec => ({
                        uid: `linkset_${linksetSpec.id}`,
                        type: 'linkset',
                        spec: linksetSpec,
                    })),
                    ...lensSpecs.map(lensSpec => ({
                        uid: `lensSpec_${lensSpec.id}`,
                        type: 'lens',
                        spec: lensSpec,
                    }))
                ];
            },

            specsUsedInLens() {
                const specsInLens = lensSpec => this.$root
                    .getRecursiveElements(lensSpec.specs, 'elements')
                    .flatMap(elem => {
                        if (elem.type === 'lens') {
                            const elemLensSpec = this.$root.getLensSpecById(elem.id);
                            if (elemLensSpec)
                                return [({type: 'lens', id: elemLensSpec.id}), ...specsInLens(elemLensSpec)];
                        }
                        else if (elem.type === 'linkset') {
                            const elemLinksetSpec = this.$root.getLinksetSpecById(elem.id);
                            if (elemLinksetSpec)
                                return [({type: 'linkset', id: elemLinksetSpec.id})];
                        }

                        return [];
                    });

                const specs = this.$root.lensSpecs.reduce((acc, lensSpec) => acc.concat(specsInLens(lensSpec)), []);
                return [...new Set(specs)];
            },
        },
        methods: {
            isTabValid(isValid, isSaved, message) {
                this.tabError = isValid ? '' : message;
                this.isSaved = isSaved;
                return !!isValid;
            },

            validateResearchTab() {
                return this.isTabValid(this.$root.job, false, 'Please update or create your research first!');
            },

            validateEntityTypeSelectionsTab(alwaysSave = false) {
                const results = this.$refs.entityTypeSelectionComponents
                    .map(entityTypeSelectionComponent => entityTypeSelectionComponent.validateEntityTypeSelection());

                const isValid = results.includes(false)
                    ? this.isTabValid(false, alwaysSave,
                        'One or more entity-type selections contain errors!')
                    : this.isTabValid(this.$root.entityTypeSelections.length > 0, false,
                        'Please add at least one entity-type selection!');

                if (isValid || alwaysSave)
                    this.submit();

                return isValid;
            },

            validateLinksetSpecsTab(alwaysSave = false) {
                const results = this.$refs.linksetSpecComponents
                    .map(linksetSpecComponent => linksetSpecComponent.validateLinkset());

                const isValid = results.includes(false)
                    ? this.isTabValid(false, alwaysSave,
                        'One or more linkset specs contain errors!')
                    : this.isTabValid(this.$root.linksetSpecs.length > 0, false,
                        'Please add at least one linkset spec!');

                if (isValid || alwaysSave)
                    this.submit();

                return isValid;
            },

            validateLensSpecsTab(alwaysSave = false) {
                const results = this.$refs.lensSpecComponents
                    ? this.$refs.lensSpecComponents.map(lensSpecComponent => lensSpecComponent.validateLens())
                    : [];

                const isValid = this.isTabValid(!results.includes(false), alwaysSave,
                    'One or more lensSpec specs contain errors!');
                if (isValid || alwaysSave)
                    this.submit();

                return isValid;
            },

            validateAndSave(activeTabIndex) {
                switch (activeTabIndex) {
                    case 1:
                        return this.validateEntityTypeSelectionsTab(true);
                    case 2:
                        return this.validateLinksetSpecsTab(true);
                    case 3:
                        return this.validateLensSpecsTab(true);
                    default:
                        return false;
                }
            },

            activateStep(stepName, jump = false) {
                const stepIndex = this.steps.indexOf(stepName);
                if (stepIndex < 0 || typeof this.$refs.formWizard.tabs[stepIndex] === 'undefined')
                    return false;

                for (let i = 0; i <= stepIndex; i++)
                    this.$set(this.$refs.formWizard.tabs[i], 'checked', true);

                this.$set(this.$refs.formWizard, 'maxStep', stepIndex);

                if (jump)
                    this.$refs.formWizard.changeTab(this.$refs.formWizard.activeTabIndex, stepIndex);
            },

            addEntityTypeSelection() {
                this.$root.addEntityTypeSelection();
            },

            addLinksetSpec() {
                this.$root.addLinksetSpec();
            },

            addLensSpec() {
                this.$root.addLensSpec();
            },

            duplicateEntityTypeSelection(entityTypeSelection) {
                this.$root.duplicateEntityTypeSelection(entityTypeSelection);
            },

            duplicateLinksetSpec(linksetSpec) {
                this.$root.duplicateLinksetSpec(linksetSpec);
            },

            duplicateLensSpec(lensSpec) {
                this.$root.duplicateLensSpec(lensSpec);
            },

            async createJob(inputs) {
                const jobId = await this.$root.createJob(inputs);
                await this.setJobId(jobId);
            },

            async updateJob(jobData) {
                this.isUpdating = true;

                await this.$root.updateJob(jobData);
                await this.getJobData();

                this.isUpdating = false;
            },

            async setJobId(jobId, fromUrl = false) {
                this.jobId = jobId;
                this.isLoading = true;

                if (!fromUrl) {
                    const parsedUrl = new URL(window.location.href);
                    parsedUrl.searchParams.set('job_id', jobId);
                    window.history.pushState(null, null, parsedUrl.href);
                }
                else {
                    this.researchForm = 'existing';
                }

                await this.getJobData();

                this.isLoading = false;
            },

            async submit() {
                await this.$root.submit();
                await this.getJobData();
            },

            async getJobData() {
                if (this.jobId !== '') {
                    await this.$root.loadJob(this.jobId);

                    if (this.$root.job) {
                        this.jobTitle = this.$root.job.job_title;
                        this.jobDescription = this.$root.job.job_description;
                        this.jobLink = this.$root.job.job_link;

                        this.activateStep('entityTypeSelections');

                        if (this.$root.entityTypeSelections.length === 0)
                            this.$root.addEntityTypeSelection();

                        if (this.$root.linksetSpecs.length === 0)
                            this.$root.addLinksetSpec();
                        else
                            this.activateStep('linksetSpecs');

                        this.refresh();
                    }
                }
            },

            async refresh(load = false) {
                if (load)
                    await Promise.all([this.$root.loadLinksets(), this.$root.loadLenses(), this.$root.loadClusterings()]);

                let hasFinished = false;
                let hasUnfinished = false;

                this.$root.linksets.forEach(linkset => {
                    if (linkset.status === 'done' && linkset.distinct_links_count > 0)
                        hasFinished = true;
                    else if (linkset.status !== 'done' && linkset.status !== 'failed')
                        hasUnfinished = true;
                });

                this.$root.lenses.forEach(lens => {
                    if (lens.status !== 'done' && lens.status !== 'failed')
                        hasUnfinished = true;
                });

                this.$root.clusterings.forEach(clustering => {
                    if (clustering.status !== 'done' && clustering.status !== 'failed')
                        hasUnfinished = true;
                });

                if (hasFinished) {
                    this.activateStep('lensSpecs');
                    this.activateStep('validation');
                    this.activateStep('export');
                }

                if (hasUnfinished)
                    setTimeout(() => {
                        Promise.all([this.$root.loadLinksets(), this.$root.loadLenses(), this.$root.loadClusterings()])
                            .then(() => this.refresh());
                    }, 2000);
            },

            async refreshDownloadsInProgress(externalTrigger = false) {
                if (externalTrigger && this.isDownloading)
                    return;

                this.isDownloading = true;
                await this.$root.loadDownloadsInProgress();

                if (this.$root.downloading.length > 0)
                    setTimeout(_ => this.refreshDownloadsInProgress(), 2000);
                else
                    this.isDownloading = false;
            },

            async removeSpec(type, id) {
                if (this.specsUsedInLens.find(spec => spec.type === type && spec.id === id))
                    return;

                if (confirm(`Are you sure you want to delete this ${type}?`)) {
                    if (type === 'linkset') {
                        if (this.$root.linksets.find(linkset => linkset.spec_id === id))
                            if (!(await this.$root.deleteResult(type, id))) return;

                        const index = this.$root.linksetSpecs.findIndex(linkset => linkset.id === id);
                        this.$root.linksetSpecs.splice(index, 1);

                        await this.submit();
                    }
                    else if (type === 'lens') {
                        if (this.$root.lenses.find(lens => lens.spec_id === id))
                            if (!(await this.$root.deleteResult(type, id))) return;

                        const index = this.$root.lensSpecs.findIndex(lens => lens.id === id);
                        this.$root.lensSpecs.splice(index, 1);

                        await this.submit();
                    }
                }
            },
        },
        mounted() {
            const urlParams = new URLSearchParams(window.location.search);

            const hsid = urlParams.get('hsid');
            if (hsid) {
                window.opener.postMessage({'timbuctoo-hsid': hsid});
                return;
            }

            const jobId = urlParams.get('job_id');
            if (jobId)
                this.setJobId(jobId, true);

            this.refreshDownloadsInProgress();
            this.$root.loadAssociationFiles();

            EventBus.$on('refresh', _ => this.refresh(true));
            EventBus.$on('refreshDownloadsInProgress', _ => this.refreshDownloadsInProgress(true));
        },
    };
</script>