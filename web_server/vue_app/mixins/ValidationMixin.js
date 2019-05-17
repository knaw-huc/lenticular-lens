export default {
    data() {
        return {
            errors: []
        }
    },
    methods: {
        validateField(field, isValid) {
            isValid ? this.removeError(field) : this.addError(field);
            return !!isValid;
        },

        addError(field) {
            if (!this.errors.includes(field))
                this.errors.push(field);
        },

        removeError(field) {
            const index = this.errors.indexOf(field);
            if (index >= 0)
                this.errors.splice(index, 1);
        }
    }
};