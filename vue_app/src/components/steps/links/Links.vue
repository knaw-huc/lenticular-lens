<template>
  <card :id="'links_' + match.id" type="links" :label="match.label" :fillLabel="false"
        @show="getLinks" @hide="showData = false">
    <template v-slot:columns>
      <div class="col-auto mr-auto">
        <button type="button" class="btn btn-info btn-sm" v-b-toggle="'matches_info_' + match.id">
          <octicon name="chevron-down" scale="1" v-b-toggle="'matches_info_' + match.id"></octicon>
          Show alignment
        </button>
      </div>
    </template>

    <template v-slot:header>
      <b-collapse :id="'matches_info_' + match.id" accordion="matches-info-accordion">
        <match-info :match="match"/>
      </b-collapse>
    </template>

    <virtual-list :size="40" :remain="8" :item="item" :itemcount="links.length" :itemprops="getItemProps"/>
  </card>
</template>

<script>
    import VirtualList from 'vue-virtual-scroll-list';

    import Card from "../../structural/Card";
    import SubCard from "../../structural/SubCard";
    import MatchInfo from "../../helpers/MatchInfo";

    //import LinksTable from "./LinksTable";
    import MatchLink from "./MatchLink";

    export default {
        name: "Links",
        components: {
            VirtualList,
            Card,
            SubCard,
            MatchInfo,
            //LinksTable,
            MatchLink,
        },
        data() {
            return {
                links: [],
                showData: false,
                item: MatchLink,
            }
        },
        props: {
            match: Object,
        },
        methods: {
            async getLinks() {
                this.showData = true;

                const links = await this.$root.getAlignment(this.match.id);
                this.links = links;
            },

            getItemProps(idx) {
                return {
                    props: {
                        link: this.links[idx],
                    }
                };
            },
        },
    }
</script>

<style>
  .matching-links {
    height: 20em;
    overflow-y: auto;
  }
</style>