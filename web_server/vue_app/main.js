import './app.scss'

import Vue from 'vue'
import BootstrapVue from 'bootstrap-vue'
Vue.use(BootstrapVue);

import App from './config_form.vue'
import ResultsComponent from './components/Results'

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
      return this.currentRoute.startsWith('/job')
          ? ResultsComponent
          : App
    },
  },
  data: {
    currentRoute: window.location.pathname
  },
  render(h) {
    return h(this.ViewComponent)
  }
}).$mount('#app');
