import $ from 'jquery';

import config from '../config';
import Notifer from './notifer';

class GrowlNotifer extends Notifer {
    constructor() {
        super('growl');
        this.testUrl = config.srRoot + '/home/testGrowl';
        this.host = null;
        this.password = null;
    }

    test() {
        if (this.host) {
            return $.get(this.testUrl, {
                host: this.host,
                password: this.password
            }).done(this.done);
        }

        return this.disable();
    }
}

export default GrowlNotifer;
