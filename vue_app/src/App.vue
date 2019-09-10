<template>
  <div class="container" id="app">
    <form-wizard
        title="Lenticular Lenses II"
        subtitle="Reconcile data for Golden Agents"
        color="#efc501"
        shape="square"
        ref="formWizard">
      <tab-content title="Idea" :before-change="validateIdeaTab">
        <tab-content-structure title="Idea" :tab_error="tab_error" :is_saved="is_saved">
          <template v-slot:header>
            <div class="col-auto" v-if="$root.job">
              <span class="badge badge-info">Created {{ $root.job.created_at }}</span>
            </div>
          </template>

          <idea
              :job_id="job_id"
              :job_title="job_title"
              :job_description="job_description"
              :idea_form="idea_form"
              :is_updating="is_updating"
              @load="setJobId($event)"
              @create="createJob($event)"
              @update="updateJob($event)"
          ></idea>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Collections" :before-change="validateCollectionsTab">
        <tab-content-structure title="Collections" :tab_error="tab_error" :is_saved="is_saved">
          <template v-slot:header>
            <div class="col-auto">
              <button-add @click="addResource" title="Add a Collection" size="2x"/>
            </div>
          </template>

          <draggable v-model="$root.resources" group="resources" handle=".handle">
            <resource
                v-for="(resource, index) in $root.resources"
                :key="resource.id"
                :resource="resource"
                @duplicate="duplicateResource($event)"
                @remove="$root.resources.splice(index, 1)"
                ref="resourceComponents"/>
          </draggable>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Alignments" :before-change="validateAlignmentsTab">
        <tab-content-structure title="Alignment Specifications" :tab_error="tab_error" :is_saved="is_saved">
          <template v-slot:header>
            <div class="col-auto">
              <button-add @click="addMatch" title="Add an Alignment" size="2x"/>
            </div>
          </template>

          <draggable v-model="$root.matches" group="matches" handle=".handle">
            <match
                v-for="(match, index) in $root.matches"
                :match="match"
                :key="match.id"
                @duplicate="duplicateMatch($event)"
                @submit="submit"
                @remove="$root.matches.splice(index, 1)"
                @update:label="match.label = $event"
                @refresh="refresh(true)"
                ref="matchComponents"/>
          </draggable>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Validation">
        <tab-content-structure title="Validation" :tab_error="tab_error" :is_saved="is_saved">
          <match-validation
              v-if="$root.alignments.find(al => al.alignment === match.id && al.status === 'Finished')"
              v-for="match in $root.matches"
              :match="match"
              :key="match.id"
          ></match-validation>
        </tab-content-structure>
      </tab-content>

      <tab-content title="Export">
        <tab-content-structure title="Export" :tab_error="tab_error" :is_saved="is_saved"></tab-content-structure>
      </tab-content>

      <template v-if="(props.activeTabIndex === 0  && !job_id) || [1,2].includes(props.activeTabIndex)"
                slot="next" slot-scope="props">
        <template v-if="props.activeTabIndex === 0 && !job_id">
          <wizard-button
              :style="props.fillButtonStyle"
              :disabled="props.loading || idea_form === 'existing'"
              @click.native.prevent.stop="idea_form='existing'">
            Existing Idea
          </wizard-button>
          &nbsp;
          <wizard-button
              v-if="hasChanges"
              :style="props.fillButtonStyle"
              :disabled="props.loading || idea_form === 'new'"
              @click.native.prevent.stop="idea_form='new'">
            New Idea
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

    import Idea from './components/steps/idea/Idea';
    import Resource from './components/steps/resources/Resource';
    import Match from './components/steps/matches/Match';
    import MatchValidation from './components/steps/validation/MatchValidation';

    import ValidationMixin from "./mixins/ValidationMixin";
    import TabContentStructure from './components/structural/TabContentStructure';

    export default {
        name: 'App',
        mixins: [ValidationMixin],
        components: {
            Draggable,
            TabContentStructure,
            Idea,
            Resource,
            Match,
            MatchValidation,
        },
        data() {
            return {
                tab_error: '',
                idea_form: '',
                id_to_load: '',
                job_id: '',
                job_title: '',
                job_description: '',
                is_saved: true,
                is_updating: false,
                steps: ['idea', 'collections', 'alignments', 'validation', 'export'],
            };
        },
        computed: {
            hasChanges() {
                return !Boolean(this.$root.job)
                    || JSON.stringify(this.$root.resources) !== JSON.stringify(this.$root.job['resources_form_data'])
                    || JSON.stringify(this.$root.matches) !== JSON.stringify(this.$root.job['mappings_form_data']);
            },
        },
        methods: {
            isTabValid(isValid, isSaved, message) {
                this.tab_error = isValid ? '' : message;
                this.is_saved = isSaved;
                return !!isValid;
            },

            validateIdeaTab() {
                return this.isTabValid(this.$root.job, false, 'Please update or create your idea first!');
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
                this.is_updating = true;

                await this.$root.updateJob(job_data);
                await this.getJobData();

                this.is_updating = false;
            },

            async setJobId(job_id) {
                this.$set(this, 'job_id', job_id);

                let parsedUrl = new URL(window.location.href);
                parsedUrl.searchParams.set('job_id', job_id);
                window.history.pushState(null, null, parsedUrl.href);

                await this.getJobData();
            },

            async submit() {
                await this.$root.submit();
                await this.getJobData();
            },

            async getJobData() {
                if (this.job_id !== '') {
                    await this.$root.loadJob(this.job_id);

                    if (this.$root.job) {
                        this.job_title = this.$root.job.job_title;
                        this.job_description = this.$root.job.job_description;

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
                    if (alignment.status === 'Finished')
                        hasFinished = true;
                    else if (!alignment.status.startsWith('FAILED'))
                        hasUnfinished = true;
                });

                this.$root.clusterings.forEach(clustering => {
                    if (clustering.status !== 'Finished' && !clustering.status.startsWith('FAILED'))
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
                    }, 5000);
            },
        },
        async mounted() {
            await this.$root.loadDatasets();

            const urlParams = new URLSearchParams(window.location.search);
            const job_id = urlParams.get('job_id');
            if (job_id) {
                this.job_id = job_id;
                this.idea_form = 'existing';
                this.getJobData();
            }
        },
    };
</script>