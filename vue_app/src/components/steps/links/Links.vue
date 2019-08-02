<template>
  <card :id="'links_' + match.id" type="links" :label="match.label" :fillLabel="false"
        @show="getLinks" @hide="showData = false">
    <template v-slot:columns>
      <div class="col-auto">
        <button type="button" class="btn btn-info btn-sm" v-b-toggle="'matches_info_' + match.id">
          <octicon name="chevron-down" scale="1" v-b-toggle="'matches_info_' + match.id"></octicon>
          Show alignment
        </button>
      </div>

      <div class="col-auto mr-auto">
        <button type="button" class="btn btn-info btn-sm" v-b-toggle="'properties_' + match.id">
          <octicon name="chevron-down" scale="1" v-b-toggle="'properties_' + match.id"></octicon>
          Select properties
        </button>
      </div>
    </template>

    <template v-slot:header>
      <b-collapse :id="'matches_info_' + match.id" accordion="matches-info-accordion">
        <match-info :match="match"/>
      </b-collapse>

      <b-collapse :id="'properties_' + match.id" accordion="properties-accordion">
        <properties :properties="match.properties"/>
      </b-collapse>
    </template>

    <virtual-list
        v-if="showData && hasProperties"
        class="mt-4"
        :size="130"
        :remain="5"
        :item="item"
        :pagemode="true"
        :itemcount="links.length"
        :itemprops="getItemProps"/>
  </card>
</template>

<script>
    import VirtualList from 'vue-virtual-scroll-list';

    import Card from "../../structural/Card";
    import SubCard from "../../structural/SubCard";

    import MatchInfo from "../../helpers/MatchInfo";
    import Properties from "../../helpers/Properties";

    import MatchLink from "./MatchLink";

    export default {
        name: "Links",
        components: {
            VirtualList,
            Card,
            SubCard,
            MatchInfo,
            Properties,
            MatchLink,
        },
        data() {
            return {
                links: [],
                properties: Object,
                showData: false,
                item: MatchLink,
            }
        },
        props: {
            match: Object,
        },
        computed: {
            hasProperties() {
                return !this.match.properties.map(res => res[1] !== '').includes(false);
            },
        },
        methods: {
            async getLinks() {
                const targets = this.$root.getTargetsForMatch(this.match.id);

                this.links = await this.$root.getAlignment(this.match.id);
                this.properties = await this.$root.loadPropertiesForAlignment(this.match.id, targets);

                this.showData = true;
            },

            getItemProps(idx) {
                const link = this.links[idx];
                return {
                    props: {
                        source: link[0],
                        sourceValues: this.properties[link[0]] || [],
                        target: link[1],
                        targetValues: this.properties[link[1]] || [],
                        strength: link[2],
                        isFirst: (idx === 0),
                    },
                };
            },
        },
    }
</script>