<template>
<div class="container" id="app">
    <form @submit.prevent="submitForm" action="" method="post">
    <form-wizard
        title="Lenticular Lenses II"
        subtitle="Reconcile data for Golden Agents"
        color="#efc501"
        shape="square"
        ref="formWizard"
    >

        <tab-content title="Idea">
            <div class="h2">Idea</div>
            <div v-if="idea_form === 'new' ||  job_id" class="border p-4 mt-4 bg-light">
                <div class="form-group">
                    <label class="h3" for="idea">What's your idea?</label>
                    <input type="text" class="form-control" id="idea" v-model="inputs.job_title">
                </div>

                <div class="form-group pt-3">
                    <label class="h3" for="description">Describe your idea</label>
                    <textarea class="form-control" id="description" v-model="inputs.job_description"></textarea>
                </div>

                <div class="form-group row justify-content-end pt-3 mb-0">
                    <div class="col-auto">
                        <b-button @click="saveIdea" variant="info">{{ job_id ? 'Update' : 'Create' }}</b-button>
                    </div>
                </div>
            </div>

            <div v-if="idea_form === 'existing' || job_id" class="bg-light border mt-4 pl-4 pr-4 pt-4">
                <div class="form-group row justify-content-end">
                    <label class="h3 col-auto" for="job_id_input">{{ job_id ? '' : 'Existing ' }}Job ID</label>
                    <input type="text" class="form-control col-md-3 col-auto" ref="job_id_input" id="job_id_input" :disabled="Boolean(job_id)" v-model="inputs.job_id">

                    <div v-if="!job_id" class="form-group col-auto">
                        <b-button @click="setJobId(inputs.job_id)" variant="info">Load</b-button>
                    </div>
                    <div v-else class="col-auto">
                        <b-button @click="copyToClipboard($refs['job_id_input'])"><octicon name="clippy" class="align-text-top"></octicon></b-button>
                    </div>
                </div>
                <div class="row justify-content-end mb-0" ref="clipboard_copy_message" hidden>
                    <div class="col-auto text-success">
                        Job ID copied to clipboard.
                    </div>
                </div>
            </div>
        </tab-content>

        <tab-content title="Collections">
        <div id="resources">
            <h2>Collections</h2>
            <resource-component
                    :initial_label="'Collection ' + resource.id"
                    :resource="resource"
                    :datasets="datasets"
                    :resources="resources"
                    v-for="(resource, index) in resources"
                    :key="resource.id"
                    v-on:remove="resources.splice(index, 1)"
                    @update:label="resource.label = $event"
            ></resource-component>

            <div class="form-group mt-4">
                <button v-on:click="addResource" type="button" class="add-resource form-control btn btn-primary w-25">
                    + Add Collection
                </button>
            </div>
        </div>
        </tab-content>

        <tab-content title="Alignments">
        <div id="matches" class="mt-5">
            <div class="row justify-content-between">
                <div class="col-auto">
                    <h2>Alignment Specifications</h2>
                </div>
                <div class="col-auto">
                    <div class="form-group mb-0 pr-2 pt-3">
                        <button-add @click="addMatch" title="Add an Alignment"/>
                    </div>
                </div>
            </div>

            <match-component
                    :match="match"
                    :matches="matches"
                    v-for="(match, index) in matches"
                    :key="match.id"
                    @remove="matches.splice(index, 1)"
                    @update:label="match.label = $event"
            ></match-component>
        </div>
        </tab-content>

        <tab-content title="Link Validation">
        <div v-if="job_data">
            <div>
                Request received at: {{ job_data.requested_at }}
            </div>
            <div>
                Status: <pre>{{ job_data.status }}</pre>
            </div>
            <div v-if="job_data.processing_at">
                Processing started at: {{ job_data.processing_at }}
            </div>
            <div v-if="job_data.finished_at">
                Processing finished at: {{ job_data.finished_at }}
                <div v-for="match in matches">
                    <a :href="'/job/' + job_id + '/result/' + match.label" target="_blank">Results for {{ match.label }}</a>
                </div>
                <div>
                    <a :href="'/job/' + job_id + '/result/download'" download>Download RDF</a>
                </div>
            </div>
        </div>
        </tab-content>

        <tab-content title="Clusters">
            <div class="border p-4 mt-4 bg-light"
                 v-for="match in matches"
                 v-if="!match.is_association"
            >
                <div class="row justify-content-between">
                    <div class="col-auto">
                        <octicon name="chevron-down" scale="3" v-b-toggle="'clustering_clusters_match_' + match.id"></octicon>
                    </div>

                    <div class="col align-self-center" v-b-toggle="'clustering_clusters_match_' + match.id">
                        <div class="h2">{{ match.label }}</div>
                    </div>

                    <div v-if="getResultForMatch(match.label).clusterings.length > 0" class="col-auto align-self-center">
                        <div class="h3 text-success">Clustered</div>
                    </div>

                    <div class="col-auto">
                        <button v-if="getResultForMatch(match.label).clusterings.length > 0" type="button" class="btn btn-info" @click="createClustering(match.label, $event)" :disabled="association === ''" :title="association === '' ? 'Choose an association first' : ''">Reconcile</button>
                        <button v-if="getResultForMatch(match.label).clusterings.length === 0" type="button" class="btn btn-info" @click="createClustering(match.label, $event)">Cluster<template v-if="association !== ''"> &amp; Reconcile</template></button>
                    </div>

                    <div v-if="job_data" class="col-auto align-self-center form-group">
                        <select class="form-control" v-model="association" :id="'match_' + match.id + '_association'">
                            <option value="">No association</option>
                            <option v-for="association_file_name in job_data.association_files" :value="association_file_name">{{ association_file_name }}</option>
                        </select>
                    </div>
                </div>

                <div class="row" v-if="getResultForMatch(match.label).clusterings.length > 0">
                    <div class="col-5">
                        <div class="row">
                            <div class="col-6">
                                Clusters:
                            </div>
                            <div class="col-6">
                                {{ getResultForMatch(match.label).clusterings[0].clusters_count }}
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-6">
                                Extended Clusters:
                            </div>
                            <div class="col-6">
                                {{ getResultForMatch(match.label).clusterings[0].extended_count }}
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-6">
                                Clusters with Cycles:
                            </div>
                            <div class="col-6">
                                {{ getResultForMatch(match.label).clusterings[0].cycles_count }}
                            </div>
                        </div>
                    </div>
                    <div class="col-5">
                        <div class="row">
                            <div class="col-6">
                                Clusters not Extended:
                            </div>
                            <div class="col-6">
                                {{ getResultForMatch(match.label).clusterings[0].clusters_count - getResultForMatch(match.label).clusterings[0].extended_count }}
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-6">
                                Clusters without Cycles:
                            </div>
                            <div class="col-6">
                                {{ getResultForMatch(match.label).clusterings[0].clusters_count - getResultForMatch(match.label).clusterings[0].cycles_count }}
                            </div>
                        </div>
                    </div>
                </div>

                <b-collapse
                        @show="getClusters(getResultForMatch(match.label).clusterings[0].clustering_id)"
                        class="row border-bottom mb-5"
                        :id="'clustering_clusters_match_' + match.id"
                        accordion="clusters-matches-accordion"
                >
                    <div class="col-md-12">
                        <div id="clustering_dataset_linking_stats_cluster_results" style="height: 20em; width:100%; scroll: both; overflow: auto;">
                            <table class="table table-striped" id="clustering_resultTable" style="height: 20em; scroll: both; overflow: auto;">
                                <thead>
                                    <tr>
                                        <th>Ext</th>
                                        <th>Rec</th>
                                        <th>ID</th>
                                        <th>count</th>
                                        <th>size</th>
                                        <th>prop</th>
                                        <th>sample</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <cluster-table-row-component
                                            v-for="(cluster_data, cluster_id) in clusters"
                                            :key="'clustering_cluster_' + cluster_id"
                                            :cluster_id="cluster_id"
                                            :cluster_data="cluster_data"
                                            @select:cluster_id="cluster_id_selected = $event"
                                    />
                                </tbody>
                            </table>
                        </div>
                    </div>
                </b-collapse>
            </div>
            <template v-if="cluster_id_selected">
                <cluster-visualization-component
                        parent_tab="clusters"
                        :clustering_id="clustering_id"
                        :cluster_id="cluster_id_selected"
                        :cluster_data="clusters[cluster_id_selected]"
                />
            </template>
        </tab-content>

        <tab-content title="Cluster Validation">
            <template v-if="job_data">
                <div class="border mb-5 p-3">
                    <div class="border p-4 mt-4 bg-light"
                         v-for="match in matches"
                         v-if="!match.is_association"
                    >
                        <div class="row justify-content-between">
                            <div class="col-auto">
                                <octicon name="chevron-down" scale="3" v-b-toggle="'clusters_match_' + match.id"></octicon>
                            </div>

                            <div class="col align-self-center" v-b-toggle="'clusters_match_' + match.id">
                                <div class="h2">{{ match.label }}</div>
                            </div>

                            <div class="col-auto align-self-center" v-b-toggle="'clusters_match_' + match.id">
                                <div v-if="getResultForMatch(match.label).clusterings.length > 0" class="h3 text-success">Clustered</div>
                                <div v-else class="h3 text-danger">Not clustered</div>
                            </div>
                        </div>
                        <b-collapse
                                @show="getClusters(getResultForMatch(match.label).clusterings[0].clustering_id)"
                                class="row border-bottom mb-5"
                                :id="'clusters_match_' + match.id"
                                accordion="clusters-matches-accordion"
                        >
                            <div class="col-md-12">
                                <div id="dataset_linking_stats_cluster_results" style="height: 20em; width:100%; scroll: both; overflow: auto;">
                                    <table class="table table-striped" id="resultTable" style="height: 20em; scroll: both; overflow: auto;">
                                        <thead>
                                            <tr>
                                                <th>Ext</th>
                                                <th>ID</th>
                                                <th>count</th>
                                                <th>size</th>
                                                <th>prop</th>
                                                <th>sample</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <cluster-table-row-component
                                                    v-for="(cluster_data, cluster_id) in clusters"
                                                    :cluster_id="cluster_id"
                                                    :cluster_data="cluster_data"
                                                    @select:cluster_id="cluster_id_selected = $event"
                                            />
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </b-collapse>
                    </div>
                </div>

                <template v-if="cluster_id_selected">
                    <cluster-visualization-component
                            parent_tab="cluster_validation"
                            :clustering_id="clustering_id"
                            :cluster_id="cluster_id_selected"
                            :cluster_data="clusters[cluster_id_selected]"
                    />
                </template>
            </template>
        </tab-content>

        <template v-if="(props.activeTabIndex === 0  && !job_id) || props.activeTabIndex === 2" slot="next" scope="props">
            <template v-if="props.activeTabIndex === 2">
                <wizard-button
                        v-if="job_data"
                        :style="props.fillButtonStyle"
                        :disabled="props.loading">
                    Results
                </wizard-button>
                &nbsp;
                <wizard-button
                        v-if="has_changes"
                        :style="props.fillButtonStyle"
                        :disabled="props.loading"
                        @click.native="submitForm">
                    Run Job
                 </wizard-button>
            </template>

            <template v-if="props.activeTabIndex === 0 && !job_id">
                <wizard-button
                        :style="props.fillButtonStyle"
                        :disabled="props.loading || idea_form === 'existing'"
                        @click.native.prevent.stop="idea_form='existing'"
                >
                    Existing Idea
                </wizard-button>
                &nbsp;
                <wizard-button
                        v-if="has_changes"
                        :style="props.fillButtonStyle"
                        :disabled="props.loading || idea_form === 'new'"
                        @click.native.prevent.stop="idea_form='new'"
                >
                    New Idea
                 </wizard-button>
            </template>
        </template>
        <template slot="finish" scope="props" style="display: none">&#8203;</template>
    </form-wizard>
    </form>
