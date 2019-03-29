import './app.scss'

import Vue from 'vue'
import BootstrapVue from 'bootstrap-vue'
Vue.use(BootstrapVue);

import App from './config_form.vue'
import ResultsComponent from './components/Results'
import ClusterVisualization from './components/ClusterVisualization'
import EditLabel from './components/EditLabel'
Vue.component('edit-label-component', EditLabel);

import Octicon from 'vue-octicon/components/Octicon.vue'
import 'vue-octicon/icons'

import MatchingFieldValueComponent from "./components/MatchingFieldValue"

Vue.component('octicon', Octicon);

import md5 from 'md5'
Vue.prototype.$utilities = {
  md5: md5,
};

import VueFormWizard from 'vue-form-wizard'
import 'vue-form-wizard/dist/vue-form-wizard.min.css'
Vue.use(VueFormWizard);

Vue.component('matching-field-value-component', MatchingFieldValueComponent);

new Vue({
  computed: {
    ViewComponent() {
      if (this.currentRoute.startsWith('/job')) {
        let cluster_id_res = /(?<=\/job\/.+\/cluster\/)(.+)\/(.+)/.exec(this.currentRoute);
        if (cluster_id_res) {
          this.child_component_data = JSON.stringify({
            props: {
              clustering_id: cluster_id_res[1],
              cluster_id: cluster_id_res[2],
            },
          });
          return ClusterVisualization;
        }

        return ResultsComponent;
      }

      return App;
    },
  },
  data: {
    child_component_data: null,
    currentRoute: window.location.pathname
  },
  render(h) {
    return h(this.ViewComponent, JSON.parse(this.child_component_data))
  }
}).$mount('#app');
