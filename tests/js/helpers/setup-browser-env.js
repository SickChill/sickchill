import browserEnv from 'browser-env';
import test from 'ava';

browserEnv();

test('1', t => {
    t.is(1, 1);
});
