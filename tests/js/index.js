const { getMeta } = require("/sickchill/gui/slick/js/core");

const test = require("ava");

test.failing("getMeta", async t => {
    const meta = document.createElement("meta");
    meta.setAttribute("data-var", "scRoot");
    meta.setAttribute("content", "/sickchill");

    t.is(getMeta("scRoot"), "/sickchill");
});
