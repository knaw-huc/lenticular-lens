<template>
  <div class="main-card" v-bind:class="{'is-invalid': hasError}" ref="cardElem">
    <handle v-if="hasHandle && !visible" class="absolute-handle"/>

    <div class="bg-light py-2" v-bind:class="{'sticky-top': visible}">
      <div class="row flex-nowrap align-items-center justify-content-start">
        <div v-if="hasCollapse" class="col-auto">
          <fa-icon icon="chevron-down" size="2x" v-b-toggle="hasCollapse ? id : {}"></fa-icon>
        </div>

        <div class="col-auto small text-uppercase text-muted p-0">
          {{ resType ? resType + ' ' : '' }}#{{ resId }}
        </div>

        <div class="flex-shrink-1 mr-auto" v-bind:class="[isEditing ? 'col' : 'col-auto']">
          <input v-if="isEditing" type="text" class="form-control border-0 card-title-input" :value="value"
                 ref="editInput" required @blur="editing = false" @input="$emit('input', $event.target.value)"/>

          <div v-else-if="!label" class="row" @mouseenter="hovering = true" @mouseleave="hovering = false">
            <div class="h2 col" v-b-toggle="hasCollapse ? id : {}">{{ value }}</div>

            <button type="button" class="btn col-auto p-0" title="Click to Edit"
                    v-bind:class="{'invisible': !hovering}" @click="editing = true">
              <fa-icon icon="pencil-alt" size="lg"/>
            </button>
          </div>

          <div v-else class="h2" v-b-toggle="hasCollapse ? id : {}">{{ label }}</div>
        </div>

        <slot name="title-columns"></slot>
      </div>

      <div v-if="hasExtraRow" class="row flex-nowrap align-items-center justify-content-between mt-4">
        <slot name="columns"></slot>
      </div>
    </div>

    <b-collapse v-if="hasCollapse" :id="id" :ref="id" :accordion="type + '-accordion'" :visible="openCard"
                @show="$emit('show')" @hide="$emit('hide')"
                @hidden="scrollIntoView" @input="withInput($event)">
      <slot></slot>
    </b-collapse>

    <slot v-else></slot>
  </div>
</template>

<script>
    export default {
        name: 'Card',
        props: {
            id: String,
            type: String,
            resId: Number,
            resType: String,
            label: String,
            value: String,
            openCard: {
                type: Boolean,
                default: false,
            },
            hasError: {
                type: Boolean,
                default: false,
            },
            hasCollapse: {
                type: Boolean,
                default: true
            },
            hasExtraRow: {
                type: Boolean,
                default: false,
            },
            hasHandle: {
                type: Boolean,
                default: false,
            },
        },
        data() {
            return {
                editing: false,
                hovering: false,
                visible: false,
            };
        },
        computed: {
            isEditing() {
                return !this.label && (this.editing || this.value === '');
            }
        },
        methods: {
            withInput(evt) {
                this.visible = evt;
                evt ? this.$emit('show') : this.$emit('hide');
            },

            scrollIntoView() {
                this.$refs.cardElem.scrollIntoView({behavior: 'smooth'});
            },
        },
        updated() {
            if (this.editing)
                this.$refs.editInput.focus();
        },
    };
</script>
