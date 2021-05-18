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

        updateView(id, type, entityTypeSelections) {
            let view = this.getViewByIdAndType(id, type);

            if (view) {
                const propertiesToRemove = JSON.parse(JSON.stringify(view.properties));
                const filtersToRemove = JSON.parse(JSON.stringify(view.filters));

                entityTypeSelections.forEach(etsId => {
                    const ets = this.getEntityTypeSelectionById(etsId);

                    const propsIdx = propertiesToRemove.findIndex(prop =>
                        prop.timbuctoo_graphql === ets.dataset.timbuctoo_graphql &&
                        prop.dataset_id === ets.dataset.dataset_id &&
                        prop.collection_id === ets.dataset.collection_id
                    );

                    if (propsIdx > -1)
                        propertiesToRemove.splice(propsIdx, 1);

                    const filterIdx = filtersToRemove.findIndex(filter =>
                        filter.timbuctoo_graphql === ets.dataset.timbuctoo_graphql &&
                        filter.dataset_id === ets.dataset.dataset_id &&
                        filter.collection_id === ets.dataset.collection_id
                    );

                    if (filterIdx > -1)
                        filtersToRemove.splice(filterIdx, 1);
                });

                propertiesToRemove.forEach(toRemove => {
                    const propsIdx = view.properties.findIndex(prop =>
                        prop.timbuctoo_graphql === toRemove.timbuctoo_graphql &&
                        prop.dataset_id === toRemove.dataset_id &&
                        prop.collection_id === toRemove.collection_id
                    );

                    if (propsIdx > -1)
                        view.properties.splice(propsIdx, 1);
                });

                filtersToRemove.forEach(toRemove => {
                    const filterIdx = view.filters.findIndex(prop =>
                        prop.timbuctoo_graphql === toRemove.timbuctoo_graphql &&
                        prop.dataset_id === toRemove.dataset_id &&
                        prop.collection_id === toRemove.collection_id
                    );

                    if (filterIdx > -1)
                        view.filters.splice(filterIdx, 1);
                });
            }
            else {
                this.addView(id, type);
                view = this.getViewByIdAndType(id, type);
            }

            entityTypeSelections.forEach(etsId => {
                const ets = this.$root.getEntityTypeSelectionById(etsId);

                const propsIdx = view.properties.findIndex(prop =>
                    prop.timbuctoo_graphql === ets.dataset.timbuctoo_graphql &&
                    prop.dataset_id === ets.dataset.dataset_id &&
                    prop.collection_id === ets.dataset.collection_id
                );

                if (propsIdx < 0)
                    view.properties.push({
                        timbuctoo_graphql: ets.dataset.timbuctoo_graphql,
                        dataset_id: ets.dataset.dataset_id,
                        collection_id: ets.dataset.collection_id,
                        properties: [['']]
                    });

                const filterIdx = view.filters.findIndex(filter =>
                    filter.timbuctoo_graphql === ets.dataset.timbuctoo_graphql &&
                    filter.dataset_id === ets.dataset.dataset_id &&
                    filter.collection_id === ets.dataset.collection_id
                );

                if (filterIdx < 0)
                    view.filters.push({
                        timbuctoo_graphql: ets.dataset.timbuctoo_graphql,
                        dataset_id: ets.dataset.dataset_id,
                        collection_id: ets.dataset.collection_id,
                        filter: {
                            type: 'AND',
                            conditions: [],
                        },
                    });
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

        getExportCsvLink(type, id, params) {
            return `/job/${this.job.job_id}/csv/${type}/${id}?${params.join('&')}`;
        },

        getExportRdfLink(type, id, params) {
            return `/job/${this.job.job_id}/rdf/${type}/${id}?${params.join('&')}`;
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

                this.entityTypeSelections = entityTypeSelections;
            }

            if (this.job.linkset_specs)
                this.linksetSpecs = copy(this.job.linkset_specs);

            if (this.job.lens_specs)
                this.lensSpecs = copy(this.job.lens_specs);

            if (this.job.views)
                this.views = copy(this.job.views);

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

        async getLinksTotals(type, id, props) {
            props = {applyFilters: true, uris: [], clusterIds: [], min: undefined, max: undefined, ...props};

            const params = [`apply_filters=${props.applyFilters}`];

            if (props.uris && props.uris.length > 0)
                props.uris.forEach(uri => params.push(`uri=${encodeURIComponent(uri)}`));

            if (props.clusterIds && props.clusterIds.length > 0)
                props.clusterIds.forEach(clusterId => params.push(`cluster_id=${encodeURIComponent(clusterId)}`));

            if (props.min && props.min > 0) params.push(`min=${props.min}`);
            if (props.max && props.max < 1) params.push(`max=${props.max}`);

            return callApi(`/job/${this.job.job_id}/links_totals/${type}/${id}?${params.join('&')}`);
        },

        async getLinks(type, id, props, limit = undefined, offset = 0) {
            props = {
                withProperties: 'multiple', applyFilters: true,
                accepted: false, rejected: false, notSure: false, notValidated: false, mixed: false,
                uris: [], clusterIds: [], min: undefined, max: undefined, sort: 'desc', ...props
            };

            const params = [
                `with_properties=${props.withProperties}`,
                `apply_filters=${props.applyFilters}`
            ];

            if (props.accepted) params.push('valid=accepted');
            if (props.rejected) params.push('valid=rejected');
            if (props.notSure) params.push('valid=not_sure');
            if (props.notValidated) params.push('valid=not_validated');
            if (props.mixed) params.push('valid=mixed');

            if (props.uris && props.uris.length > 0)
                props.uris.forEach(uri => params.push(`uri=${encodeURIComponent(uri)}`));
            if (props.clusterIds && props.clusterIds.length > 0)
                props.clusterIds.forEach(clusterId => params.push(`cluster_id=${encodeURIComponent(clusterId)}`));

            if (props.min && props.min > 0) params.push(`min=${props.min}`);
            if (props.max && props.max < 1) params.push(`max=${props.max}`);
            if (props.sort) params.push(`sort=${props.sort}`);

            if (limit) params.push(`limit=${limit}`);
            if (offset) params.push(`offset=${offset}`);

            return callApi(`/job/${this.job.job_id}/links/${type}/${id}?${params.join('&')}`);
        },

        async getClustersTotals(type, id, props) {
            props = {
                applyFilters: true, uris: [], clusterIds: [], min: undefined, max: undefined,
                minSize: undefined, maxSize: undefined, minCount: undefined, maxCount: undefined, ...props
            };

            const params = [`apply_filters=${props.applyFilters}`];

            if (props.uris && props.uris.length > 0)
                props.uris.forEach(uri => params.push(`uri=${encodeURIComponent(uri)}`));

            if (props.clusterIds && props.clusterIds.length > 0)
                props.clusterIds.forEach(clusterId => params.push(`cluster_id=${encodeURIComponent(clusterId)}`));

            if (props.min && props.min > 0) params.push(`min=${props.min}`);
            if (props.max && props.max < 1) params.push(`max=${props.max}`);

            if (props.minSize) params.push(`min_size=${props.minSize}`);
            if (props.maxSize) params.push(`max_size=${props.maxSize}`);

            if (props.minCount) params.push(`min_count=${props.minCount}`);
            if (props.maxCount) params.push(`max_count=${props.maxCount}`);

            return callApi(`/job/${this.job.job_id}/clusters_totals/${type}/${id}?${params.join('&')}`);
        },

        async getClusters(type, id, props, limit = undefined, offset = 0) {
            props = {
                withProperties: 'multiple', applyFilters: true,
                uris: [], clusterIds: [], min: undefined, max: undefined, minSize: undefined, maxSize: undefined,
                minCount: undefined, maxCount: undefined, sort: undefined, ...props
            };

            const params = [
                `with_properties=${props.withProperties}`,
                `apply_filters=${props.applyFilters}`
            ];

            if (props.uris && props.uris.length > 0)
                props.uris.forEach(uri => params.push(`uri=${encodeURIComponent(uri)}`));
            if (props.clusterIds && props.clusterIds.length > 0)
                props.clusterIds.forEach(clusterId => params.push(`cluster_id=${encodeURIComponent(clusterId)}`));

            if (props.min && props.min > 0) params.push(`min=${props.min}`);
            if (props.max && props.max < 1) params.push(`max=${props.max}`);

            if (props.minSize) params.push(`min_size=${props.minSize}`);
            if (props.maxSize) params.push(`max_size=${props.maxSize}`);

            if (props.minCount) params.push(`min_count=${props.minCount}`);
            if (props.maxCount) params.push(`max_count=${props.maxCount}`);

            if (props.sort) params.push(`sort=${props.sort}`);

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

        async validateLink(type, id, validation, source, target) {
            return callApi(`/job/${this.job.job_id}/validate/${type}/${id}`,
                {validation, apply_filters: false, source, target});
        },

        async validateSelection(type, id, validation, props) {
            props = {
                accepted: false, rejected: false, notSure: false, notValidated: false, mixed: false,
                uris: [], clusterIds: [], min: undefined, max: undefined, ...props
            };

            const body = {validation, apply_filters: true, valid: [], uri: [], cluster_id: []};

            if (props.accepted) body.valid.push('accepted');
            if (props.rejected) body.valid.push('rejected');
            if (props.notSure) body.valid.push('not_sure');
            if (props.notValidated) body.valid.push('not_validated');
            if (props.mixed) body.valid.push('mixed');

            if (props.uris && props.uris.length > 0)
                props.uris.forEach(uri => body.uri.push(uri));
            if (props.clusterIds && props.clusterIds.length > 0)
                props.clusterIds.forEach(clusterId => body.cluster_id.push(clusterId));

            if (props.min && props.min > 0) body.min = props.min;
            if (props.max && props.max < 1) body.max = props.max;

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