const test = require('ava');

test('getMeta', t => {
    const meta = document.createElement('meta');
    meta.setAttribute('data-var', 'scRoot');
    meta.setAttribute('content', '/sickchill');
    document.head.appendChild(meta);

    t.is(getMeta('scRoot'), '/sickchill');
});