</div>
</template>

<script>
    import Resource from './components/Resource'
    import Match from './components/Match'
    import ClusterVisualizationComponent from "./components/ClusterVisualization";
    import ClusterTableRowComponent from "./components/ClusterTableRow";

    export default {
        name: 'app',
        components: {
            ClusterTableRowComponent,
            ClusterVisualizationComponent,
            'resource-component': Resource,
            'match-component': Match,
        },
        computed: {
            has_changes() {
                return !Boolean(this.job_data)
                    || JSON.stringify(this.resources) !== JSON.stringify(this.job_data['resources_form_data'])
                    || JSON.stringify(this.matches) !== JSON.stringify(this.job_data['mappings_form_data'])
            },
        },
        data() {
            return {
                association: '',
                cluster_id_selected: null,
                clustering_id: null,
                clusters: [],
                datasets: [],
                idea_form: '',
                inputs: {
                    job_id: '',
                    job_title: '',
                    job_description: '',
                },
                job_id: '',
                job_data: null,
                resources: [],
                resources_count: 0,
                limit_all: -1,
                matches: [],
                matches_count: 0,
                steps: [
                    'idea',
                    'collections',
                    'alignments',
                    'link_validation',
                    'clusters',
                    'cluster_validation',
                ],
            }
        },
        methods: {
            activateStep(step_name, jump=false) {
                let step_index = this.steps.indexOf(step_name);

                if (step_index < 0 || typeof this.$refs['formWizard'].tabs[step_index] === 'undefined')
                    return false;

                for (let i = 0; i <= step_index; i++) {
                    this.$set(this.$refs['formWizard'].tabs[i], 'checked', true);
                }

                this.$set(this.$refs['formWizard'], 'maxStep', step_index);

                if (jump) {
                    this.$refs['formWizard'].changeTab(this.$refs['formWizard'].activeTabIndex, step_index);
                }
            },
            addFilterCondition(resource) {
                let condition = {
                    'type': '',
                    'property': '',
                };
                resource.filter.conditions.push(condition);
            },
            addResource(event) {
                if (event) {
                    event.target.blur();
                }
                this.resources_count ++;
                let resource = {
                    dataset_id: '',
                    collection_id: '',
                    'id': this.resources_count,
                    'filter': {
                        'type': 'AND',
                        'conditions': [],
                    },
                    limit: -1,
                    related: [],
                    related_array: false,
                };
                this.resources.push(resource);
            },
            addMatch(event) {
                if (event) {
                    event.target.blur();
                }
                this.matches_count++;
                let match = {
                    'id': this.matches.length,
                    'is_association': false,
                    'label': 'Alignment ' + (this.matches.length + 1),
                    'sources': [],
                    'targets': [],
                    'conditions': {
                        'type': 'AND',
                        'items': [],
                    },
                };
                this.matches.push(match);
            },
            applyLimitAll() {
                this.resources.forEach(resource => {
                    this.$set(resource, 'limit', this.limit_all);
                });
            },
            clearForm() {
                this.resources = [];
                this.matches = [];
                this.resources_count = 0;
                this.matches_count = 0;
                this.association = '';
                this.cluster_id_selected = null;
                this.clustering_id = null;
                this.limit_all = -1;
            },
            copyToClipboard(el) {
                let disabled = el.hasAttribute('disabled');
                if (disabled) {
                    el.removeAttribute('disabled');
                }

                let selected = document.getSelection().rangeCount > 0 ? document.getSelection().getRangeAt(0) : false;

                el.select();
                document.execCommand('copy');

                document.getSelection().removeAllRanges();
                if (selected) {
                    document.getSelection().addRange(selected);
                }

                if (disabled) {
                    el.setAttribute('disabled', 'disabled');
                }

                this.$refs['clipboard_copy_message'].removeAttribute('hidden');
                setTimeout(() => {
                    this.$refs['clipboard_copy_message'].setAttribute('hidden', 'hidden');
                }, 2000)
            },
            createClustering(mapping_label, event) {
                let btn = event.target;
                btn.setAttribute('disabled', 'disabled');

                fetch('/job/' + this.job_id + '/create_clustering/',
                    {
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                        },
                        method: "POST",
                        body: JSON.stringify({
                            'mapping_label': mapping_label,
                            'association_file': this.association,
                            'clustered': this.getResultForMatch(mapping_label).clusterings.length > 0,
                        })
                    })
                    .then((response) => response.json())
                    .then((data) => {
                        this.getJobData();
                    });
            },
            createJob() {
                fetch("/job/create/",
                    {
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                        },
                        method: "POST",
                        body: JSON.stringify(this.inputs),
                    }
                )
                    .then((response) => response.json())
                    .then((data) => {
                        this.setJobId(data.job_id);
                    }
                );
            },
            getClusters(clustering_id) {
                this.clustering_id = clustering_id;

                fetch('/job/' + this.job_id + '/clusters/' + clustering_id + '?association=' + this.association)
                    .then((response) => response.json())
                    .then((data) => {
                        this.clusters = data;
                    });
            },
            getDatasets() {
                let vue = this;
                fetch('/datasets')
                    .then((response) => response.json())
                    .then((data) => {
                        // Make internal references for referenced collections
                        Object.keys(data).forEach(dataset_name => {
                            let dataset = data[dataset_name];
                            Object.keys(dataset.collections).forEach(collection_name => {
                                let collection = dataset.collections[collection_name];
                                Object.keys(collection).forEach(property_name => {
                                    let property = collection[property_name];
                                    if (typeof property['referencedCollections'] !== 'undefined') {
                                        let referenced_collections = property['referencedCollections'];
                                        property['referencedCollections'] = {};
                                        referenced_collections = referenced_collections.filter(ref_collection_name => {
                                            return ref_collection_name !== 'tim_unknown'
                                        });
                                        referenced_collections.forEach(ref_collection_name => {
                                            property['referencedCollections'][ref_collection_name] = dataset.collections[ref_collection_name];
                                        });
                                    }
                                });
                            });
                        });

                        vue.datasets = data;

                        let urlParams = new URLSearchParams(window.location.search);
                        let job_id = urlParams.get('job_id');
                        if (job_id) {
                            this.job_id = job_id;
                            this.idea_form = 'existing';
                            this.$set(this.inputs, 'job_id', job_id);
                            this.getJobData();
                        }
                    });
            },
            getJobData() {
                if (this.job_id !== '') {
                    fetch('/job/' + this.job_id)
                        .then((response) => response.json())
                        .then((data) => {
                            this.job_data = JSON.parse(JSON.stringify(data));

                            this.$set(this.inputs, 'job_title', data.job_title);
                            this.$set(this.inputs, 'job_description', data.job_description);

                            this.activateStep('collections');

                            if (this.resources_count < 1) {
                                if (data.resources_form_data) {
                                    this.resources = data.resources_form_data;
                                    this.resources_count = this.resources.length;
                                } else {
                                    this.addResource();
                                }
                            }

                            if (this.matches.length < 1) {
                                if (data.mappings_form_data) {
                                    this.matches = data.mappings_form_data;
                                    this.activateStep('alignments');
                                } else {
                                    this.addMatch();
                                }
                            }

                            if (this.job_data.status) {
                                this.activateStep(this.job_data.status === 'Finished' ? 'clusters' : 'cluster_validation');

                                if (this.job_data.status !== 'Finished' && !this.job_data.status.startsWith('FAILED')) {
                                    setTimeout(this.getJobData, 5000);
                                }
                            }
                        })
                    ;
                }
            },
            getMatchById(match_id) {
                for (let i = 0; i < this.matches.length; i++) {
                    if (this.matches[i].id == match_id)
                        return this.matches[i];
                }
            },
            getResourceById(resource_id, resources = this.resources) {
                for (let i = 0; i < resources.length; i++) {
                    if (resources[i].id == resource_id || resources[i].label === resource_id)
                        return resources[i];
                }
            },
            getResultForMatch(match_label) {
                let clusterings = [];

                if (this.job_data) {
                    this.job_data.results.clusterings.forEach(clustering => {
                        if (clustering.mapping_name === match_label) {
                            clusterings.push(clustering);
                        }
                    });
                }

                return {
                    'clusterings': clusterings,
                }
            },
            getOrCreate(subject, key, default_value) {
                if (typeof subject[key] === 'undefined') {
                    this.$set(subject, key, default_value);
                }

                return subject[key];
            },
            saveIdea() {
                if (this.job_id) {
                    this.updateJob(this.inputs);
                } else {
                    this.createJob();
                }
            },
            setJobId(job_id) {
                this.$set(this, 'job_id', job_id);
                this.$set(this.inputs, 'job_id', job_id);

                let parsedUrl = new URL(window.location.href);
                parsedUrl.searchParams.set('job_id', job_id);
                window.history.pushState(null, null, parsedUrl.href);

                this.clearForm();
                this.getJobData();
            },
            submitForm() {
                let vue = this;
                function get_value(value_object, target_object) {
                    if (value_object.value_type === 'property') {
                        let converted_property = create_references_for_property(value_object.property);

                        let resource_label = converted_property[0] == parseInt(converted_property[0]) ?
                            vue.getResourceById(converted_property[0]).label :
                            converted_property[0];

                        target_object.property = [
                            resource_label,
                            converted_property[1].toLowerCase()
                        ];
                    }

                    let exclude_keys = ['', 'function_name', 'property', 'transformers', 'value_type'];

                    if (value_object.value_type === 'function') {
                        if (Array.isArray(value_object[value_object.function_name])) {
                            target_object[value_object.function_name] = [];
                            value_object[value_object.function_name].forEach(parameter_object => {
                                let target_parameter_object = {};
                                target_object[value_object.function_name].push(get_value(parameter_object, target_parameter_object))
                            });
                        } else {
                            target_object[value_object.function_name] = {};
                            if (value_object[value_object.function_name].value_type === '') {
                                Object.keys(value_object[value_object.function_name]).forEach(field_name => {
                                    if (exclude_keys.indexOf(field_name) < 0) {
                                        target_object[value_object.function_name][field_name] = {};
                                        target_object[value_object.function_name][field_name] = get_value(value_object[value_object.function_name][field_name], target_object[value_object.function_name][field_name]);
                                    }
                                });
                            } else {
                                target_object[value_object.function_name] = get_value(value_object[value_object.function_name], target_object[value_object.function_name])
                            }
                        }
                    }

                    if (value_object.value_type === '') {
                        Object.keys(value_object).forEach(field_name => {
                            if (exclude_keys.indexOf(field_name) < 0) {
                                target_object[field_name] = {};
                                target_object[field_name] = get_value(value_object[field_name], target_object[field_name]);
                            }
                        });
                    }

                    if (value_object.transformers && value_object.transformers.length > 0) {
                        target_object.transformers = value_object.transformers;
                    }

                    return target_object;
                }

                function create_references_for_property(property) {
                    // Check if reference
                    if (property.length > 2) {
                        // Don't follow reference if user selected 'Value'
                        if (property[2] === '__value__') {
                            return property.slice(0, 2)
                        }

                        let base_referenced_resource = vue.getResourceById(property[0], resources_copy);

                        // Add resource
                        let referenced_resource = {
                            "collection_id": property[2],
                            "dataset_id": base_referenced_resource.dataset_id,
                            "related": []
                        };
                        referenced_resource['label'] = vue.$utilities.md5(property[0] + property[1] + JSON.stringify(referenced_resource));

                        let resource_exists = false;
                        resources_copy.forEach(rc => {
                            if (rc.label === referenced_resource.label) {
                                resource_exists = true;
                                return false
                            }
                        });
                        if (!resource_exists) {
                            resources_copy.push(referenced_resource);
                        }

                        // Add relation
                        let relation = {
                            "resource": referenced_resource.label,
                            "local_property": property[1],
                            "remote_property": "uri"
                        };
                        let relation_exists = false;
                        base_referenced_resource.related.forEach(existing_relation => {
                            if (JSON.stringify(existing_relation) === JSON.stringify(relation)) {
                                relation_exists = true;
                                return false
                            }
                        });
                        if (!relation_exists) {
                            base_referenced_resource.related.push(relation);
                        }

                        if (base_referenced_resource.related.length > 1) {
                            base_referenced_resource.related_array = true;
                        }

                        // Replace part of property that was processed and re-enter the function with that output
                        return create_references_for_property([referenced_resource.label, property[3].toLowerCase()].concat(property.slice(4)))
                    }

                    return property
                }

                function get_recursive_conditions(filter_obj) {
                    let conditions = [];
                    let obj_arr;

                    if (Array.isArray(filter_obj)) {
                        obj_arr = filter_obj;
                    } else if (Array.isArray(filter_obj.conditions)) {
                        obj_arr = filter_obj.conditions;
                    }

                    if (obj_arr) {
                        obj_arr.forEach(condition => {
                            conditions = conditions.concat(get_recursive_conditions(condition));
                        });
                        return conditions;
                    } else {
                        return [filter_obj]
                    }
                }

                let resources = [];
                let resources_copy = JSON.parse(JSON.stringify(this.resources));
                let matches_copy = JSON.parse(JSON.stringify(this.matches));

                // Check for references
                resources_copy.forEach(resource_copy => {
                    if (resource_copy.filter.type) {
                        get_recursive_conditions(resource_copy.filter.conditions).forEach(condition => {
                            condition.property = create_references_for_property(condition.property);
                        });
                    }
                });

                matches_copy.forEach(match_copy => {
                    delete match_copy['id'];

                    ['sources', 'targets'].forEach(resources_key => {
                        match_copy[resources_key].forEach((resource_id, resource_index) => {
                            match_copy[resources_key][resource_index] = this.getResourceById(resource_id).label;
                        });
                    });

                    match_copy.conditions.items.forEach(condition => {
                        delete condition['id'];
                        delete condition['method_index'];

                        // For method parameter type "matching_label", replace match IDs with labels
                        if (typeof condition['method'] === 'object') {
                            Object.keys(condition['method']).forEach(method_name => {
                                let method_parameters = condition['method'][method_name];
                                let new_parameters;

                                if (Array.isArray(method_parameters)) {
                                    new_parameters = [];
                                    method_parameters.forEach(parameter => {
                                        if (typeof parameter === 'object' && parameter.type === "matching_label") {
                                            new_parameters.push(this.getMatchById(parameter.value).label);
                                        } else {
                                            new_parameters.push(parameter);
                                        }
                                    });
                                } else {
                                    new_parameters = {};
                                    Object.keys(method_parameters).forEach(parameter_key => {
                                        let parameter = method_parameters[parameter_key];
                                        if (typeof parameter === 'object' && parameter.type === "matching_label") {
                                            new_parameters[parameter_key] = this.getMatchById(parameter.value);
                                        } else {
                                            new_parameters[parameter_key] = parameter;
                                        }
                                    });
                                }
                                condition['method'][method_name] = new_parameters;
                            });
                        }

                        ['sources', 'targets'].forEach(resources_key => {
                            Object.keys(condition[resources_key]).forEach(resource_id => {
                                condition[resources_key][resource_id].forEach((property, property_index) => {
                                    condition[resources_key][resource_id][property_index].property = create_references_for_property(property.property);
                                    condition[resources_key][resource_id][property_index].property.forEach((property_part, property_part_index) => {
                                        if (property_part > 0) {
                                            condition[resources_key][resource_id][property_index].property[property_part_index] = this.getResourceById(property_part).label;
                                        }
                                    });
                                });

                                condition[resources_key][this.getResourceById(resource_id).label] = condition[resources_key][resource_id];
                                delete condition[resources_key][resource_id];
                            });
                        });
                    });
                });

                resources_copy.forEach(resource_copy => {
                    if (resource_copy.filter && resource_copy.filter.type) {
                        get_recursive_conditions(resource_copy.filter.conditions).forEach(condition => {
                            if (condition.property[0] == parseInt(condition.property[0])) {
                                condition.property[0] = this.getResourceById(condition.property[0]).label;
                            }
                            condition.property[1] = condition.property[1].toLowerCase();
                            if (typeof condition.value_type !== 'undefined') {
                                condition[condition.value_type] = condition.value;
                                delete condition.value;
                                delete condition.value_type;
                            }
                        });
                    } else {
                        delete resource_copy.filter;
                    }

                    if (resource_copy.related) {
                        resource_copy.related.forEach(related => {
                            if (related.resource == parseInt(related.resource)) {
                                related.resource = this.getResourceById(related.resource).label;
                            }
                            related.local_property = [related.local_property.toLowerCase()];
                            related.remote_property = [related.remote_property.toLowerCase()];
                            delete related.resource_index;
                        });

                        if (resource_copy.related_array) {
                            resource_copy.related = [resource_copy.related]
                        }
                    }

                    delete resource_copy.related_array;
                    let resource_copy_copy = JSON.parse(JSON.stringify(resource_copy));
                    delete resource_copy_copy.id;

                    resources.push(resource_copy_copy);
                });

                let data = {
                    'resources': resources,
                    'matches': matches_copy,
                    'resources_original': this.resources,
                    'matches_original': this.matches,
                    'status': 'Requested',
                };

                Object.keys(this.inputs).forEach(key => {
                    data[key] = this.inputs[key];
                });

                this.updateJob(data);
            },
            updateJob(job_data) {
                fetch("/job/update/",
                    {
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                        },
                        method: "POST",
                        body: JSON.stringify(job_data),
                    }
                )
                    .then((response) => response.json())
                    .then((data) => {
                        this.getJobData();
                    }
                );
            },
        },
        mounted() {
            this.getDatasets();
        },
    };
</script>