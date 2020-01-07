export default {
    data() {
        return {
            job: null,
            alignments: [],
            clusterings: [],
            resources: [],
            matches: [],
            datasets: {},
            downloaded: [],
            downloading: [],
            associationFiles: [],
        };
    },
    methods: {
        getDatasets(graphqlEndpoint, hsid) {
            const id = graphqlEndpoint && hsid ? graphqlEndpoint + ':' + hsid : graphqlEndpoint;
            return this.datasets.hasOwnProperty(id) ? this.datasets[id] : {};
        },

        addResource() {
            this.resources.unshift({
                id: findId(this.resources),
                description: '',
                dataset: {
                    timbuctoo_graphql: 'https://repository.goldenagents.org/v5/graphql',
                    timbuctoo_hsid: null,
                    dataset_id: '',
                    collection_id: '',
                    published: true,
                },
                filter: {
                    type: 'AND',
                    conditions: [],
                },
                properties: [],
                limit: -1,
                related: [],
                related_array: false,
            });
        },

        addMatch() {
            this.matches.unshift({
                id: findId(this.matches),
                description: '',
                is_association: false,
                label: 'Alignment ' + (this.matches.length + 1),
                sources: [],
                targets: [],
                properties: [],
                match_against: null,
                methods: {
                    type: 'AND',
                    conditions: [],
                },
            });
        },

        duplicateResource(resource) {
            const index = this.resources.findIndex(res => res.id === resource.id);
            const duplicate = copy(resource);
            this.resources.splice(index, 0, {
                ...duplicate,
                id: findId(this.resources),
                label: undefined,
            });
        },

        duplicateMatch(match) {
            const index = this.matches.findIndex(m => m.id === match.id);
            const duplicate = copy(match);
            this.matches.splice(index, 0, {
                ...duplicate,
                id: findId(this.matches),
                label: 'Alignment ' + (this.matches.length + 1),
            });
        },

        getResourceById(resourceId) {
            return this.resources.find(res => res.id === parseInt(resourceId));
        },

        getMatchById(matchId) {
            return this.matches.find(match => match.id === parseInt(matchId));
        },

        getCleanPropertyName(property, propInfo) {
            if (propInfo.isList)
                property = property.replace(/List$/, '');
            if (propInfo.isInverse)
                property = property.replace(/^_inverse_/, '');

            return property;
        },

        exportCsvLink(alignment, accepted, declined, notValidated) {
            const params = [];
            if (accepted) params.push('accepted=true');
            if (declined) params.push('declined=true');
            if (notValidated) params.push('not_validated=true');

            return `/job/${this.job.job_id}/export/${alignment}/csv?${params.join('&')}`;
        },

        getRecursiveConditions(conditionsGroup) {
            let conditions;
            if (Array.isArray(conditionsGroup))
                conditions = conditionsGroup;
            else if (Array.isArray(conditionsGroup.conditions))
                conditions = conditionsGroup.conditions;

            if (conditions)
                return conditions.reduce((acc, condition) => acc.concat(this.getRecursiveConditions(condition)), []);

            return [conditionsGroup];
        },

        async submit() {
            await this.updateJob({
                job_id: this.job.job_id,
                job_title: this.job.job_title,
                job_description: this.job.job_description,
                job_link: this.job.job_link,
                resources: this.resources,
                mappings: this.matches,
            });
        },

        async loadJob(jobId) {
            const job = await callApi('/job/' + jobId);
            if (!job)
                return;

            job.created_at = job.created_at ? new Date(job.created_at) : null;
            job.updated_at = job.updated_at ? new Date(job.updated_at) : null;
            this.job = job;

            if (this.job.resources) {
                const resources = copy(this.job.resources);

                const graphQlEndpoints = resources
                    .map(res => ({endpoint: res.dataset.timbuctoo_graphql, hsid: res.dataset.timbuctoo_hsid}))
                    .sort((dataA, dataB) => {
                        if (dataA.hsid && !dataB.hsid) return -1;
                        if (dataB.hsid && !dataA.hsid) return 1;
                        return 0;
                    })
                    .filter((data, idx, res) => res.findIndex(data2 => data2.endpoint === data.endpoint) === idx);
                await Promise.all(graphQlEndpoints.map(data => this.loadDatasets(data.endpoint, data.hsid)));

                this.resources = resources;
            }

            if (this.job.mappings)
                this.matches = copy(this.job.mappings);

            await Promise.all([this.loadAlignments(), this.loadClusterings()]);
        },

        async loadAlignments() {
            const alignments = await callApi(`/job/${this.job.job_id}/alignments`);
            alignments.forEach(alignment => {
                alignment.requested_at = alignment.requested_at ? new Date(alignment.requested_at) : null;
                alignment.processing_at = alignment.processing_at ? new Date(alignment.processing_at) : null;
                alignment.finished_at = alignment.finished_at ? new Date(alignment.finished_at) : null;
            });
            this.alignments = alignments;
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

        async startDownload(datasetId, collectionId, graphqlEndpoint, hsid) {
            const params = [`dataset_id=${datasetId}`, `collection_id=${collectionId}`, `endpoint=${graphqlEndpoint}`];
            if (hsid) params.push(`hsid=${hsid}`);

            return callApi(`/download?${params.join('&')}`);
        },

        async getResourceSample(resourceLabel, total = false, limit = undefined, offset = 0) {
            const params = [];
            if (total) params.push(`total=true`);
            if (!total && limit) params.push(`limit=${limit}`);
            if (!total && offset) params.push(`offset=${offset}`);

            return callApi(`/job/${this.job.job_id}/resource/${resourceLabel}?${params.join('&')}`);
        },

        async createJob(inputs) {
            const data = await callApi('/job/create/', inputs);
            return data.job_id;
        },

        async updateJob(jobData) {
            return callApi('/job/update/', jobData);
        },

        async runAlignment(alignment, restart) {
            await this.submit();
            return callApi(`/job/${this.job.job_id}/run_alignment/${alignment}`, {restart});
        },

        async killAlignment(alignment) {
            return callApi(`/job/${this.job.job_id}/kill_alignment/${alignment}`, {});
        },

        async killClustering(alignment) {
            return callApi(`/job/${this.job.job_id}/kill_clustering/${alignment}`, {});
        },

        async getAlignment(alignment, clusterId = undefined, limit = undefined, offset = 0) {
            const params = [];
            if (clusterId) params.push(`cluster_id=${clusterId}`);
            if (limit) params.push(`limit=${limit}`);
            if (offset) params.push(`offset=${offset}`);

            return callApi(`/job/${this.job.job_id}/alignment/${alignment}?${params.join('&')}`);
        },

        async getClusters(alignment, association, limit = undefined, offset = 0) {
            const params = [];
            if (association) params.push(`association=${association}`);
            if (limit) params.push(`limit=${limit}`);
            if (offset) params.push(`offset=${offset}`);

            return callApi(`/job/${this.job.job_id}/clusters/${alignment}?${params.join('&')}`);
        },

        async runClustering(alignment, association_file) {
            return callApi(`/job/${this.job.job_id}/run_clustering/${alignment}`, {association_file});
        },

        async getClusterGraphs(alignment, clusterId,
                               getCluster = undefined, getClusterCompact = undefined, getReconciliation = undefined) {
            const params = [];
            if (getCluster !== undefined) params.push(`get_cluster=${getCluster}`);
            if (getClusterCompact !== undefined) params.push(`get_cluster_compact=${getClusterCompact}`);
            if (getReconciliation !== undefined) params.push(`get_reconciliation=${getReconciliation}`);

            return callApi(`/job/${this.job.job_id}/cluster/${alignment}/${clusterId}/graph?${params.join('&')}`);
        },

        async validateLink(alignment, source, target, valid) {
            return callApi(`/job/${this.job.job_id}/validate/${alignment}`, {source, target, valid});
        },

        async loadDatasets(graphqlEndpoint, hsid) {
            const id = graphqlEndpoint && hsid ? graphqlEndpoint + ':' + hsid : graphqlEndpoint;
            if (!id || this.datasets.hasOwnProperty(id))
                return;

            const params = [`endpoint=${graphqlEndpoint}`];
            if (hsid) params.push(`hsid=${hsid}`);

            this.datasets[id] = await callApi(`/datasets?${params.join('&')}`);

            if (hsid) {
                const datasetsPublished = {};

                Object.keys(this.datasets[id]).forEach(datasetName => {
                    const dataset = this.datasets[id][datasetName];
                    if (dataset.published)
                        datasetsPublished[datasetName] = dataset;
                });

                this.datasets[graphqlEndpoint] = datasetsPublished;
            }
        },

        async loadDownloadsInProgress() {
            const downloads = await callApi('/downloads');
            this.downloaded = downloads.downloaded;
            this.downloading = downloads.downloading;
        },

        async loadAssociationFiles() {
            this.associationFiles = await callApi('/association_files');
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

async function callApi(path, body) {
    try {
        let response = null;

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
        else {
            response = await fetch(path);
        }

        if (!response.ok)
            return null;

        return response.json();
    }
    catch (e) {
        return null;
    }
}