import './app.scss'

import Vue from 'vue'
import BootstrapVue from 'bootstrap-vue'
Vue.use(BootstrapVue);

import App from './config_form.vue'
import ResultsComponent from './components/Results'
import ClusterVisualization from './components/ClusterVisualization'
import EditLabel from './components/EditLabel'
Vue.component('edit-label-component', EditLabel);
import ButtonAdd from './components/misc/ButtonAdd'
Vue.component('button-add', ButtonAdd);
import ButtonDelete from './components/misc/ButtonDelete'
Vue.component('button-delete', ButtonDelete);
import ButtonInfo from './components/misc/ButtonInfo'
Vue.component('button-info', ButtonInfo);
import VSelect from './components/misc/VSelect'
Vue.component('v-select', VSelect);
import Property from './components/Property'
Vue.component('property-component', Property);

import Octicon from 'vue-octicon/components/Octicon.vue'
import 'vue-octicon/icons'

Vue.component('octicon', Octicon);

import md5 from 'md5'
Vue.prototype.$utilities = {
  md5: md5,
};

import VueFormWizard from 'vue-form-wizard'
import 'vue-form-wizard/dist/vue-form-wizard.min.css'
Vue.use(VueFormWizard);

Vue.filter('capitalize', function (value) {
  if (!value) return '';
  value = value.toString();
  return value.charAt(0).toUpperCase() + value.slice(1)
});

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
