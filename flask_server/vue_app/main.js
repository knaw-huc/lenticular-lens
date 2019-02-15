import Vue from 'vue'
import App from './config_form.vue'
import ResultsComponent from './components/Results'

import Octicon from 'vue-octicon/components/Octicon.vue'
import 'vue-octicon/icons'

import MatchingFieldValueComponent from "./components/MatchingFieldValue"

Vue.component('octicon', Octicon);

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
