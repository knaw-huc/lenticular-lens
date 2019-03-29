<template>
<div class="border p-4 mt-4 bg-light">
    <div class="row justify-content-between">
        <div class="col-auto">
            <octicon name="chevron-down" scale="3" v-b-toggle="'match_' + match.id"></octicon>
        </div>

        <div class="col" v-b-toggle="'match_' + match.id">
            <div class="row">
                <div class="h2 col">{{ match_label }}</div>
            </div>
            <div class="row">
                <div class="col form-group form-check ml-3 mb-1">
                    <input type="checkbox" class="form-check-input" :id="'match_' + match.id + '_is_association'" v-model.boolean="match.is_association">
                    <label class="form-check-label" :for="'match_' + match.id + '_is_association'">Association</label>
                </div>
            </div>
        </div>

        <div class="form-group col-1">
            <button v-on:click="$emit('remove')" type="button" class="ml-3 btn btn-danger"><octicon name="trashcan"></octicon></button>
        </div>
    </div>

    <b-collapse :id="'match_' + match.id" :ref="'match_' + match.id" accordion="matches-accordion" @shown="scrollTo('match_' + match.id)">
        <div class="form-group col-3">
            <label :for="'match_' + match.id + '_label'">Mapping label</label>
            <input v-model="label_input" class="form-control" id="'match_' + match.id + '_label'" :placeholder="match_label">
        </div>
    
        <div class="row">
            <div class="col">
                <h3>Sources</h3>

                <match-resource-component
                        v-for="(match_resource, index) in match.sources"
                        :match_resource_id="'source_' + index"
                        :match="match"
                        :match_resource="match_resource"
                        :datasets="datasets"
                        :resources="resources"
                        @remove="match.sources.splice(index, 1)"
                ></match-resource-component>

                <div class="form-group">
                    <button type="button" class="btn btn-primary w-25 form-control" @click="addMatchResource(match.sources, $event)">+ Add source</button>
                </div>
            </div>
        </div>


        <div class="row">
            <div class="col">
                <h3>Targets</h3>
                <match-resource-component
                        v-for="(match_resource, index) in match.targets"
                        :match_resource_id="'target_' + index"
                        :match="match"
                        :match_resource="match_resource"
                        :datasets="datasets"
                        :resources="resources"
                        @remove="match.targets.splice(index, 1)"
                ></match-resource-component>

                <div class="form-group">
                    <button type="button" class="btn btn-primary w-25 form-control" @click="addMatchResource(match.targets, $event)">+ Add target</button>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col">
                <h3>Conditions</h3>

                <div class="form-group">
                    <select class="form-control" v-model="match.conditions.type">
                        <option value="AND">All conditions must be met (AND)</option>
                        <option value="OR">At least one of the conditions must be met (OR)</option>
                    </select>
                </div>

                <match-condition
                        v-for="(condition, index) in match.conditions.items"
                        :condition="condition"
                        :matching_field_labels="matching_field_labels"
                        @remove="match.conditions.items.splice(index, 1)"
                ></match-condition>

                <div class="form-group">
                    <button type="button" class="btn btn-primary w-25 form-control" @click="addCondition($event)">+ Add condition</button>
                </div>
            </div>
        </div>
    </b-collapse>
</div>
</template>

<script>
    import MatchResource from './MatchResource'
    import MatchCondition from './MatchCondition'

    export default {
        components: {
            'match-resource-component': MatchResource,
            'match-condition': MatchCondition,
        },
        computed: {
            match_label() {
                if (typeof this.label_input !== 'undefined' && this.label_input !== '') {
                    this.$emit('update:label', this.label_input);
                    return this.label_input;
                }

                return 'Mapping ' + this.match.id;
            },
            matching_field_labels() {
                let labels = [];

                this.match.sources[0].matching_fields.forEach(matching_field => {
                    labels.push(matching_field.label);
                });

                this.match.matching_field_labels = labels;

                return labels;
            },
        },
        data() {
            return {
                label_input: '',
                conditions_count: 0,
            }
        },
        props: ['match', 'matches', 'datasets', 'resources'],
        methods: {
            addCondition(event) {
                if (event) {
                    event.target.blur();
                }

                this.conditions_count++;

                let condition = {
                    'id': this.conditions_count,
                    'matching_field': '',
                    'method': '',
                };

                this.match.conditions.items.push(condition);
            },
            addMatchResource(match_resources, event) {
                if (event) {
                    event.target.blur();
                }

                let match_resource = {
                    'matching_fields': [],
                };

                match_resources.push(match_resource);
            },
            scrollTo(ref) {
                this.$refs[ref].$el.parentNode.scrollIntoView({'behavior':'smooth', 'block':'start'});
            }
        },
        mounted() {
            if (this.match.sources.length < 1) {
                this.addMatchResource(this.match.sources);
            }

            this.conditions_count = this.match.conditions.items.length;
            if (this.conditions_count < 1) {
                this.addCondition();
            }
        },
        watch: {
            label_input() {
                this.$set(this.match, 'label', this.match_label);
                this.matches.reverse();
                this.matches.reverse();
            }
        }
    }
</script>
