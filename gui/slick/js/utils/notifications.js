/* global PNotify */
import $ from 'jquery';

import config from '../config';

PNotify.desktop.permission();

PNotify.prototype.options.addclass = 'stack-bottomright';
PNotify.prototype.options.buttons.closer_hover = false; // eslint-disable-line camelcase
PNotify.prototype.options.delay = 5000;
PNotify.prototype.options.hide = true;
PNotify.prototype.options.history = false;
PNotify.prototype.options.shadow = false;
PNotify.prototype.options.stack = {
    dir1: 'up',
    dir2: 'left',
    firstpos1: 25,
    firstpos2: 25
};
PNotify.prototype.options.styling = 'bootstrap3';
PNotify.prototype.options.width = '340px';
PNotify.prototype.options.desktop = {
    desktop: true,
    icon: config.srRoot + '/images/ico/favicon-196.png'
};

const displayPNotify = ({type, title, message, id}) => {
    const opts = {
        desktop: {
            tag: id
        },
        type,
        title,
        text: message.replace(/<br[\s/]*(?:\s[^>]*)?>/ig, '\n')
            .replace(/<[/]?b(?:\s[^>]*)?>/ig, '*')
            .replace(/<i(?:\s[^>]*)?>/ig, '[').replace(/<[/]i>/ig, ']')
            .replace(/<(?:[/]?ul|\/li)(?:\s[^>]*)?>/ig, '').replace(/<li(?:\s[^>]*)?>/ig, '\n* ')
    };
    new PNotify(opts); // eslint-disable-line
};

const checkNotifications = timeout => {
    $.getJSON(config.srRoot + '/ui/get_messages', data => {
        $.each(data, (name, {type, title, message}) => displayPNotify({type, title, message, name}));
    });
    setTimeout(checkNotifications, timeout || 3000);
    if (window.test === true) {
        displayPNotify({type: 'error', title: 'test', message: 'heelo world', name: '0000000000'});
    }
};

export default checkNotifications;
