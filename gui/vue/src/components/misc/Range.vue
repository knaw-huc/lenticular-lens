<template>
  <div class="d-flex form-control form-control-sm">
    <label v-if="label" :for="id" class="mr-3">
      {{ label }}
    </label>

    <div class="d-flex">
      <input :id="id" type="range" :min="min" :max="max" :step="step" class="custom-range"
             :value="value" @input="$emit('input', $event.target.value)"/>
      <label :for="id" class="ml-2 smaller text-secondary w-number">
        {{ (value === 0 && !allowZero) ? '-' : value }}
      </label>
    </div>
  </div>
</template>

<script>
    export default {
        props: {
            id: String,
            value: Number,
            min: {
                type: Number,
                default: 0,
            },
            max: {
                type: Number,
                default: 1,
            },
            step: {
                type: Number,
                default: 0.05,
            },
            label: {
                type: String,
                default: undefined,
            },
            allowZero: {
                type: Boolean,
                default: true,
            },
        },
    }
</script>
