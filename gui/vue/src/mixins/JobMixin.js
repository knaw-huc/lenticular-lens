export default {
    data() {
        return {
            job: null,
            linksets: [],
            lenses: [],
            clusterings: [],
            entityTypeSelections: [],
            linksetSpecs: [],
            lensSpecs: [],
            views: [],
            datasets: {},
            downloaded: [],
            downloading: [],
        };
    },
    methods: {
        getDatasets(graphqlEndpoint) {
            return this.datasets.hasOwnProperty(graphqlEndpoint) ? this.datasets[graphqlEndpoint] : {};
        },

        addEntityTypeSelection() {
            this.entityTypeSelections.unshift({
                id: findId(this.entityTypeSelections),
                description: '',
                dataset: {
                    dataset_id: '',
                    collection_id: '',
                    timbuctoo_graphql: 'https://repository.goldenagents.org/v5/graphql',
                },
                filter: {
                    type: 'AND',
                    conditions: [],
                },
                limit: -1,
                random: false,
                properties: [],
            });
        },

        addLinksetSpec() {
            this.linksetSpecs.unshift({
                id: findId(this.linksetSpecs),
                label: 'Linkset ' + (this.linksetSpecs.length + 1),
                description: '',
                use_counter: true,
                sources: [],
                targets: [],
                threshold: 0,
                methods: {
                    type: 'AND',
                    conditions: [],
                },
            });
        },

        addLensSpec() {
            this.lensSpecs.unshift({
                id: findId(this.lensSpecs),
                label: 'Lens ' + (this.lensSpecs.length + 1),
                description: '',
                specs: {
                    type: 'UNION',
                    t_conorm: '',
                    threshold: 0,
                    elements: [],
                },
            });
        },

        addView(id, type) {
            this.views.unshift({
                id: id,
                type: type,
                properties: [],
                filters: [],
            });
        },

        duplicateEntityTypeSelection(entityTypeSelection) {
            const index = this.entityTypeSelections.findIndex(res => res.id === entityTypeSelection.id);
            this.entityTypeSelections.splice(index, 0, {
                ...copy(entityTypeSelection),
                id: findId(this.entityTypeSelections),
                label: undefined,
            });
        },

        duplicateLinksetSpec(linksetSpec) {
            const linksetIdx = this.linksetSpecs.findIndex(m => m.id === linksetSpec.id);
            const newLinksetSpec = {
                ...copy(linksetSpec),
                id: findId(this.linksetSpecs),
                label: 'Linkset ' + (this.linksetSpecs.length + 1),
            };

            this.linksetSpecs.splice(linksetIdx, 0, newLinksetSpec);

            const viewIdx = this.views.findIndex(view => view.id === linksetSpec.id && view.type === 'linkset');
            if (viewIdx > -1)
                this.views.splice(viewIdx, 0, {
                    ...copy(this.views[viewIdx]),
                    id: newLinksetSpec.id,
                });
        },

        duplicateLensSpec(lensSpec) {
            const lensIdx = this.lensSpecs.findIndex(m => m.id === lensSpec.id);
            const newLensSpec = {
                ...copy(lensSpec),
                id: findId(this.lensSpecs),
                label: 'Lens ' + (this.lensSpecs.length + 1),
            };

            this.lensSpecs.splice(lensIdx, 0, newLensSpec);

            const viewIdx = this.views.findIndex(view => view.id === lensSpec.id && view.type === 'lens');
            if (viewIdx > -1)
                this.views.splice(viewIdx, 0, {
                    ...copy(this.views[viewIdx]),
                    id: newLensSpec.id,
                });
        },

        getEntityTypeSelectionById(id) {
            return this.entityTypeSelections.find(res => res.id === parseInt(id));
        },

        getLinksetSpecById(id) {
            return this.linksetSpecs.find(linksetSpec => linksetSpec.id === parseInt(id));
        },

        getLensSpecById(id) {
            return this.lensSpecs.find(lensSpec => lensSpec.id === parseInt(id));
        },

        getViewByIdAndType(id, type) {
            return this.views.find(view => view.id === parseInt(id) && view.type === type);
        },

        exportCsv(type, id, params) {
            window.open(`/job/${this.job.job_id}/csv/${type}/${id}?${params.join('&')}`);
        },

        exportRdf(type, id, params) {
            window.open(`/job/${this.job.job_id}/rdf/${type}/${id}?${params.join('&')}`);
        },

        getRecursiveElements(element, groupName) {
            let elements;
            if (Array.isArray(element))
                elements = element;
            else if (Array.isArray(element[groupName]))
                elements = element[groupName];

            if (elements)
                return elements.reduce((acc, element) => acc.concat(this.getRecursiveElements(element, groupName)), []);

            return [element];
        },

        async submit() {
            await this.updateJob({
                job_id: this.job.job_id,
                job_title: this.job.job_title,
                job_description: this.job.job_description,
                job_link: this.job.job_link,
                entity_type_selections: this.entityTypeSelections,
                linkset_specs: this.linksetSpecs,
                lens_specs: this.lensSpecs,
                views: this.views,
            });
        },

        async loadJob(id) {
            const job = await callApi('/job/' + id);
            if (!job)
                return;

            job.created_at = job.created_at ? new Date(job.created_at) : null;
            job.updated_at = job.updated_at ? new Date(job.updated_at) : null;
            this.job = job;

            if (this.job.entity_type_selections) {
                const entityTypeSelections = copy(this.job.entity_type_selections);

                const graphQlEndpoints = entityTypeSelections
                    .map(ets => ets.dataset.timbuctoo_graphql)
                    .filter((data, idx, res) => res.findIndex(data2 => data2 === data) === idx);
                await Promise.all(graphQlEndpoints.map(data => this.loadDatasets(data)));

                entityTypeSelections.forEach(entityTypeSelection => {
                    delete entityTypeSelection.dataset.published;
                    delete entityTypeSelection.dataset.timbuctoo_hsid;
                    delete entityTypeSelection.related;
                    delete entityTypeSelection.related_array;

                    if (entityTypeSelection.filter)
                        this.getRecursiveElements(entityTypeSelection.filter, 'conditions')
                            .forEach(filter => {
                                switch (filter.type) {
                                    case '=':
                                        filter.type = 'equals';
                                        break;
                                    case '!=':
                                        filter.type = 'not_equals';
                                        break;
                                    case 'is_null':
                                        filter.type = 'empty';
                                        break;
                                    case 'not_null':
                                        filter.type = 'not_empty';
                                        break;
                                    case 'ilike':
                                        filter.type = 'contains';
                                        break;
                                    case 'not_ilike':
                                        filter.type = 'not_contains';
                                        break;
                                }
                            });
                });

                this.entityTypeSelections = entityTypeSelections;
            }

            if (this.job.views)
                this.views = copy(this.job.views);

            if (this.job.linkset_specs) {
                const linksetSpecs = copy(this.job.linkset_specs);

                linksetSpecs.forEach(linksetSpec => {
                    delete linksetSpec.is_association;
                    delete linksetSpec.threshold;

                    this.getRecursiveElements(linksetSpec.methods, 'conditions').forEach(method => {
                        if (method.hasOwnProperty('list_matching')
                            && method.list_matching.hasOwnProperty('links_threshold')) {
                            method.list_matching.threshold = method.list_matching.links_threshold;
                            method.list_matching.is_percentage = method.list_matching.links_is_percentage;

                            delete method.list_matching.links_threshold;
                            delete method.list_matching.links_is_percentage;
                            delete method.list_matching.unique_threshold;
                            delete method.list_matching.unique_is_percentage;
                            delete method.list_matching.source_threshold;
                            delete method.list_matching.source_is_percentage;
                            delete method.list_matching.target_threshold;
                            delete method.list_matching.target_is_percentage;
                        }
                        else if (method.hasOwnProperty('list_threshold')) {
                            method.list_matching = {
                                threshold: method.list_threshold,
                                is_percentage: method.list_threshold_unit === 'percentage'
                            };

                            delete method.list_threshold;
                            delete method.list_threshold_unit;
                        }

                        if (!method.hasOwnProperty('list_matching')) {
                            method.list_matching = {
                                threshold: 0,
                                is_percentage: false,
                            };
                        }

                        if (method.method_name === 'TIME_DELTA'
                            && method.method_config.hasOwnProperty('multiplier')) {
                            method.method_config.type = '<>';
                            method.method_config.years = 0;
                            method.method_config.months = 0;

                            delete method.method_config.multiplier;
                        }

                        if (method.method_name === 'INTERMEDIATE'
                            && !Array.isArray(method.method_config.intermediate_source[0])) {
                            method.method_config.intermediate_source = [method.method_config.intermediate_source];
                            method.method_config.intermediate_target = [method.method_config.intermediate_target];
                        }

                        if (Array.isArray(method.sources)) {
                            method.sources = method.sources.reduce((acc, source) => {
                                if (!acc.hasOwnProperty(source.entity_type_selection))
                                    acc[source.entity_type_selection] = [];

                                acc[source.entity_type_selection].push({
                                    property: source.property,
                                    transformers: source.transformers,
                                });

                                return acc;
                            }, {});
                        }

                        if (Array.isArray(method.targets)) {
                            method.targets = method.targets.reduce((acc, target) => {
                                if (!acc.hasOwnProperty(target.entity_type_selection))
                                    acc[target.entity_type_selection] = [];

                                acc[target.entity_type_selection].push({
                                    property: target.property,
                                    transformers: target.transformers,
                                });

                                return acc;
                            }, {});
                        }

                        if (!method.sources.hasOwnProperty('transformers')) {
                            method.sources = {
                                properties: method.sources,
                                transformers: []
                            };
                        }

                        if (!method.targets.hasOwnProperty('transformers')) {
                            method.targets = {
                                properties: method.targets,
                                transformers: []
                            };
                        }

                        delete method.transformers;

                        Object.values(method.sources.properties).forEach(properties => {
                            properties.forEach(prop => {
                                prop.property_transformer_first = false;
                                if (prop.hasOwnProperty('stopwords')) {
                                    if (prop.stopwords.dictionary !== '')
                                        prop.transformers.push({name: 'STOPWORDS', parameters: prop.stopwords});
                                    delete prop.stopwords;
                                }
                            });
                        });

                        Object.values(method.targets.properties).forEach(properties => {
                            properties.forEach(prop => {
                                prop.property_transformer_first = false;
                                if (prop.hasOwnProperty('stopwords')) {
                                    if (prop.stopwords.dictionary !== '')
                                        prop.transformers.push({name: 'STOPWORDS', parameters: prop.stopwords});
                                    delete prop.stopwords;
                                }
                            });
                        });

                        if (method.hasOwnProperty('method_name')) {
                            method.method = {
                                name: method.method_name,
                                config: method.method_config,
                            };

                            delete method.method_name;
                            delete method.method_config;
                        }

                        if (method.hasOwnProperty('method_sim_name')) {
                            method.sim_method = {
                                name: method.method_sim_name,
                                config: method.method_sim_config,
                                normalized: method.method_sim_normalized,
                            };

                            delete method.method_sim_name;
                            delete method.method_sim_config;
                            delete method.method_sim_normalized;
                        }

                        if (method.hasOwnProperty('t_conorm')) {
                            method.fuzzy = {
                                t_conorm: method.t_conorm,
                                threshold: method.threshold,
                            };

                            delete method.t_conorm;
                            delete method.threshold;
                        }
                    });

                    if (linksetSpec.hasOwnProperty('properties')) {
                        if (!this.getViewByIdAndType(linksetSpec.id, 'linkset'))
                            this.addView(linksetSpec.id, 'linkset');

                        const view = this.getViewByIdAndType(linksetSpec.id, 'linkset');
                        linksetSpec.properties.forEach(prop => {
                            const ets = this.$root.getEntityTypeSelectionById(prop.entity_type_selection);
                            const propsIdx = view.properties.findIndex(viewProp =>
                                viewProp.timbuctoo_graphql === ets.dataset.timbuctoo_graphql &&
                                viewProp.dataset_id === ets.dataset.dataset_id &&
                                viewProp.collection_id === ets.dataset.collection_id
                            );

                            if (propsIdx < 0)
                                view.properties.push({
                                    timbuctoo_graphql: ets.dataset.timbuctoo_graphql,
                                    dataset_id: ets.dataset.dataset_id,
                                    collection_id: ets.dataset.collection_id,
                                    properties: [prop.property]
                                });
                            else
                                view.properties[propsIdx].properties.push(prop.property);
                        });

                        delete linksetSpec.properties;
                    }
                });

                this.linksetSpecs = linksetSpecs;
            }

            if (this.job.lens_specs) {
                const lensSpecs = copy(this.job.lens_specs);

                lensSpecs.forEach(lensSpec => {
                    if (lensSpec.hasOwnProperty('properties')) {
                        if (!this.getViewByIdAndType(lensSpec.id, 'lens'))
                            this.addView(lensSpec.id, 'lens');

                        const view = this.getViewByIdAndType(lensSpec.id, 'lens');
                        lensSpec.properties.forEach(prop => {
                            const ets = this.$root.getEntityTypeSelectionById(prop.entity_type_selection);
                            const propsIdx = view.properties.findIndex(viewProp =>
                                viewProp.timbuctoo_graphql === ets.dataset.timbuctoo_graphql &&
                                viewProp.dataset_id === ets.dataset.dataset_id &&
                                viewProp.collection_id === ets.dataset.collection_id
                            );

                            if (propsIdx < 0)
                                view.properties.push({
                                    timbuctoo_graphql: ets.dataset.timbuctoo_graphql,
                                    dataset_id: ets.dataset.dataset_id,
                                    collection_id: ets.dataset.collection_id,
                                    properties: [prop.property]
                                });
                            else
                                view.properties[propsIdx].properties.push(prop.property);
                        });

                        delete lensSpec.properties;
                    }
                });

                this.lensSpecs = lensSpecs;
            }

            await Promise.all([this.loadLinksets(), this.loadLenses(), this.loadClusterings()]);
        },

        async loadLinksets() {
            const linksets = await callApi(`/job/${this.job.job_id}/linksets`);
            linksets.forEach(linkset => {
                linkset.requested_at = linkset.requested_at ? new Date(linkset.requested_at) : null;
                linkset.processing_at = linkset.processing_at ? new Date(linkset.processing_at) : null;
                linkset.finished_at = linkset.finished_at ? new Date(linkset.finished_at) : null;
            });
            this.linksets = linksets;
        },

        async loadLenses() {
            const lenses = await callApi(`/job/${this.job.job_id}/lenses`);
            lenses.forEach(lens => {
                lens.requested_at = lens.requested_at ? new Date(lens.requested_at) : null;
                lens.processing_at = lens.processing_at ? new Date(lens.processing_at) : null;
                lens.finished_at = lens.finished_at ? new Date(lens.finished_at) : null;
            });
            this.lenses = lenses;
        },

        async loadClusterings() {
            const clusterings = await callApi(`/job/${this.job.job_id}/clusterings`);
            clusterings.forEach(clustering => {
                clustering.requested_at = clustering.requested_at ? new Date(clustering.requested_at) : null;
                clustering.processing_at = clustering.processing_at ? new Date(clustering.processing_at) : null;
                clustering.finished_at = clustering.finished_at ? new Date(clustering.finished_at) : null;
            });
            this.clusterings = clusterings;
        },

        async createJob(inputs) {
            const data = await callApi('/job/create', inputs);
            return data.job_id;
        },

        async updateJob(jobData) {
            return callApi('/job/update', jobData);
        },

        async runLinkset(id, restart) {
            await this.submit();
            return callApi(`/job/${this.job.job_id}/run/linkset/${id}`, {restart});
        },

        async runLens(id, restart) {
            await this.submit();
            return callApi(`/job/${this.job.job_id}/run/lens/${id}`, {restart});
        },

        async runClustering(type, id) {
            return callApi(`/job/${this.job.job_id}/run_clustering/${type}/${id}`, {});
        },

        async killLinkset(id) {
            return callApi(`/job/${this.job.job_id}/kill/linkset/${id}`, {});
        },

        async killLens(id) {
            return callApi(`/job/${this.job.job_id}/kill/lens/${id}`, {});
        },

        async killClustering(type, id) {
            return callApi(`/job/${this.job.job_id}/kill_clustering/${type}/${id}`, {});
        },

        async deleteResult(type, id) {
            return callApi(`/job/${this.job.job_id}/${type}/${id}`, undefined, true);
        },

        async getEntityTypeSelectionSampleTotal(id) {
            return callApi(`/job/${this.job.job_id}/entity_type_selection_total/${id}`);
        },

        async getEntityTypeSelectionSample(id, invert = false, limit = undefined, offset = 0) {
            const params = [];
            if (invert) params.push(`invert=${invert}`);
            if (limit) params.push(`limit=${limit}`);
            if (offset) params.push(`offset=${offset}`);

            return callApi(`/job/${this.job.job_id}/entity_type_selection/${id}?${params.join('&')}`);
        },

        async getLinksTotals(type, id, min = undefined, max = undefined, clusterId = undefined) {
            const params = [];
            if (clusterId) params.push(`cluster_id=${clusterId}`);
            if (min) params.push(`min=${min}`);
            if (max) params.push(`max=${max}`);

            return callApi(`/job/${this.job.job_id}/links_totals/${type}/${id}?${params.join('&')}`);
        },

        async getLinks(type, id, accepted, rejected, notSure, notValidated, mixed,
                       min = undefined, max = undefined, clusterId = undefined,
                       limit = undefined, offset = 0) {
            const params = [];
            if (accepted) params.push('valid=accepted');
            if (rejected) params.push('valid=rejected');
            if (notSure) params.push('valid=not_sure');
            if (notValidated) params.push('valid=not_validated');
            if (mixed) params.push('valid=mixed');

            if (clusterId) params.push(`cluster_id=${clusterId}`);
            if (min && min > 0) params.push(`min=${min}`);
            if (max && max < 1) params.push(`max=${max}`);
            if (limit) params.push(`limit=${limit}`);
            if (offset) params.push(`offset=${offset}`);

            return callApi(`/job/${this.job.job_id}/links/${type}/${id}?${params.join('&')}`);
        },

        async getClusters(type, id, limit = undefined, offset = 0) {
            const params = [];
            if (limit) params.push(`limit=${limit}`);
            if (offset) params.push(`offset=${offset}`);

            return callApi(`/job/${this.job.job_id}/clusters/${type}/${id}?${params.join('&')}`);
        },

        async getClusterGraphs(type, id, clusterId, getCluster = undefined,
                               getClusterCompact = undefined, getReconciliation = undefined) {
            const params = [];
            if (getCluster !== undefined) params.push(`get_cluster=${getCluster}`);
            if (getClusterCompact !== undefined) params.push(`get_cluster_compact=${getClusterCompact}`);
            if (getReconciliation !== undefined) params.push(`get_reconciliation=${getReconciliation}`);

            return callApi(`/job/${this.job.job_id}/cluster/${type}/${id}/${clusterId}/graph?${params.join('&')}`);
        },

        async validateLink(type, id, valid, source, target) {
            return callApi(`/job/${this.job.job_id}/validate/${type}/${id}`, {valid, source, target});
        },

        async validateSelection(type, id, valid, clusterId, accepted, rejected, notSure, notValidated, mixed) {
            const body = {valid, validation: []};

            if (accepted) body.validation.push('accepted');
            if (rejected) body.validation.push('rejected');
            if (notSure) body.validation.push('not_sure');
            if (notValidated) body.validation.push('not_validated');
            if (mixed) body.validation.push('mixed');

            if (clusterId) body['cluster_id'] = clusterId;

            return callApi(`/job/${this.job.job_id}/validate/${type}/${id}`, body);
        },

        async loadDatasets(graphqlEndpoint) {
            if (this.datasets.hasOwnProperty(graphqlEndpoint))
                return;

            this.datasets[graphqlEndpoint] = await callApi(`/datasets?endpoint=${graphqlEndpoint}`);
        },

        async startDownload(datasetId, collectionId, graphqlEndpoint) {
            const params = [`dataset_id=${datasetId}`, `collection_id=${collectionId}`, `endpoint=${graphqlEndpoint}`];
            return callApi(`/download?${params.join('&')}`);
        },

        async loadDownloadsInProgress() {
            const downloads = await callApi('/downloads');
            this.downloaded = downloads.downloaded;
            this.downloading = downloads.downloading;
        },
    },
};

function copy(obj) {
    return JSON.parse(JSON.stringify(obj));
}

function findId(objs) {
    let latestId = -1;
    objs.forEach(obj => {
        if (obj.id > latestId) latestId = obj.id;
    });
    return latestId + 1;
}

async function callApi(path, body, isDelete = false) {
    try {
        let response;

        if (body) {
            response = await fetch(path, {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                method: 'POST',
                body: JSON.stringify(body)
            });
        }
        else if (isDelete) {
            response = await fetch(path, {method: 'DELETE'});
        }
        else {
            response = await fetch(path);
        }

        if (!response.ok && response.status !== 400)
            return null;

        return response.json();
    }
    catch (e) {
        return null;
    }
}