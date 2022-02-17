const test = require('ava');

test.failing('getMeta', t => {
    const meta = document.createElement('meta', {
        'data-var': 'scRoot',
        content: '/sickchill',
    });
    document.body.append(meta);

    t.is(getMeta('scRoot'), '/sickchill');
});
