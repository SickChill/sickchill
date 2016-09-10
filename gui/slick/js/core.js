// @TODO Move these into common.ini when possible,
//       currently we can't do that as browser.js and a few others need it before this is loaded

function getMeta(pyVar){
    return $('meta[data-var="' + pyVar + '"]').data('content');
}

var srRoot = getMeta('srRoot'),
    srDefaultPage = getMeta('srDefaultPage'),
    srPID = getMeta('srPID'),
    themeSpinner = getMeta('themeSpinner'),
    anonURL = getMeta('anonURL'),
    topImageHtml = '<img src="' + srRoot + '/images/top.gif" width="31" height="11" alt="Jump to top" />', // jshint ignore:line
    loading = '<img src="' + srRoot + '/images/loading16' + themeSpinner + '.gif" height="16" width="16" />';

var configSuccess = function(){
    $('.config_submitter').each(function(){
        $(this).removeAttr("disabled");
        $(this).next().remove();
        $(this).show();
    });
    $('.config_submitter_refresh').each(function(){
        $(this).removeAttr("disabled");
        $(this).next().remove();
        $(this).show();
        window.location.href = srRoot + '/config/providers/';
    });
    $('#email_show').trigger('notify');
    $('#prowl_show').trigger('notify');
};

function metaToBool(pyVar){
    var meta = $('meta[data-var="' + pyVar + '"]').data('content');
    if(meta === undefined){
        console.log(pyVar + ' is empty, did you forget to add this to main.mako?');
        return meta;
    } else {
        meta = (isNaN(meta) ? meta.toLowerCase() : meta.toString());
        return !(meta === 'false' || meta === 'none' || meta === '0');
    }
}

function isMeta(pyVar, result){
    var reg = new RegExp(result.length > 1 ? result.join('|') : result);
    return (reg).test($('meta[data-var="' + pyVar + '"]').data('content'));
}

(function init() {
    var imgDefer = document.getElementsByTagName('img');
    for (var i=0; i<imgDefer.length; i++) {
        if(imgDefer[i].getAttribute('data-src')) {
            imgDefer[i].setAttribute('src',imgDefer[i].getAttribute('data-src'));
        }
    }
})();

$.confirm.options = {
    confirmButton: "Yes",
    cancelButton: "Cancel",
    dialogClass: "modal-dialog",
    post: false,
    confirm: function(e) {
        location.href = e.context.href;
    }
};

$("a.shutdown").confirm({
    title: "Shutdown",
    text: "Are you sure you want to shutdown SickRage?"
});

$("a.restart").confirm({
    title: "Restart",
    text: "Are you sure you want to restart SickRage?"
});

$("a.removeshow").confirm({
    title: "Remove Show",
    text: 'Are you sure you want to remove <span class="footerhighlight">' + $('#showtitle').data('showname') + '</span> from the database?<br><br><input type="checkbox" id="deleteFiles"> <span class="red-text">Check to delete files as well. IRREVERSIBLE</span></input>',
    confirm: function(e) {
        location.href = e.context.href + ($('#deleteFiles')[0].checked ? '&full=1' : '');
    }
});

$('a.clearhistory').confirm({
    title: 'Clear History',
    text: 'Are you sure you want to clear all download history?'
});

$('a.trimhistory').confirm({
    title: 'Trim History',
    text: 'Are you sure you want to trim all download history older than 30 days?'
});

$('a.submiterrors').confirm({
    title: 'Submit Errors',
    text: 'Are you sure you want to submit these errors ?<br><br><span class="red-text">Make sure SickRage is updated and trigger<br> this error with debug enabled before submitting</span>'
});

$("#config-components").tabs({
    activate: function (event, ui) {
        var lastOpenedPanel = $(this).data("lastOpenedPanel");

        if(!lastOpenedPanel) { lastOpenedPanel = $(ui.oldPanel); }

        if(!$(this).data("topPositionTab")) { $(this).data("topPositionTab", $(ui.newPanel).position().top); }

        //Dont use the builtin fx effects. This will fade in/out both tabs, we dont want that
        //Fadein the new tab yourself
        $(ui.newPanel).hide().fadeIn(0);

        if(lastOpenedPanel) {
            // 1. Show the previous opened tab by removing the jQuery UI class
            // 2. Make the tab temporary position:absolute so the two tabs will overlap
            // 3. Set topposition so they will overlap if you go from tab 1 to tab 0
            // 4. Remove position:absolute after animation
            lastOpenedPanel
                .toggleClass("ui-tabs-hide")
                .css("position", "absolute")
                .css("top", $(this).data("topPositionTab") + "px")
                .fadeOut(0, function () {
                    $(this).css("position", "");
                });
        }

        //Saving the last tab has been opened
        $(this).data("lastOpenedPanel", $(ui.newPanel));
    }
});

// @TODO Replace this with a real touchscreen check
// hack alert: if we don't have a touchscreen, and we are already hovering the mouse, then click should link instead of toggle
if((navigator.maxTouchPoints || 0) < 2) {
    $('.dropdown-toggle').on('click', function() {
        var $this = $(this);
        if ($this.attr('aria-expanded') === 'true') {
            window.location.href = $this.attr('href');
        }
    });
}

if(metaToBool('sickbeard.FUZZY_DATING')) {
    $.timeago.settings.allowFuture = true;
    $.timeago.settings.strings = {
        prefixAgo: null,
        prefixFromNow: 'In ',
        suffixAgo: "ago",
        suffixFromNow: "",
        seconds: "less than a minute",
        minute: "about a minute",
        minutes: "%d minutes",
        hour: "an hour",
        hours: "%d hours",
        day: "a day",
        days: "%d days",
        month: "a month",
        months: "%d months",
        year: "a year",
        years: "%d years",
        wordSeparator: " ",
        numbers: []
    };
    $("[datetime]").timeago();
}

$(document.body).on('click', 'a[data-no-redirect]', function(e){
    e.preventDefault();
    $.get($(this).attr('href'));
    return false;
});

$(document.body).on('click', '.bulkCheck', function(){
    var bulkCheck = this;
    var whichBulkCheck = $(bulkCheck).attr('id');

    $('.'+whichBulkCheck+':visible').each(function(){
        $(this).prop('checked', $(bulkCheck).prop('checked'));
    });
});
