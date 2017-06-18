import $ from 'jquery';

import config from '../config';
import Notifer from './notifer';

class ProwlNotifer extends Notifer {
    constructor() {
        super('prowl');
        this.testUrl = config.srRoot + '/home/testProwl';
        this.api = null;
        this.prority = null;
    }

    test() {
        if (this.api) {
            return $.get(this.testUrl, {
                prowl_api: this.api, // eslint-disable-line camelcase
                prowl_priority: this.priority // eslint-disable-line camelcase
            }).done(this.done);
        }

        return this.disable();
    }
}

export default ProwlNotifer;
