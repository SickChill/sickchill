import $ from 'jquery';

import {browser, getText} from './utils';
import config from './config';
import scrolltotop from './lib/jquery.scrolltopcontrol-1.1';

import {home} from './routes';

browser.load();
getText.load();
scrolltotop.init({
    html: `<img src="${config.srRoot}/images/top.gif" width="31" height="11" alt="Jump to top" />`
});

const routes = {
    home
};

const UTIL = {
    exec(controller, action) {
        action = action === undefined ? 'init' : action;
        action = action === 'index' ? 'root' : action;

        if (controller !== '' && routes[controller] && typeof routes[controller][action] === 'function') {
            routes[controller][action]();
        }
    },
    init() {
        const body = document.body;
        const controller = body.getAttribute('data-controller');
        const action = body.getAttribute('data-action');

        UTIL.exec('common');
        UTIL.exec(controller);
        UTIL.exec(controller, action);
    }
};

$(document).on('ready', UTIL.init);
