import $ from 'jquery';

import {browser, getText, notifications, siteMessage} from './utils';
import log from './log';
import config from './config';
import scrolltotop from './lib/jquery.scrolltopcontrol-1.1';

import {home, config as configRoute} from './routes';

browser.load();
getText.load();
scrolltotop.init({
    html: `<img src="${config.srRoot}/images/top.gif" width="31" height="11" alt="Jump to top" />`
});
notifications();
siteMessage.getMessages();

const routes = {
    home,
    config: {
        notifications: configRoute.notifications
    }
};

window.routes = routes;

const UTIL = {
    exec(controller, action) {
        action = action === undefined ? 'init' : action;
        action = action === 'index' ? 'root' : action;

        log.info(`Cannot load route ${controller}:${action}`);

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
