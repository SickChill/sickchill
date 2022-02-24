const test = false;

var PNotify = require('@pnotify/core');
import * as PNotifyDesktop from '@pnotify/desktop';
import * as PNotifyMobile from '@pnotify/mobile';
import { defaults } from '@pnotify/core';

defaults.addclass = 'stack-bottomright';
// defaults.buttons.closer_hover = !1; // eslint-disable-line camelcase
defaults.delay = 5000;
defaults.hide = !0;
defaults.history = !1;
defaults.shadow = !1;
defaults.stack = {dir1: 'up', dir2: 'left', firstpos1: 25, firstpos2: 25};
defaults.styling = 'bootstrap3';
defaults.width = '340px';
PNotifyDesktop.permission();
defaults.desktop = {desktop: !0, icon: scRoot + '/images/ico/favicon-196.png'};

function displayPNotify(type, title, message, id) {
    new PNotify({ // eslint-disable-line no-new
        desktop: {
            tag: id,
        },
        type,
        title,
        text: message.replace(/<br[\s/]*(?:\s[^>]*)?>/gi, '\n')
            .replace(/<\/?b(?:\s[^>]*)?>/gi, '*')
            .replace(/<i(?:\s[^>]*)?>/gi, '[').replace(/<\/i>/gi, ']')
            .replace(/<(?:\/?ul|\/li)(?:\s[^>]*)?>/gi, '').replace(/<li(?:\s[^>]*)?>/gi, '\n* '),
    });
}

function checkNotifications() {
    $.getJSON(scRoot + '/ui/get_messages', data => {
        $.each(data, (name, data) => {
            displayPNotify(data.type, data.title, data.message, data.hash);
        });
    });
    setTimeout(checkNotifications, 3000);
}

$(document).ready(() => {
    checkNotifications();
    if (test) {
        displayPNotify('notice', 'test', 'test<br><i class="test-class">hello <b>world</b></i><ul><li>item 1</li><li>item 2</li></ul>', 'notification-test');
    }
});
