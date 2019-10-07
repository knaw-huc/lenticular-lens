<template>
  <div>
    <div v-if="research_form === 'new' || job_id" class="border p-4 mt-4 bg-light">
      <div class="form-group">
        <label class="h3" for="research">What is your research question?</label>
        <input type="text" class="form-control" id="research" v-model="title"
               v-bind:class="{'is-invalid': errors.includes('title')}" :disabled="is_updating">
        <div class="invalid-feedback" v-show="errors.includes('title')">
          Please indicate your research question
        </div>
      </div>

      <div class="form-group pt-3">
        <label class="h3" for="description">What is your research about?</label>
        <textarea class="form-control" id="description" v-model="description"
                  v-bind:class="{'is-invalid': errors.includes('description')}"
                  :disabled="is_updating"></textarea>
        <div class="invalid-feedback" v-show="errors.includes('description')">
          Please indicate what your research is about
        </div>
      </div>

      <div class="form-group row justify-content-end align-items-center pt-3 mb-0">
        <div class="col-auto" v-if="$root.job">
          <span class="badge badge-info" v-show="$root.job.created_at !== $root.job.updated_at">
            Updated {{ $root.job.updated_at | moment("MMMM Do YYYY, hh:mm:ss") }}
          </span>
        </div>

        <div class="col-auto">
          <b-button @click="saveResearch" variant="info">
            {{ job_id ? 'Update' : 'Create' }}
          </b-button>
        </div>
      </div>
    </div>

    <div v-if="research_form === 'existing' || job_id" class="bg-light border mt-4 p-4">
      <div class="row justify-content-end align-items-center">
        <span class="badge badge-info" ref="clipboard_copy_message" hidden>
            Job ID copied to clipboard
        </span>

        <template v-if="job_id">
          <label class="h3 col-auto" for="job_id_copy">Job ID</label>

          <input type="text" class="col-md-3 col-auto" id="job_id_copy" ref="job_id_copy" disabled v-model="job_id"/>

          <div class="col-auto">
            <b-button @click="copyToClipboard()">
              <fa-icon :icon="['far', 'clipboard']"/>
            </b-button>
          </div>
        </template>

        <template v-else>
          <label class="h3 col-auto" for="id_to_load">Existing Job ID</label>

          <input type="text" class="col-md-3 col-auto" id="id_to_load" v-model="id_to_load"/>

          <div class="col-auto">
            <b-button @click="$emit('load', id_to_load)" variant="info">Load</b-button>
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
                id_to_load: '',
                title: '',
                description: '',
            };
        },
        props: {
            job_id: String,
            job_title: String,
            job_description: String,
            research_form: String,
            is_updating: Boolean,
        },
        methods: {
            validateResearch() {
                const ideaValid = this.validateField('title', this.title);
                const descriptionValid = this.validateField('description', this.description);
                return ideaValid && descriptionValid;
            },

            saveResearch() {
                if (this.validateResearch()) {
                    const event = this.job_id ? 'update' : 'create';
                    this.$emit(event, {
                        job_id: this.job_id || undefined,
                        job_title: this.title,
                        job_description: this.description
                    });
                }
            },

            copyToClipboard() {
                const el = this.$refs.job_id_copy;
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

                this.$refs.clipboard_copy_message.removeAttribute('hidden');
                setTimeout(() => this.$refs.clipboard_copy_message.setAttribute('hidden', 'hidden'), 2000);
            },
        },
        watch: {
            job_title() {
                if (this.job_title)
                    this.title = this.job_title;
            },

            job_description() {
                if (this.job_description)
                    this.description = this.job_description;
            },
        },
    };
</script>