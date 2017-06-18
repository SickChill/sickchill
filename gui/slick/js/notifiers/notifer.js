import $ from 'jquery';
import dotProp from 'dot-prop';

import {LOADING_TEXT, MISSING_FIELDS} from '../consts';

class Notifer {
    constructor(namespace) {
        this.$el = $(`[namespace="${namespace}"]`);
        this.$testButton = this.$el.find('.btn.test');
        this.$result = this.$el.find('.result');

        this.getFields();
    }

    init() {
        this.$testButton.on('click', this.test.bind(this));
        this.$el.find('[field]').on('change', this.getFields.bind(this));
    }

    test() {}

    disable() {
        this.$el.find(`[field]`).removeClass('warning');
        this.$result.html(LOADING_TEXT);
        this.$testButton.prop('disabled', true);
    }

    missingFields(fields) {
        if (fields) {
            fields = typeof fields === 'string' ? [fields] : fields;
            fields.forEach(field => {
                this.$el.find(`[field=${field}]`).addClass('warning');
            });
        }
        this.$result.html(MISSING_FIELDS);
    }

    getFields() {
        this.$el.find('[field]').each((index, element) => {
            const field = $(element).attr('field');
            const value = $(element).is(':checkbox') ? $(element).is(':checked') : $(element).val();
            dotProp.set(this, field, value);
        });
    }

    done(message) {
        this.$result.html(message);
        this.$testButton.prop('disabled', false);
    }
}

export default Notifer;
