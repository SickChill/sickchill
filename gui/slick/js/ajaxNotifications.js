const test = false;

PNotify.prototype.options.addclass = 'stack-bottomright';
PNotify.prototype.options.buttons.closer_hover = !1; // eslint-disable-line camelcase
PNotify.prototype.options.delay = 5000;
PNotify.prototype.options.hide = !0;
PNotify.prototype.options.history = !1;
PNotify.prototype.options.shadow = !1;
PNotify.prototype.options.stack = {dir1: 'up', dir2: 'left', firstpos1: 25, firstpos2: 25};
PNotify.prototype.options.styling = 'bootstrap3';
PNotify.prototype.options.width = '340px';
PNotify.desktop.permission();
PNotify.prototype.options.desktop = {desktop: !0, icon: srRoot + '/images/ico/favicon-196.png'};

function displayPNotify(type, title, message, id) {
    new PNotify({ // eslint-disable-line no-new
        desktop: {
            tag: id
        },
        type,
        title,
        text: message.replace(/<br[\s/]*(?:\s[^>]*)?>/ig, '\n')
            .replace(/<[/]?b(?:\s[^>]*)?>/ig, '*')
            .replace(/<i(?:\s[^>]*)?>/ig, '[').replace(/<[/]i>/ig, ']')
            .replace(/<(?:[/]?ul|\/li)(?:\s[^>]*)?>/ig, '').replace(/<li(?:\s[^>]*)?>/ig, '\n* ')
    });
}

function checkNotifications() {
    $.getJSON(srRoot + '/ui/get_messages', data => {
        $.each(data, (name, data) => {
            displayPNotify(data.type, data.title, data.message, data.hash);
        });
    });
    setTimeout(() => {
        'use strict';
        checkNotifications();
    }, 3000);
}

$(document).ready(() => {
    checkNotifications();
    if (test) {
        displayPNotify('notice', 'test', 'test<br><i class="test-class">hello <b>world</b></i><ul><li>item 1</li><li>item 2</li></ul>', 'notification-test');
    }
});
