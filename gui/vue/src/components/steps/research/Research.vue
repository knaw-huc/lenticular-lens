<template>
  <div>
    <div v-if="!isLoading && (researchForm === 'new' || $root.job)" class="border p-4 mt-4 bg-light">
      <div class="form-group">
        <label class="h3" for="research">Research Question</label>
        <textarea class="form-control" id="research" v-model="title"
                  v-bind:class="{'is-invalid': errors.includes('title')}" :disabled="isUpdating"></textarea>
        <small class="form-text text-muted mt-2">
          Write here your main research question
        </small>
        <div class="invalid-feedback" v-show="errors.includes('title')">
          Please indicate your research question
        </div>
      </div>

      <div class="form-group">
        <label class="h3" for="description">Hypothesis</label>
        <textarea class="form-control" id="description" v-model="description"
                  v-bind:class="{'is-invalid': errors.includes('description')}" :disabled="isUpdating"></textarea>
        <small class="form-text text-muted mt-2">
          Describe here your expectations and possibly your sub-research questions
        </small>
        <div class="invalid-feedback" v-show="errors.includes('description')">
          Please indicate what your research is about
        </div>
      </div>

      <div class="form-group">
        <label class="h3" for="link">Link</label>
        <input type="text" class="form-control" id="link" v-model="link" :disabled="isUpdating">
        <small class="form-text text-muted mt-2">
          Provide a link to the paper if this work gets published
        </small>
      </div>

      <div class="form-group row justify-content-end align-items-center pt-3 mb-0">
        <div class="col-auto" v-if="$root.job">
          <span class="badge badge-secondary" v-show="$root.job.created_at !== $root.job.updated_at">
            Updated {{ $root.job.updated_at | moment("MMMM Do YYYY, HH:mm:ss") }}
          </span>
        </div>

        <div class="col-auto">
          <b-button @click="saveResearch" variant="secondary">
            {{ $root.job ? 'Update' : 'Create' }}
          </b-button>
        </div>
      </div>
    </div>

    <div v-if="researchForm === 'existing' || jobId" class="bg-light border mt-4 p-4">
      <div class="row justify-content-end align-items-center">
        <loading v-if="isLoading"/>

        <failed v-else-if="failed" size="2x"/>

        <span class="badge badge-secondary" ref="clipboardCopyMessage" hidden>
          Job ID copied to clipboard
        </span>

        <template v-if="jobId && !failed">
          <label class="h3 col-auto" for="jobIdCopy">Job ID</label>

          <input type="text" class="form-control col-md-3 col-auto" id="jobIdCopy"
                 ref="jobIdCopy" disabled v-model="jobId"/>

          <div class="col-auto">
            <button class="btn btn-secondary" @click="copyToClipboard()">
              <fa-icon icon="copy"/>
            </button>
          </div>
        </template>

        <template v-else>
          <label class="h3 col-auto" for="id_to_load">Existing Job ID</label>

          <input type="text" class="col-md-3 col-auto" id="id_to_load" v-model="idToLoad"
                 v-on:keyup.enter="$emit('load', idToLoad)"/>

          <div class="col-auto">
            <b-button @click="$emit('load', idToLoad)" variant="secondary">Load</b-button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
    import ValidationMixin from '../../../mixins/ValidationMixin';

    export default {
        name: "Research",
        mixins: [ValidationMixin],
        data() {
            return {
                idToLoad: '',
                title: '',
                description: '',
                link: '',
            };
        },
        props: {
            jobId: String,
            jobTitle: String,
            jobDescription: String,
            jobLink: String,
            researchForm: String,
            isLoading: Boolean,
            isUpdating: Boolean,
        },
        computed: {
            failed() {
                return !this.isLoading && this.jobId && !this.$root.job;
            },
        },
        methods: {
            validateResearch() {
                const ideaValid = this.validateField('title', this.title);
                const descriptionValid = this.validateField('description', this.description);
                return ideaValid && descriptionValid;
            },

            saveResearch() {
                if (this.validateResearch()) {
                    const event = this.$root.job ? 'update' : 'create';
                    this.$emit(event, {
                        job_id: this.$root.job ? this.jobId : undefined,
                        job_title: this.title,
                        job_description: this.description,
                        job_link: this.link,
                    });
                }
            },

            copyToClipboard() {
                const el = this.$refs.jobIdCopy;
                const disabled = el.hasAttribute('disabled');
                if (disabled)
                    el.removeAttribute('disabled');

                const selected = document.getSelection().rangeCount > 0 ? document.getSelection().getRangeAt(0) : false;

                el.select();
                document.execCommand('copy');

                document.getSelection().removeAllRanges();
                if (selected)
                    document.getSelection().addRange(selected);

                if (disabled)
                    el.setAttribute('disabled', 'disabled');

                this.$refs.clipboardCopyMessage.removeAttribute('hidden');
                setTimeout(() => this.$refs.clipboardCopyMessage.setAttribute('hidden', 'hidden'), 2000);
            },
        },
        watch: {
            jobTitle() {
                if (this.jobTitle)
                    this.title = this.jobTitle;
            },

            jobDescription() {
                if (this.jobDescription)
                    this.description = this.jobDescription;
            },

            jobLink() {
                if (this.jobLink)
                    this.link = this.jobLink;
            },
        },
    };
</script>