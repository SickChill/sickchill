window.$ = require('jquery');

window.getMeta = function (pyVar) {
    return $('meta[data-var="' + pyVar + '"]').data('content');
}

window.scRoot = getMeta('scRoot');
window.srDefaultPage = getMeta('srDefaultPage');
window.themeSpinner = getMeta('themeSpinner');
window.anonURL = getMeta('anonURL');
window.topImageHtml = '<img src="' + scRoot + '/images/top.gif" width="31" height="11" alt="Jump to top" />'; // eslint-disable-line no-unused-vars
window.loading = '<img src="' + scRoot + '/images/loading16' + themeSpinner + '.gif" height="16" width="16" />';

window.srPID = getMeta('srPID');
