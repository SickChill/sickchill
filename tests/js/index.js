import test from 'ava';

test.failing('getMeta', t => {
    const meta = document.createElement('meta', {
        'data-var': 'scRoot',
        content: '/sickchill'
    });
    document.body.appendChild(meta);

    t.is(getMeta('scRoot'), '/sickchill');
});
