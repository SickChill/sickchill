const test = false;

function displayPNotify(type, title, message, id) {
    PNotify.desktop.permission();
    const notice = new PNotify({
        desktop: {
            tag: id,
            desktop: true,
            fallback: true,
            menu: true,
            icon: scRoot + '/images/ico/favicon-196.png',
        },
        nonblock: {
            nonblock: true,
        },
        type,
        title,
        text: message.replaceAll(/<br[\s/]*(?:\s[^>]*)?>/gi, '\n')
            .replaceAll(/<\/?b(?:\s[^>]*)?>/gi, '*')
            .replaceAll(/<i(?:\s[^>]*)?>/gi, '[').replaceAll(/<\/i>/gi, ']')
            .replaceAll(/<(?:\/?ul|\/li)(?:\s[^>]*)?>/gi, '').replaceAll(/<li(?:\s[^>]*)?>/gi, '\n* '),
        maxonscreen: 5,
        addclass: 'stack-bottomright',
        closer_hover: true, // eslint-disable-line camelcase
        delay: 8000,
        hide: true,
        history: true,
        shadow: true,
        stack: {dir1: 'up', dir2: 'left', firstpos1: 25, firstpos2: 25},
        styling: 'fontawesome',
        width: '340px',
        destroy: true,
    });
    if (test === true) {
        console.log('sent pnotify with tag: ' + notice.options.desktop.tag);
    }
}

let notificationTimer;
const notificationDown = {
    type: 'error',
    title: 'offline',
    message: 'sickchill is restarting or is not running',
};

function checkNotifications() {
    $.getJSON(scRoot + '/ui/get_messages', data => {
        $.each(data, (name, data) => {
            displayPNotify(data.type, data.title, data.message, data.hash);
        });
    })
        .fail(() => {
            displayPNotify(notificationDown.type, notificationDown.title, notificationDown.message, 'offline-notice');
            clearTimeout(notificationTimer);
        })
        .done(() => {
            notificationTimer = setTimeout(checkNotifications, 3000);
        });
}

$(document).ready(() => {
    checkNotifications();
    if (test) {
        displayPNotify('notice', 'test', 'test<br><i class="test-class">hello <b>world</b></i><ul><li>item 1</li><li>item 2</li></ul>', 'notification-test');
    }
});
