import test from 'ava';

test.failing('getMeta', t => {
    const meta = document.createElement('meta', {
        'data-var': 'srRoot',
        content: 'http://localhost:8081/'
    });
    document.body.appendChild(meta);

    t.is(getMeta('srRoot'), 'http://localhost:8081');
});
