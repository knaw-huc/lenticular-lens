<template>
  <div class="d-flex">
    <input :id="id" type="range" :min="min" :max="max" :step="step" class="custom-range"
           :value="value" @input="$emit('input', $event.target.value)"/>
    <label :for="id" class="ml-2 smaller text-secondary w-number">
      {{ value }}
    </label>
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
        },
    }
</script>
