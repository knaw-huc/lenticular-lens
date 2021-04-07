<template>
  <div v-if="isLogicBox" class="position-relative shadow border p-3 mt-3"
       v-bind:class="[{'is-invalid': errors.length > 0}, ...styleClass]">
    <handle v-if="!isRoot" class="absolute-handle"/>

    <div class="row align-items-center">
      <div class="col-auto">
        <fa-icon icon="chevron-down" size="lg" v-b-toggle="uid"></fa-icon>
      </div>

      <div v-if="Object.keys(options).length > 0 && logicBoxElements.length > 0" class="col">
        <select-box v-model="element.type">
          <template v-if="Object.keys(optionGroups).length > 0">
            <optgroup v-for="(optionKeys, label) in optionGroups" :label="label">
              <option v-for="optionKey in optionKeys" :value="optionKey">{{ options[optionKey] }}</option>
            </optgroup>
          </template>

          <option v-else v-for="(value, key) in options" :value="key">{{ value }}</option>
        </select-box>
      </div>

      <div v-if="logicBoxElements.length < 1" class="col font-italic">
        {{ emptyElementsText }}

        <div class="invalid-feedback" v-bind:class="{'is-invalid': errors.includes('elements')}">
          {{ validationFailedText }}
        </div>
      </div>

      <slot name="box-slot" v-bind:index="index" v-bind:element="element"/>

      <div class="col-auto ml-auto">
        <div class="row">
          <div v-if="!isRoot && (logicBoxElements.length > 0 || controlledElements)" class="col-auto">
            <button-delete @click="remove" title="Delete" class="pt-1 pr-0"/>
          </div>

          <div v-if="!controlledElements || logicBoxElements.length === 0" class="col-auto">
            <button-add @click="add" title="Add"/>
          </div>
        </div>
      </div>
    </div>

    <b-collapse visible :id="uid" :ref="uid" v-model="isOpen">
      <sub-card v-if="optionDescriptions.hasOwnProperty(element.type) && logicBoxElements.length > 0"
                class="max-overflow small" label="Description" size="xs">
        <p class="mt-2">{{ optionDescriptions[element.type] }}</p>
      </sub-card>

      <draggable v-model="element[elementsName]" :group="controlledElements ? uid : group"
                 handle=".handle" @change="onMove($event)">
        <logic-box
            v-for="(elem, elemIdx) in logicBoxElements"
            :key="elemIdx"
            :uid="uid + '_' + elemIdx"
            :element="elem"
            :elements-name="elementsName"
            :group="group"
            :validate-method-name="validateMethodName"
            :empty-elements-text="emptyElementsText"
            :validation-failed-text="validationFailedText"
            :parent-type="element.type"
            :index="elemIdx"
            :options="options"
            :option-groups="optionGroups"
            :option-descriptions="optionDescriptions"
            :group-include="groupInclude"
            :should-have-elements="shouldHaveElements"
            :controlled-elements="controlledElements"
            @add="addElement($event)"
            @remove="removeElement($event)"
            @promote="promoteElement($event)"
            @demote="demoteElement($event)"
            ref="logicBoxComponents">
          <template v-slot:default="slotProps">
            <slot name="default" v-bind="slotProps"/>
          </template>

          <template v-slot:box-slot="boxSlotProps">
            <slot name="box-slot" v-bind="boxSlotProps"/>
          </template>
        </logic-box>
      </draggable>
    </b-collapse>
  </div>

  <div v-else class="position-relative" v-bind:class="styleClass">
    <handle class="absolute-handle"/>

    <slot v-bind:type="parentType" v-bind:index="index" v-bind:element="element"
          v-bind:add="() => $emit('promote', index)" v-bind:remove="() => $emit('remove', index)"/>
  </div>
</template>

<script>
    import Draggable from 'vuedraggable';
    import ValidationMixin from "../../mixins/ValidationMixin";

    export default {
        name: "LogicBox",
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
            element: Object,
            elementsName: String,
            group: String,
            validateMethodName: String,
            emptyElementsText: String,
            validationFailedText: String,
            parentType: String,
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
            optionGroups: {
                type: Object,
                default: () => ({})
            },
            optionDescriptions: {
                type: Object,
                default: () => ({})
            },
            groupInclude: {
                type: Object,
                default: () => ({})
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
                    styleClass.push('bg-secondary-light', 'border-secondary');
                else
                    styleClass.push('bg-primary-light', 'border-primary');

                return styleClass;
            },

            isLogicBox() {
                return typeof this.element === 'object' &&
                    this.element.hasOwnProperty(this.elementsName);
            },

            logicBoxElements() {
                return this.element[this.elementsName];
            },
        },
        methods: {
            validateLogicBox() {
                let logicBoxValid = true;
                let elementsValid = true;
                let childrenValid = true;

                if (this.isLogicBox && this.logicBoxElements.length > 0)
                    logicBoxValid = !this.$refs.logicBoxComponents
                        .map(logicBoxComponent => logicBoxComponent.validateLogicBox())
                        .includes(false);
                else if (this.isLogicBox && this.shouldHaveElements)
                    elementsValid = this.validateField('elements', this.element.conditions.length > 0);
                else if (!this.isLogicBox && this.validateMethodName && this.$children.length > 0) {
                    if (typeof this.$children[1][this.validateMethodName] === 'function')
                        childrenValid = this.$children[1][this.validateMethodName]();
                }

                logicBoxValid = this.validateField('logicBox', logicBoxValid);
                elementsValid = this.validateField('elements', elementsValid);
                childrenValid = this.validateField('children', childrenValid);

                return logicBoxValid && elementsValid && childrenValid;
            },

            onMove(event) {
                if (event.hasOwnProperty('removed') && !this.isRoot && this.logicBoxElements.length === 1)
                    this.$emit('demote', this.index);
            },

            add() {
                this.$emit('add', this.element);
                this.isOpen = true;
            },

            remove() {
                this.$emit('remove', {group: null, index: this.index});
            },

            addElement(elem) {
                this.$emit('add', elem);
            },

            removeElement(idx) {
                if (this.controlledElements) {
                    const {group, index} = idx;
                    this.$emit('remove', {group: group || this.element, index});
                }
                else {
                    this.element[this.elementsName].splice(idx, 1);
                    if (!this.isRoot && this.element[this.elementsName].length === 1)
                        this.$emit('demote', this.index);
                }
            },

            promoteElement(index) {
                const element = this.element[this.elementsName][index];
                const elementCopy = JSON.parse(JSON.stringify(element));

                const logicBox = {
                    ...this.groupInclude,
                    type: Object.keys(this.options)[0],
                    [this.elementsName]: [elementCopy],
                };

                this.$set(this.element[this.elementsName], index, logicBox);
                this.$emit('add', this.element[this.elementsName][index]);
            },

            demoteElement(index) {
                const element = this.element[this.elementsName][index][this.elementsName][0];
                const elementCopy = JSON.parse(JSON.stringify(element));

                this.$set(this.element[this.elementsName], index, elementCopy);
            },
        }
    };
</script>