import Vue from 'vue';

import BootstrapVue from 'bootstrap-vue';
import VueFormWizard from 'vue-form-wizard';

Vue.use(BootstrapVue);
Vue.use(VueFormWizard);

import EditLabel from './components/EditLabel';
import ButtonAdd from './components/misc/ButtonAdd';
import ButtonDelete from './components/misc/ButtonDelete';
import ButtonInfo from './components/misc/ButtonInfo';
import VSelect from './components/misc/VSelect';
import Property from './components/Property';
import Octicon from 'vue-octicon/components/Octicon.vue';
import 'vue-octicon/icons';

Vue.component('edit-label', EditLabel);
Vue.component('button-add', ButtonAdd);
Vue.component('button-delete', ButtonDelete);
Vue.component('button-info', ButtonInfo);
Vue.component('v-select', VSelect);
Vue.component('property', Property);
Vue.component('octicon', Octicon);

import md5 from 'md5';

Vue.prototype.$utilities = {
    md5: md5,

    getOrCreate(setter, subject, key, default_value) {
        if (typeof subject[key] === 'undefined')
            setter(subject, key, default_value);

        return subject[key];
    },
};

Vue.filter('capitalize', function (value) {
    if (!value) return '';
    value = value.toString();
    return value.charAt(0).toUpperCase() + value.slice(1);
});

import App from './App.vue';
import ResultsComponent from './components/Results';
import ClusterVisualization from './components/ClusterVisualization';
import JobMixin from './mixins/JobMixin';

import './assets/app.scss';
import 'vue-form-wizard/dist/vue-form-wizard.min.css';

new Vue({
    mixins: [JobMixin],
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
        currentRoute: window.location.pathname,
    },
    render(h) {
        return h(this.ViewComponent, JSON.parse(this.child_component_data));
    }
}).$mount('#app');
