// @TODO: Move everything from core into seperate files and then import into here
import {getText} from './utils';

import home from './home';

getText.load();

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
