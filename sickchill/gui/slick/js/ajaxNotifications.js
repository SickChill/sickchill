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
PNotify.prototype.options.desktop = {desktop: !0, icon: scRoot + '/images/ico/favicon-196.png'};

function displayPNotify(type, title, message, id) {
    new PNotify({ // eslint-disable-line no-new
        desktop: {
            tag: id,
        },
        type,
        title,
        text: message.replaceAll(/<br[\s/]*(?:\s[^>]*)?>/gi, '\n')
            .replaceAll(/<\/?b(?:\s[^>]*)?>/gi, '*')
            .replaceAll(/<i(?:\s[^>]*)?>/gi, '[').replaceAll(/<\/i>/gi, ']')
            .replaceAll(/<(?:\/?ul|\/li)(?:\s[^>]*)?>/gi, '').replaceAll(/<li(?:\s[^>]*)?>/gi, '\n* '),
    });
}

function create_UUID() {
    var dt = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (dt + Math.random() * 16) % 16 | 0;
        dt = Math.floor(dt / 16);
        return (c=='x' ? r :(r&0x3|0x8)).toString(16);
    });
    return uuid;
}

let notificationTimer;
let notificationDown = {
    title: 'error',
    message: 'sickchill is restarting or is not running'
};

function checkNotifications() {
    $.getJSON(scRoot + '/ui/get_messages', data => {
        $.each(data, (name, data) => {
            displayPNotify(data.type, data.title, data.message, data.hash);
        })
        .fail(function () {
            displayPNotify(notificationDown.title, notificationDown.message, create_UUID());
            notificationTimer = clearTimeout(notificationTimer);
        ))
    });
}

$(document).ready(() => {
    notificationTimer = setTimeout(checkNotifications, 3000);
    if (test) {
        displayPNotify('notice', 'test', 'test<br><i class="test-class">hello <b>world</b></i><ul><li>item 1</li><li>item 2</li></ul>', 'notification-test');
    }
});
