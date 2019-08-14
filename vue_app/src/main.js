import Vue from 'vue';

import BootstrapVue from 'bootstrap-vue';
import VueFormWizard from 'vue-form-wizard';

Vue.use(BootstrapVue);
Vue.use(VueFormWizard);

import EditLabel from './components/misc/EditLabel';
import ButtonAdd from './components/misc/ButtonAdd';
import ButtonDelete from './components/misc/ButtonDelete';
import ButtonInfo from './components/misc/ButtonInfo';
import VSelect from './components/misc/VSelect';
import Loading from './components/misc/Loading';
import Property from './components/helpers/Property';
import Octicon from 'vue-octicon/components/Octicon.vue';
import 'vue-octicon/icons';

Vue.component('edit-label', EditLabel);
Vue.component('button-add', ButtonAdd);
Vue.component('button-delete', ButtonDelete);
Vue.component('button-info', ButtonInfo);
Vue.component('v-select', VSelect);
Vue.component('loading', Loading);
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
import JobMixin from './mixins/JobMixin';

import './assets/app.scss';
import 'vue-form-wizard/dist/vue-form-wizard.min.css';

new Vue({
    mixins: [JobMixin],
    render: h => h(App),
}).$mount('#app');
