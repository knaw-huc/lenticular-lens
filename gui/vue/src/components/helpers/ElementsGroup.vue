<template>
  <div v-if="hasGroup" class="position-relative shadow border p-3 mt-3"
       v-bind:class="[{'is-invalid': errors.length > 0}, ...styleClass]">
    <handle v-if="!isRoot"/>

    <div class="row align-items-center">
      <div class="col-auto">
        <fa-icon icon="chevron-down" size="lg" v-b-toggle="uid"></fa-icon>
      </div>

      <div v-if="Object.keys(options).length > 0 && elements.length > 0" class="col">
        <select-box v-model="elementsGroup.type">
          <option v-for="(value, key) in options" :value="key">{{ value }}</option>
        </select-box>
      </div>

      <div v-if="elements.length < 1" class="col font-italic">
        {{ emptyElementsText }}

        <div class="invalid-feedback" v-bind:class="{'is-invalid': errors.includes('elements')}">
          {{ validationFailedText }}
        </div>
      </div>

      <div class="col-auto ml-auto">
        <div class="row">
          <div v-if="!isRoot && (elements.length > 0 || controlledElements)" class="col-auto">
            <button-delete @click="remove" title="Delete this group" class="pt-1 pr-0"/>
          </div>

          <div v-if="!controlledElements || elements.length === 0" class="col-auto">
            <button-add @click="add" title="Add"/>
          </div>
        </div>
      </div>
    </div>

    <b-collapse visible :id="uid" :ref="uid" v-model="isOpen">
      <draggable v-model="elementsGroup[elementsGroupName]" :group="controlledElements ? uid : group"
                 handle=".handle" @change="onMove($event)">
        <elements-group
            v-for="(element, elementIndex) in elements"
            :key="elementIndex"
            :index="elementIndex"
            :uid="uid + '_' + elementIndex"
            :group="group"
            :elements-group="element"
            :elements-group-name="elementsGroupName"
            :should-have-elements="shouldHaveElements"
            :controlled-elements="controlledElements"
            :validate-method-name="validateMethodName"
            :empty-elements-text="emptyElementsText"
            :validation-failed-text="validationFailedText"
            :options="options"
            @add="addElement($event)"
            @remove="removeElement($event)"
            @promote="promoteElement($event)"
            @demote="demoteElement($event)"
            v-slot="slotProps"
            ref="elementGroupComponents">
          <slot v-bind="slotProps"/>
        </elements-group>
      </draggable>
    </b-collapse>
  </div>

  <div v-else class="position-relative" v-bind:class="styleClass">
    <handle/>

    <slot v-bind:index="index" v-bind:element="elementsGroup"
          v-bind:add="() => $emit('promote', index)" v-bind:remove="() => $emit('remove', index)"/>
  </div>
</template>

<script>
    import Draggable from 'vuedraggable';
    import ValidationMixin from "../../mixins/ValidationMixin";

    export default {
        name: "ElementsGroup",
        components: {
            Draggable,
        },
        mixins: [ValidationMixin],
        data() {
            return {
                isOpen: true,
            };
        },
        props: {
            uid: String,
            elementsGroup: Object,
            elementsGroupName: String,
            group: String,
            validateMethodName: String,
            emptyElementsText: String,
            validationFailedText: String,
            index: {
                type: Number,
                default: 0,
            },
            options: {
                type: Object,
                default: () => ({
                    'AND': 'All conditions must be met (AND)',
                    'OR': 'At least one of the conditions must be met (OR)'
                })
            },
            isRoot: {
                type: Boolean,
                default: false,
            },
            shouldHaveElements: {
                type: Boolean,
                default: false,
            },
            controlledElements: {
                type: Boolean,
                default: false,
            },
        },
        computed: {
            styleClass() {
                const styleClass = [];

                if (this.isRoot)
                    styleClass.push('mt-3');

                if (this.isRoot || this.$parent.$parent.$parent.styleClass.includes('bg-primary-light'))
                    styleClass.push('bg-info-light', 'border-info');
                else
                    styleClass.push('bg-primary-light', 'border-primary');

                return styleClass;
            },

            hasGroup() {
                return typeof this.elementsGroup === 'object' &&
                    this.elementsGroup.hasOwnProperty(this.elementsGroupName);
            },

            elements() {
                return this.elementsGroup[this.elementsGroupName];
            },
        },
        methods: {
            validateElementsGroup() {
                let elementsValid = true;
                let groupValid = true;
                let childrenValid = true;

                if (this.hasGroup && this.elements.length > 0)
                    groupValid = !this.$refs.elementGroupComponents
                        .map(elementGroupComponent => elementGroupComponent.validateElementsGroup())
                        .includes(false);
                else if (this.hasGroup && this.shouldHaveElements)
                    elementsValid = this.validateField('elements', this.elementsGroup.conditions.length > 0);
                else if (!this.hasGroup && this.validateMethodName && this.$children.length > 0) {
                    if (typeof this.$children[1][this.validateMethodName] === 'function')
                        childrenValid = this.$children[1][this.validateMethodName]();
                }

                elementsValid = this.validateField('elements', elementsValid);
                groupValid = this.validateField('group', groupValid);
                childrenValid = this.validateField('children', childrenValid);

                return elementsValid && groupValid && childrenValid;
            },

            onMove(event) {
                if (event.hasOwnProperty('removed') && !this.isRoot && this.elements.length === 1)
                    this.$emit('demote', this.index);
            },

            add() {
                this.$emit('add', this.elementsGroup);
                this.isOpen = true;
            },

            remove() {
                this.$emit('remove', {group: null, index: this.index});
            },

            addElement(elementsGroup) {
                this.$emit('add', elementsGroup);
            },

            removeElement(idx) {
                if (this.controlledElements) {
                    const {group, index} = idx;
                    this.$emit('remove', {group: group || this.elementsGroup, index});
                }
                else {
                    this.elementsGroup[this.elementsGroupName].splice(idx, 1);
                    if (!this.isRoot && this.elementsGroup[this.elementsGroupName].length === 1)
                        this.$emit('demote', this.index);
                }
            },

            promoteElement(index) {
                const element = this.elementsGroup[this.elementsGroupName][index];
                const elementCopy = JSON.parse(JSON.stringify(element));

                const elementGroup = {
                    type: Object.keys(this.options)[0],
                    [this.elementsGroupName]: [elementCopy],
                };

                this.$set(this.elementsGroup[this.elementsGroupName], index, elementGroup);
                this.$emit('add', this.elementsGroup[this.elementsGroupName][index]);
            },

            demoteElement(index) {
                const element = this.elementsGroup[this.elementsGroupName][index][this.elementsGroupName][0];
                const elementCopy = JSON.parse(JSON.stringify(element));

                this.$set(this.elementsGroup[this.elementsGroupName], index, elementCopy);
            },
        }
    };
</script>