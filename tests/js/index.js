const test = require('ava');

test.failing('getMeta',
    t => {
        const meta = document.createElement('meta');
        meta.datavar = 'scRoot';
        meta.content = '/sickchill';
        document.body.appendChild(meta);
        t.is(getMeta('scRoot'), '/sickchill');
    });
