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
              <span class="badge badge-info">
                Created {{ $root.job.created_at | moment("MMMM Do YYYY, hh:mm:ss") }}
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

      <tab-content title="Collections" :before-change="validateCollectionsTab">
        <tab-content-structure title="Collections" :tab-error="tabError" :is-saved="isSaved">
          <template v-slot:header>
            <div class="col-auto">
              <button-add @click="addResource" title="Add a Collection" size="2x"/>
            </div>
          </template>

          <draggable v-model="$root.resources" group="resources" handle=".handle">
            <b-collapse v-for="(resource, index) in $root.resources"
                        :key="resource.id" :id="'resource_card_' + resource.id"
                        :visible="resourceOpen === resource.id || resourceOpen === null">
              <resource
                  :resource="resource"
                  @duplicate="duplicateResource($event)"
                  @remove="$root.resources.splice(index, 1)"
                  @show="resourceOpen = resource.id"
                  @hide="resourceOpen = null"
                  ref="resourceComponents"/>
            </b-collapse>
          </draggable>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Alignments" :before-change="validateAlignmentsTab">
        <tab-content-structure title="Alignments" :tab-error="tabError" :is-saved="isSaved">
          <template v-slot:header>
            <div class="col-auto">
              <button-add @click="addMatch" title="Add an Alignment" size="2x"/>
            </div>
          </template>

          <draggable v-model="$root.matches" group="matches" handle=".handle">
            <b-collapse v-for="(match, index) in $root.matches"
                        :key="match.id" :id="'match_card_' + match.id"
                        :visible="matchOpen === match.id || matchOpen === null">
              <match
                  :match="match"
                  @duplicate="duplicateMatch($event)"
                  @submit="submit"
                  @remove="$root.matches.splice(index, 1)"
                  @update:label="match.label = $event"
                  @show="matchOpen = match.id"
                  @hide="matchOpen = null"
                  ref="matchComponents"/>
            </b-collapse>
          </draggable>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Validation">
        <tab-content-structure title="Validation" :tab-error="tabError" :is-saved="isSaved">
          <b-collapse v-for="match in matchesWithResults"
                      :key="match.id" :id="'match_validation_card_' + match.id"
                      :visible="matchValidationOpen === match.id || matchValidationOpen === null">
            <match-validation
                :match="match"
                :key="match.id"
                @show="matchValidationOpen = match.id"
                @hide="matchValidationOpen = null"/>
          </b-collapse>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Export">
        <tab-content-structure title="Export" :tab-error="tabError" :is-saved="isSaved">
          <match-export
              v-for="match in matchesWithResults"
              :match="match"
              :key="match.id"/>
        </tab-content-structure>
      </tab-content>

      <template v-if="(props.activeTabIndex === 0  && !jobId) || [1,2].includes(props.activeTabIndex)"
                slot="next" slot-scope="props">
        <template v-if="props.activeTabIndex === 0 && !jobId">
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
    import Resource from './components/steps/resources/Resource';
    import Match from './components/steps/matches/Match';
    import MatchValidation from './components/steps/validation/MatchValidation';
    import MatchExport from './components/steps/export/MatchExport';

    import ValidationMixin from "./mixins/ValidationMixin";
    import TabContentStructure from './components/structural/TabContentStructure';

    export default {
        name: 'App',
        mixins: [ValidationMixin],
        components: {
            Draggable,
            TabContentStructure,
            Research,
            Resource,
            Match,
            MatchValidation,
            MatchExport,
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
                resourceOpen: null,
                matchOpen: null,
                matchValidationOpen: null,
                steps: ['research', 'collections', 'alignments', 'validation', 'export'],
            };
        },
        computed: {
            hasChanges() {
                return !Boolean(this.$root.job)
                    || JSON.stringify(this.$root.resources) !== JSON.stringify(this.$root.job['resources'])
                    || JSON.stringify(this.$root.matches) !== JSON.stringify(this.$root.job['mappings']);
            },

            matchesWithResults() {
                return this.$root.matches.filter(match => {
                    return this.$root.alignments.find(al => {
                        return al.alignment === match.id && al.status === 'done' && al.distinct_links_count > 0;
                    });
                });
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

            validateCollectionsTab(alwaysSave = false) {
                const results = this.$refs.resourceComponents
                    .map(resourceComponent => resourceComponent.validateResource());

                const isValid = results.includes(false)
                    ? this.isTabValid(false, alwaysSave, 'One or more resources contain errors!')
                    : this.isTabValid(this.$root.resources.length > 0, false, 'Please add at least one resource!');

                if (isValid || alwaysSave)
                    this.submit();

                return isValid;
            },

            validateAlignmentsTab(alwaysSave = false) {
                const results = this.$refs.matchComponents.map(matchComponent => matchComponent.validateMatch());

                const isValid = results.includes(false)
                    ? this.isTabValid(false, alwaysSave, 'One or more alignments contain errors!')
                    : this.isTabValid(this.$root.matches.length > 0, false, 'Please add at least one alignment!');

                if (isValid || alwaysSave)
                    this.submit();

                return isValid;
            },

            validateAndSave(activeTabIndex) {
                switch (activeTabIndex) {
                    case 1:
                        return this.validateCollectionsTab(true);
                    case 2:
                        return this.validateAlignmentsTab(true);
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

            addResource(event) {
                if (event) event.target.blur();
                this.$root.addResource();
            },

            addMatch(event) {
                if (event) event.target.blur();
                this.$root.addMatch();
            },

            duplicateResource(resource) {
                this.$root.duplicateResource(resource);
            },

            duplicateMatch(match) {
                this.$root.duplicateMatch(match);
            },

            async createJob(inputs) {
                const jobId = await this.$root.createJob(inputs);
                this.setJobId(jobId);
            },

            async updateJob(job_data) {
                this.isUpdating = true;

                await this.$root.updateJob(job_data);
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

                        this.activateStep('collections');

                        if (this.$root.resources.length === 0)
                            this.$root.addResource();

                        if (this.$root.matches.length === 0)
                            this.$root.addMatch();
                        else
                            this.activateStep('alignments');

                        this.refresh();
                    }
                }
            },

            async refresh(load = false) {
                if (load)
                    await Promise.all([this.$root.loadAlignments(), this.$root.loadClusterings()]);

                let hasFinished = false;
                let hasUnfinished = false;

                this.$root.alignments.forEach(alignment => {
                    if (alignment.status === 'done' && alignment.distinct_links_count > 0)
                        hasFinished = true;
                    else if (alignment.status !== 'done' && alignment.status !== 'failed')
                        hasUnfinished = true;
                });

                this.$root.clusterings.forEach(clustering => {
                    if (clustering.status !== 'done' && clustering.status !== 'failed')
                        hasUnfinished = true;
                });

                if (hasFinished) {
                    this.activateStep('validation');
                    this.activateStep('export');
                }

                if (hasUnfinished)
                    setTimeout(() => {
                        Promise.all([this.$root.loadAlignments(), this.$root.loadClusterings()])
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