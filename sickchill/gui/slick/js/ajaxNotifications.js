const isTest = false;

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
        stack: {
            dir1: 'up', dir2: 'left', firstpos1: 25, firstpos2: 25,
        },
        styling: 'fontawesome',
        width: '340px',
        destroy: true,
    });
    if (isTest) {
        console.log('sent pnotify with tag: ' + notice.options.desktop.tag);
    }
}

let notificationTimer;
let notificationEmptyStreak = 0;
const notificationBaseDelay = 3000;
const notificationMaxDelay = 30_000;
const notificationDown = {
    type: 'error',
    title: 'offline',
    message: 'sickchill is restarting or is not running',
};

function notificationPollDelay(hadMessages) {
    if (hadMessages) {
        notificationEmptyStreak = 0;
        return notificationBaseDelay;
    }

    notificationEmptyStreak += 1;
    return Math.min(notificationBaseDelay * (2 ** Math.min(notificationEmptyStreak, 4)), notificationMaxDelay);
}

function checkNotifications() {
    if (document.hidden) {
        notificationTimer = setTimeout(checkNotifications, 15_000);
        return;
    }

    $.getJSON(scRoot + '/ui/get_messages', data => {
        const messages = data || {};
        $.each(messages, (name, message) => {
            displayPNotify(message.type, message.title, message.message, message.hash);
        });
        notificationTimer = setTimeout(checkNotifications, notificationPollDelay(Object.keys(messages).length > 0));
    })
        .fail(() => {
            displayPNotify(notificationDown.type, notificationDown.title, notificationDown.message, 'offline-notice');
            clearTimeout(notificationTimer);
        });
}

$(document).ready(() => {
    checkNotifications();
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            return;
        }

        clearTimeout(notificationTimer);
        notificationEmptyStreak = 0;
        checkNotifications();
    });
    if (isTest) {
        displayPNotify('notice', 'test', 'test<br><i class="test-class">hello <b>world</b></i><ul><li>item 1</li><li>item 2</li></ul>', 'notification-test');
    }
});
