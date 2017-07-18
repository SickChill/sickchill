import test from 'ava';

test.failing('getMeta', t => {
    const meta = document.createElement('meta', {
        'data-var': 'srRoot',
        content: '/sickrage'
    });
    document.body.appendChild(meta);

    t.is(getMeta('srRoot'), '/sickrage');
});
