import $ from 'jquery';

import config from '../config';
import Notifer from './notifer';

class KodiNotifer extends Notifer {
    constructor() {
        super('kodi');
        this.testUrl = config.srRoot + '/home/testKODI';
        this.host = null;
        this.username = null;
        this.password = null;
    }

    test() {
        if (this.host) {
            this.disable();
            return $.get(this.testUrl, {
                host: this.host,
                username: this.username,
                password: this.password
            }).done(data => this.done(data));
        }

        return this.missingFields('host');
    }
}

export default KodiNotifer;
