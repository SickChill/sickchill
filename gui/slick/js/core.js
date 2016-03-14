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

var SICKRAGE = {
    common: {
        init: function() {
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
        }
    },
    config: {
        init: function() {
            $('#config-components').tabs();

            $(".enabler").each(function(){
                if (!$(this).prop('checked')) { $('#content_'+$(this).attr('id')).hide(); }
            });

            $(".enabler").on('click', function() {
                if ($(this).prop('checked')){
                    $('#content_'+$(this).attr('id')).fadeIn("fast", "linear");
                } else {
                    $('#content_'+$(this).attr('id')).fadeOut("fast", "linear");
                }
            });

            $(".viewIf").on('click', function() {
                if ($(this).prop('checked')) {
                    $('.hide_if_'+$(this).attr('id')).css('display','none');
                    $('.show_if_'+$(this).attr('id')).fadeIn("fast", "linear");
                } else {
                    $('.show_if_'+$(this).attr('id')).css('display','none');
                    $('.hide_if_'+$(this).attr('id')).fadeIn("fast", "linear");
                }
            });

            $(".datePresets").on('click', function() {
                var def = $('#date_presets').val();
                if ($(this).prop('checked') && '%x' === def) {
                    def = '%a, %b %d, %Y';
                    $('#date_use_system_default').html('1');
                } else if (!$(this).prop('checked') && '1' === $('#date_use_system_default').html()){
                    def = '%x';
                }

                $('#date_presets').attr('name', 'date_preset_old');
                $('#date_presets').attr('id', 'date_presets_old');

                $('#date_presets_na').attr('name', 'date_preset');
                $('#date_presets_na').attr('id', 'date_presets');

                $('#date_presets_old').attr('name', 'date_preset_na');
                $('#date_presets_old').attr('id', 'date_presets_na');

                if (def) { $('#date_presets').val(def); }
            });

            // bind 'myForm' and provide a simple callback function
            $('#configForm').ajaxForm({
                beforeSubmit: function(){
                    $('.config_submitter .config_submitter_refresh').each(function(){
                        $(this).attr("disabled", "disabled");
                        $(this).after('<span><img src="' + srRoot + '/images/loading16' + themeSpinner + '.gif"> Saving...</span>');
                        $(this).hide();
                    });
                },
                success: function(){
                    setTimeout(function () {
                        "use strict";
                        configSuccess();
                    }, 2000);
                }
            });

            $('#api_key').on('click', function(){
                $('#api_key').select();
            });

            $("#generate_new_apikey").on('click', function(){
                $.get(srRoot + '/config/general/generateApiKey', function(data){
                    if (data.error !== undefined) {
                        alert(data.error);
                        return;
                    }
                    $('#api_key').val(data);
                });
            });

            $('#branchCheckout').on('click', function() {
                var url = srRoot + '/home/branchCheckout?branch=' + $("#branchVersion").val();
                var checkDBversion = srRoot + "/home/getDBcompare";
                $.getJSON(checkDBversion, function(data){
                    if (data.status === "success") {
                        if (data.message === "equal") {
                            //Checkout Branch
                            window.location.href = url;
                        }
                        if (data.message === "upgrade") {
                            if ( confirm("Changing branch will upgrade your database.\nYou won't be able to downgrade afterward.\nDo you want to continue?") ) {
                                //Checkout Branch
                                window.location.href = url;
                            }
                        }
                        if (data.message === "downgrade") {
                            alert("Can't switch branch as this will result in a database downgrade.");
                        }
                    }
                });
            });
        },
        index: function() {
            if ($("input[name='proxy_setting']").val().length === 0) {
                $("input[id='proxy_indexers']").prop('checked', false);
                $("label[for='proxy_indexers']").hide();
            }

            $("input[name='proxy_setting']").on('input', function() {
                if($(this).val().length === 0) {
                    $("input[id='proxy_indexers']").prop('checked', false);
                    $("label[for='proxy_indexers']").hide();
                } else {
                    $("label[for='proxy_indexers']").show();
                }
            });

            $('#log_dir').fileBrowser({ title: 'Select log file folder location' });
        },
        backupRestore: function(){
            $('#Backup').on('click', function() {
                $("#Backup").attr("disabled", true);
                $('#Backup-result').html(loading);
                var backupDir = $("#backupDir").val();
                $.get(srRoot + "/config/backuprestore/backup", {'backupDir': backupDir})
                    .done(function (data) {
                        $('#Backup-result').html(data);
                        $("#Backup").attr("disabled", false);
                    });
            });
            $('#Restore').on('click', function() {
                $("#Restore").attr("disabled", true);
                $('#Restore-result').html(loading);
                var backupFile = $("#backupFile").val();
                $.get(srRoot + "/config/backuprestore/restore", {'backupFile': backupFile})
                    .done(function (data) {
                        $('#Restore-result').html(data);
                        $("#Restore").attr("disabled", false);
                    });
            });

            $('#backupDir').fileBrowser({ title: 'Select backup folder to save to', key: 'backupPath' });
            $('#backupFile').fileBrowser({ title: 'Select backup files to restore', key: 'backupFile', includeFiles: 1 });
            $('#config-components').tabs();
        },
        notifications: function() {
            $('#testGrowl').on('click', function () {
                var growl = {};
                growl.host = $.trim($('#growl_host').val());
                growl.password = $.trim($('#growl_password').val());
                if (!growl.host) {
                    $('#testGrowl-result').html('Please fill out the necessary fields above.');
                    $('#growl_host').addClass('warning');
                    return;
                }
                $('#growl_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testGrowl-result').html(loading);
                $.get(srRoot + '/home/testGrowl', {
                    'host': growl.host,
                    'password': growl.password
                }).done(function (data) {
                    $('#testGrowl-result').html(data);
                    $('#testGrowl').prop('disabled', false);
                });
            });

            $('#testProwl').on('click', function () {
                var prowl = {};
                prowl.api = $.trim($('#prowl_api').val());
                prowl.priority = $('#prowl_priority').val();
                if (!prowl.api) {
                    $('#testProwl-result').html('Please fill out the necessary fields above.');
                    $('#prowl_api').addClass('warning');
                    return;
                }
                $('#prowl_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testProwl-result').html(loading);
                $.get(srRoot + '/home/testProwl', {
                    'prowl_api': prowl.api,
                    'prowl_priority': prowl.priority
                }).done(function (data) {
                    $('#testProwl-result').html(data);
                    $('#testProwl').prop('disabled', false);
                });
            });

            $('#testKODI').on('click', function () {
                var kodi = {};
                kodi.host = $.trim($('#kodi_host').val());
                kodi.username = $.trim($('#kodi_username').val());
                kodi.password = $.trim($('#kodi_password').val());
                if (!kodi.host) {
                    $('#testKODI-result').html('Please fill out the necessary fields above.');
                    $('#kodi_host').addClass('warning');
                    return;
                }
                $('#kodi_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testKODI-result').html(loading);
                $.get(srRoot + '/home/testKODI', {
                    'host': kodi.host,
                    'username': kodi.username,
                    'password': kodi.password
                }).done(function (data) {
                    $('#testKODI-result').html(data);
                    $('#testKODI').prop('disabled', false);
                });
            });

            $('#testPHT').on('click', function () {
                var plex = {};
                plex.client = {};
                plex.client.host = $.trim($('#plex_client_host').val());
                plex.client.username = $.trim($('#plex_client_username').val());
                plex.client.password = $.trim($('#plex_client_password').val());
                if (!plex.client.host) {
                    $('#testPHT-result').html('Please fill out the necessary fields above.');
                    $('#plex_client_host').addClass('warning');
                    return;
                }
                $('#plex_client_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPHT-result').html(loading);
                $.get(srRoot + '/home/testPHT', {
                    'host': plex.client.host,
                    'username': plex.client.username,
                    'password': plex.client.password
                }).done(function (data) {
                    $('#testPHT-result').html(data);
                    $('#testPHT').prop('disabled', false);
                });
            });

            $('#testPMS').on('click', function () {
                var plex = {};
                plex.server = {};
                plex.server.host = $.trim($('#plex_server_host').val());
                plex.server.username = $.trim($('#plex_server_username').val());
                plex.server.password = $.trim($('#plex_server_password').val());
                plex.server.token = $.trim($('#plex_server_token').val());
                if (!plex.server.host) {
                    $('#testPMS-result').html('Please fill out the necessary fields above.');
                    $('#plex_server_host').addClass('warning');
                    return;
                }
                $('#plex_server_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPMS-result').html(loading);
                $.get(srRoot + '/home/testPMS', {
                    'host': plex.server.host,
                    'username': plex.server.username,
                    'password': plex.server.password,
                    'plex_server_token': plex.server.token
                }).done(function (data) {
                    $('#testPMS-result').html(data);
                    $('#testPMS').prop('disabled', false);
                });
            });

            $('#testEMBY').on('click', function () {
                var emby = {};
                emby.host = $('#emby_host').val();
                emby.apikey = $('#emby_apikey').val();
                if (!emby.host || !emby.apikey) {
                    $('#testEMBY-result').html('Please fill out the necessary fields above.');
                    if (!emby.host) {
                        $('#emby_host').addClass('warning');
                    } else {
                        $('#emby_host').removeClass('warning');
                    }
                    if (!emby.apikey) {
                        $('#emby_apikey').addClass('warning');
                    } else {
                        $('#emby_apikey').removeClass('warning');
                    }
                    return;
                }
                $('#emby_host,#emby_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testEMBY-result').html(loading);
                $.get(srRoot + '/home/testEMBY', {
                    'host': emby.host,
                    'emby_apikey': emby.apikey
                }).done(function (data) {
                    $('#testEMBY-result').html(data);
                    $('#testEMBY').prop('disabled', false);
                });
            });

            $('#testBoxcar2').on('click', function () {
                var boxcar2 = {};
                boxcar2.accesstoken = $.trim($('#boxcar2_accesstoken').val());
                if (!boxcar2.accesstoken) {
                    $('#testBoxcar2-result').html('Please fill out the necessary fields above.');
                    $('#boxcar2_accesstoken').addClass('warning');
                    return;
                }
                $('#boxcar2_accesstoken').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testBoxcar2-result').html(loading);
                $.get(srRoot + '/home/testBoxcar2', {
                    'accesstoken': boxcar2.accesstoken
                }).done(function (data) {
                    $('#testBoxcar2-result').html(data);
                    $('#testBoxcar2').prop('disabled', false);
                });
            });

            $('#testPushover').on('click', function () {
                var pushover = {};
                pushover.userkey = $('#pushover_userkey').val();
                pushover.apikey = $('#pushover_apikey').val();
                if (!pushover.userkey || !pushover.apikey) {
                    $('#testPushover-result').html('Please fill out the necessary fields above.');
                    if (!pushover.userkey) {
                        $('#pushover_userkey').addClass('warning');
                    } else {
                        $('#pushover_userkey').removeClass('warning');
                    }
                    if (!pushover.apikey) {
                        $('#pushover_apikey').addClass('warning');
                    } else {
                        $('#pushover_apikey').removeClass('warning');
                    }
                    return;
                }
                $('#pushover_userkey,#pushover_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPushover-result').html(loading);
                $.get(srRoot + '/home/testPushover', {
                    'userKey': pushover.userkey,
                    'apiKey': pushover.apikey
                }).done(function (data) {
                    $('#testPushover-result').html(data);
                    $('#testPushover').prop('disabled', false);
                });
            });

            $('#testLibnotify').on('click', function() {
                $('#testLibnotify-result').html(loading);
                $.get(srRoot + '/home/testLibnotify', function (data) {
                    $('#testLibnotify-result').html(data);
                });
            });

            $('#twitterStep1').on('click', function() {
                $('#testTwitter-result').html(loading);
                $.get(srRoot + '/home/twitterStep1', function (data) {
                    window.open(data);
                }).done(function() {
                    $('#testTwitter-result').html('<b>Step1:</b> Confirm Authorization');
                });
            });

            $('#twitterStep2').on('click', function () {
                var twitter = {};
                twitter.key = $.trim($('#twitter_key').val());
                if (!twitter.key) {
                    $('#testTwitter-result').html('Please fill out the necessary fields above.');
                    $('#twitter_key').addClass('warning');
                    return;
                }
                $('#twitter_key').removeClass('warning');
                $('#testTwitter-result').html(loading);
                $.get(srRoot + '/home/twitterStep2', {
                    'key': twitter.key
                }, function(data) {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#testTwitter').on('click', function() {
                $.get(srRoot + '/home/testTwitter', function(data) {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#settingsNMJ').on('click', function() {
                var nmj = {};
                if (!$('#nmj_host').val()) {
                    alert('Please fill in the Popcorn IP address');
                    $('#nmj_host').focus();
                    return;
                }
                $('#testNMJ-result').html(loading);
                nmj.host = $('#nmj_host').val();

                $.get(srRoot + '/home/settingsNMJ', {'host': nmj.host}, function (data) {
                    if (data === null) {
                        $('#nmj_database').removeAttr('readonly');
                        $('#nmj_mount').removeAttr('readonly');
                    }
                    var JSONData = $.parseJSON(data);
                    $('#testNMJ-result').html(JSONData.message);
                    $('#nmj_database').val(JSONData.database);
                    $('#nmj_mount').val(JSONData.mount);

                    if (JSONData.database) {
                        $('#nmj_database').attr('readonly', true);
                    } else {
                        $('#nmj_database').removeAttr('readonly');
                    }
                    if (JSONData.mount) {
                        $('#nmj_mount').attr('readonly', true);
                    } else {
                        $('#nmj_mount').removeAttr('readonly');
                    }
                });
            });

            $('#testNMJ').on('click', function () {
                var nmj = {};
                nmj.host = $.trim($('#nmj_host').val());
                nmj.database = $('#nmj_database').val();
                nmj.mount = $('#nmj_mount').val();
                if (!nmj.host) {
                    $('#testNMJ-result').html('Please fill out the necessary fields above.');
                    $('#nmj_host').addClass('warning');
                    return;
                }
                $('#nmj_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testNMJ-result').html(loading);
                $.get(srRoot + '/home/testNMJ', {
                    'host': nmj.host,
                    'database': nmj.database,
                    'mount': nmj.mount
                }).done(function (data) {
                    $('#testNMJ-result').html(data);
                    $('#testNMJ').prop('disabled', false);
                });
            });

            $('#settingsNMJv2').on('click', function() {
                var nmjv2 = {};
                if(!$('#nmjv2_host').val()) {
                    alert('Please fill in the Popcorn IP address');
                    $('#nmjv2_host').focus();
                    return;
                }
                $('#testNMJv2-result').html(loading);
                nmjv2.host = $('#nmjv2_host').val();
                nmjv2.dbloc = '';
                var radios = document.getElementsByName('nmjv2_dbloc');
                for(var i = 0, len = radios.length; i < len; i++) {
                    if (radios[i].checked) {
                        nmjv2.dbloc = radios[i].value;
                        break;
                    }
                }

                nmjv2.dbinstance=$('#NMJv2db_instance').val();
                $.get(srRoot + '/home/settingsNMJv2', {
                    'host': nmjv2.host,
                    'dbloc': nmjv2.dbloc,
                    'instance': nmjv2.dbinstance
                }, function (data){
                    if (data === null) {
                        $('#nmjv2_database').removeAttr('readonly');
                    }
                    var JSONData = $.parseJSON(data);
                    $('#testNMJv2-result').html(JSONData.message);
                    $('#nmjv2_database').val(JSONData.database);

                    if (JSONData.database){
                        $('#nmjv2_database').attr('readonly', true);
                    } else {
                        $('#nmjv2_database').removeAttr('readonly');
                    }
                });
            });

            $('#testNMJv2').on('click', function () {
                var nmjv2 = {};
                nmjv2.host = $.trim($('#nmjv2_host').val());
                if (!nmjv2.host) {
                    $('#testNMJv2-result').html('Please fill out the necessary fields above.');
                    $('#nmjv2_host').addClass('warning');
                    return;
                }
                $('#nmjv2_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testNMJv2-result').html(loading);
                $.get(srRoot + '/home/testNMJv2', {
                    'host': nmjv2.host
                }) .done(function (data) {
                    $('#testNMJv2-result').html(data);
                    $('#testNMJv2').prop('disabled', false);
                });
            });

            $('#testFreeMobile').on('click', function () {
                var freemobile = {};
                freemobile.id = $.trim($('#freemobile_id').val());
                freemobile.apikey = $.trim($('#freemobile_apikey').val());
                if (!freemobile.id || !freemobile.apikey) {
                    $('#testFreeMobile-result').html('Please fill out the necessary fields above.');
                    if (!freemobile.id) {
                        $('#freemobile_id').addClass('warning');
                    } else {
                        $('#freemobile_id').removeClass('warning');
                    }
                    if (!freemobile.apikey) {
                        $('#freemobile_apikey').addClass('warning');
                    } else {
                        $('#freemobile_apikey').removeClass('warning');
                    }
                    return;
                }
                $('#freemobile_id,#freemobile_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testFreeMobile-result').html(loading);
                $.get(srRoot + '/home/testFreeMobile', {
                    'freemobile_id': freemobile.id,
                    'freemobile_apikey': freemobile.apikey
                }).done(function (data) {
                    $('#testFreeMobile-result').html(data);
                    $('#testFreeMobile').prop('disabled', false);
                });
            });

            $('#testTelegram').on('click', function () {
                var telegram = {};
                telegram.id = $.trim($('#telegram_id').val());
                telegram.apikey = $.trim($('#telegram_apikey').val());
                if (!telegram.id || !telegram.apikey) {
                    $('#testTelegram-result').html('Please fill out the necessary fields above.');
                    if (!telegram.id) {
                        $('#telegram_id').addClass('warning');
                    } else {
                        $('#telegram_id').removeClass('warning');
                    }
                    if (!telegram.apikey) {
                        $('#telegram_apikey').addClass('warning');
                    } else {
                        $('#telegram_apikey').removeClass('warning');
                    }
                    return;
                }
                $('#telegram_id,#telegram_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testTelegram-result').html(loading);
                $.get(srRoot + '/home/testTelegram', {
                    'telegram_id': telegram.id,
                    'telegram_apikey': telegram.apikey
                }).done(function (data) {
                    $('#testTelegram-result').html(data);
                    $('#testTelegram').prop('disabled', false);
                });
            });

            $('#TraktGetPin').on('click', function () {
                window.open($('#trakt_pin_url').val(), "popUp", "toolbar=no, scrollbars=no, resizable=no, top=200, left=200, width=650, height=550");
                $('#trakt_pin').removeClass('hide');
            });

            $('#trakt_pin').on('keyup change', function(){
                if ($('#trakt_pin').val().length !== 0) {
                    $('#TraktGetPin').addClass('hide');
                    $('#authTrakt').removeClass('hide');
                } else {
                    $('#TraktGetPin').removeClass('hide');
                    $('#authTrakt').addClass('hide');
                }
            });

            $('#authTrakt').on('click', function() {
                var trakt = {};
                trakt.pin = $('#trakt_pin').val();
                if (trakt.pin.length !== 0) {
                    $.get(srRoot + '/home/getTraktToken', {
                        'trakt_pin': trakt.pin
                    }).done(function (data) {
                        $('#testTrakt-result').html(data);
                        $('#authTrakt').addClass('hide');
                        $('#trakt_pin').addClass('hide');
                        $('#TraktGetPin').addClass('hide');
                    });
                }
            });

            $('#testTrakt').on('click', function () {
                var trakt = {};
                trakt.username = $.trim($('#trakt_username').val());
                trakt.trendingBlacklist = $.trim($('#trakt_blacklist_name').val());
                if (!trakt.username) {
                    $('#testTrakt-result').html('Please fill out the necessary fields above.');
                    if (!trakt.username) {
                        $('#trakt_username').addClass('warning');
                    } else {
                        $('#trakt_username').removeClass('warning');
                    }
                    return;
                }

                if (/\s/g.test(trakt.trendingBlacklist)) {
                    $('#testTrakt-result').html('Check blacklist name; the value needs to be a trakt slug');
                    $('#trakt_blacklist_name').addClass('warning');
                    return;
                }
                $('#trakt_username').removeClass('warning');
                $('#trakt_blacklist_name').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testTrakt-result').html(loading);
                $.get(srRoot + '/home/testTrakt', {
                    'username': trakt.username,
                    'blacklist_name': trakt.trendingBlacklist
                }).done(function (data) {
                    $('#testTrakt-result').html(data);
                    $('#testTrakt').prop('disabled', false);
                });
            });

            $('#testEmail').on('click', function () {
                var status, host, port, tls, from, user, pwd, err, to;
                status = $('#testEmail-result');
                status.html(loading);
                host = $('#email_host').val();
                host = host.length > 0 ? host : null;
                port = $('#email_port').val();
                port = port.length > 0 ? port : null;
                tls = $('#email_tls').attr('checked') !== undefined ? 1 : 0;
                from = $('#email_from').val();
                from = from.length > 0 ? from : 'root@localhost';
                user = $('#email_user').val().trim();
                pwd = $('#email_password').val();
                err = '';
                if (host === null) {
                    err += '<li style="color: red;">You must specify an SMTP hostname!</li>';
                }
                if (port === null) {
                    err += '<li style="color: red;">You must specify an SMTP port!</li>';
                } else if (port.match(/^\d+$/) === null || parseInt(port, 10) > 65535) {
                    err += '<li style="color: red;">SMTP port must be between 0 and 65535!</li>';
                }
                if (err.length > 0) {
                    err = '<ol>' + err + '</ol>';
                    status.html(err);
                } else {
                    to = prompt('Enter an email address to send the test to:', null);
                    if (to === null || to.length === 0 || to.match(/.*@.*/) === null) {
                        status.html('<p style="color: red;">You must provide a recipient email address!</p>');
                    } else {
                        $.get(srRoot + '/home/testEmail', {
                            'host': host,
                            'port': port,
                            'smtp_from': from, // @TODO we shouldn't be using any reserved words like "from"
                            'use_tls': tls,
                            'user': user,
                            'pwd': pwd,
                            'to': to
                        }, function (msg) {
                            $('#testEmail-result').html(msg);
                        });
                    }
                }
            });

            $('#testNMA').on('click', function () {
                var nma = {};
                nma.api = $.trim($('#nma_api').val());
                nma.priority = $('#nma_priority').val();
                if (!nma.api) {
                    $('#testNMA-result').html('Please fill out the necessary fields above.');
                    $('#nma_api').addClass('warning');
                    return;
                }
                $('#nma_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testNMA-result').html(loading);
                $.get(srRoot + '/home/testNMA', {
                    'nma_api': nma.api,
                    'nma_priority': nma.priority
                }).done(function (data) {
                    $('#testNMA-result').html(data);
                    $('#testNMA').prop('disabled', false);
                });
            });

            $('#testPushalot').on('click', function () {
                var pushalot = {};
                pushalot.authToken = $.trim($('#pushalot_authorizationtoken').val());
                if (!pushalot.authToken) {
                    $('#testPushalot-result').html('Please fill out the necessary fields above.');
                    $('#pushalot_authorizationtoken').addClass('warning');
                    return;
                }
                $('#pushalot_authorizationtoken').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPushalot-result').html(loading);
                $.get(srRoot + '/home/testPushalot', {
                    'authorizationToken': pushalot.authToken
                }).done(function (data) {
                    $('#testPushalot-result').html(data);
                    $('#testPushalot').prop('disabled', false);
                });
            });

            $('#testPushbullet').on('click', function () {
                var pushbullet = {};
                pushbullet.api = $.trim($('#pushbullet_api').val());
                if (!pushbullet.api) {
                    $('#testPushbullet-result').html('Please fill out the necessary fields above.');
                    $('#pushbullet_api').addClass('warning');
                    return;
                }
                $('#pushbullet_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPushbullet-result').html(loading);
                $.get(srRoot + '/home/testPushbullet', {
                    'api': pushbullet.api
                }).done(function (data) {
                    $('#testPushbullet-result').html(data);
                    $('#testPushbullet').prop('disabled', false);
                });
            });

            function getPushbulletDevices(msg){
                var pushbullet = {};
                pushbullet.api = $("#pushbullet_api").val();

                if(msg) {
                    $('#testPushbullet-result').html(loading);
                }

                if(!pushbullet.api) {
                    $('#testPushbullet-result').html("You didn't supply a Pushbullet api key");
                    $("#pushbullet_api").focus();
                    return false;
                }

                $.get(srRoot + "/home/getPushbulletDevices", {
                    'api': pushbullet.api
                }, function (data) {
                    pushbullet.devices = $.parseJSON(data).devices;
                    pushbullet.currentDevice = $("#pushbullet_device").val();
                    $("#pushbullet_device_list").html('');
                    for (var i = 0, len = pushbullet.devices.length; i < len; i++) {
                        if(pushbullet.devices[i].active === true) {
                            if(pushbullet.currentDevice === pushbullet.devices[i].iden) {
                                $("#pushbullet_device_list").append('<option value="'+pushbullet.devices[i].iden+'" selected>' + pushbullet.devices[i].nickname + '</option>');
                            } else {
                                $("#pushbullet_device_list").append('<option value="'+pushbullet.devices[i].iden+'">' + pushbullet.devices[i].nickname + '</option>');
                            }
                        }
                    }
                    $("#pushbullet_device_list").prepend('<option value="" '+ (pushbullet.currentDevice === '' ? 'selected' : '') + '>All devices</option>');
                    if(msg) { $('#testPushbullet-result').html(msg); }
                });

                $("#pushbullet_device_list").on('change', function(){
                    $("#pushbullet_device").val($("#pushbullet_device_list").val());
                    $('#testPushbullet-result').html("Don't forget to save your new pushbullet settings.");
                });
            }

            $('#getPushbulletDevices').on('click', function(){
                getPushbulletDevices("Device list updated. Please choose a device to push to.");
            });

            // we have to call this function on dom ready to create the devices select
            getPushbulletDevices();

            $('#email_show').on('change', function() {
                var key = parseInt($('#email_show').val(), 10);
                $.getJSON(srRoot + "/home/loadShowNotifyLists", function(notifyData) {
                    if (notifyData._size > 0) {
                        $('#email_show_list').val(key >= 0 ? notifyData[key.toString()].list : '');
                    }
                });
            });
            $('#prowl_show').on('change', function() {
                var key = parseInt($('#prowl_show').val(), 10);
                $.getJSON(srRoot + "/home/loadShowNotifyLists", function(notifyData) {
                    if (notifyData._size > 0) {
                        $('#prowl_show_list').val(key >= 0 ? notifyData[key.toString()].prowl_notify_list  : '');   // jshint ignore:line
                    }
                });
            });

            function loadShowNotifyLists() {
                $.getJSON(srRoot + "/home/loadShowNotifyLists", function(list) {
                    var html, s;
                    if (list._size === 0) { return; }

                    // Convert the 'list' object to a js array of objects so that we can sort it
                    var _list = [];
                    for (s in list) {
                        if (s.charAt(0) !== '_') {
                            _list.push(list[s]);
                        }
                    }
                    var sortedList = _list.sort(function(a,b) {
                        if (a.name < b.name) { return -1; }
                        if (a.name > b.name) { return 1;  }
                        return 0;
                    });
                    html = '<option value="-1">-- Select --</option>';
                    for (s in sortedList) {
                        if (sortedList[s].id && sortedList[s].name) {
                            html += '<option value="' + sortedList[s].id + '">' + $('<div/>').text(sortedList[s].name).html() + '</option>';
                        }
                    }
                    $('#email_show').html(html);
                    $('#email_show_list').val('');

                    $('#prowl_show').html(html);
                    $('#prowl_show_list').val('');
                });
            }
            // Load the per show notify lists everytime this page is loaded
            loadShowNotifyLists();

            // Update the internal data struct anytime settings are saved to the server
            $('#email_show').on('notify', function() {
                loadShowNotifyLists();
            });
            $('#prowl_show').on('notify', function() {
                loadShowNotifyLists();
            });

            $('#email_show_save').on('click', function() {
                $.post(srRoot + "/home/saveShowNotifyList", {
                    show: $('#email_show').val(),
                    emails: $('#email_show_list').val()
                }, function() {
                    // Reload the per show notify lists to reflect changes
                    loadShowNotifyLists();
                });
            });
            $('#prowl_show_save').on('click', function() {
                $.post(srRoot + "/home/saveShowNotifyList", {
                    'show': $('#prowl_show').val(),
                    'prowlAPIs': $('#prowl_show_list').val()
                }, function() {
                    // Reload the per show notify lists to reflect changes
                    loadShowNotifyLists();
                });
            });

            // show instructions for plex when enabled
            $('#use_plex_server').on('click', function() {
                if ($(this).is(':checked')) {
                    $('.plexinfo').removeClass('hide');
                } else {
                    $('.plexinfo').addClass('hide');
                }
            });
        },
        postProcessing: function() {
            $('#config-components').tabs();
            $('#tv_download_dir').fileBrowser({ title: 'Select TV Download Directory' });

            // http://stackoverflow.com/questions/2219924/idiomatic-jquery-delayed-event-only-after-a-short-pause-in-typing-e-g-timew
            var typewatch = (function () {
                var timer = 0;
                return function (callback, ms) {
                    clearTimeout(timer);
                    timer = setTimeout(callback, ms);
                };
            })();

            function isRarSupported() {
                $.get(srRoot + '/config/postProcessing/isRarSupported', function (data) {
                    if (data !== "supported") {
                        $('#unpack').qtip('option', {
                            'content.text': 'Unrar Executable not found.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#unpack').qtip('toggle', true);
                        $('#unpack').css('background-color', '#FFFFDD');
                    }
                });
            }

            function fillExamples() {
                var example = {};

                example.pattern = $('#naming_pattern').val();
                example.multi = $('#naming_multi_ep :selected').val();
                example.animeType = $('input[name="naming_anime"]:checked').val();

                $.get(srRoot + '/config/postProcessing/testNaming', {
                    'pattern': example.pattern,
                    'anime_type': 3 // jshint ignore:line
                }, function (data) {
                    if (data) {
                        $('#naming_example').text(data + '.ext');
                        $('#naming_example_div').show();
                    } else {
                        $('#naming_example_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/testNaming', {
                    'pattern': example.pattern,
                    'multi': example.multi,
                    'anime_type': 3
                }, function (data) {
                    if (data) {
                        $('#naming_example_multi').text(data + '.ext');
                        $('#naming_example_multi_div').show();
                    } else {
                        $('#naming_example_multi_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {
                    'pattern': example.pattern,
                    'multi': example.multi,
                    'anime_type': example.animeType
                }, function (data) {
                    if (data === "invalid") {
                        $('#naming_pattern').qtip('option', {
                            'content.text': 'This pattern is invalid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFDDDD');
                    } else if (data === "seasonfolders") {
                        $('#naming_pattern').qtip('option', {
                            'content.text': 'This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFFFDD');
                    } else {
                        $('#naming_pattern').qtip('option', {
                            'content.text': 'This pattern is valid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                        });
                        $('#naming_pattern').qtip('toggle', false);
                        $('#naming_pattern').css('background-color', '#FFFFFF');
                    }
                });
            }

            function fillAbdExamples() {
                var pattern = $('#naming_abd_pattern').val();

                $.get(srRoot + '/config/postProcessing/testNaming', {
                    'pattern': pattern,
                    'abd': 'True'
                }, function (data) {
                    if (data) {
                        $('#naming_abd_example').text(data + '.ext');
                        $('#naming_abd_example_div').show();
                    } else {
                        $('#naming_abd_example_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {
                    'pattern': pattern,
                    'abd': 'True'
                }, function (data) {
                    if (data === "invalid") {
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': 'This pattern is invalid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_abd_pattern').qtip('toggle', true);
                        $('#naming_abd_pattern').css('background-color', '#FFDDDD');
                    } else if (data === "seasonfolders") {
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': 'This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_abd_pattern').qtip('toggle', true);
                        $('#naming_abd_pattern').css('background-color', '#FFFFDD');
                    } else {
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': 'This pattern is valid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                        });
                        $('#naming_abd_pattern').qtip('toggle', false);
                        $('#naming_abd_pattern').css('background-color', '#FFFFFF');
                    }
                });
            }

            function fillSportsExamples() {
                var pattern = $('#naming_sports_pattern').val();

                $.get(srRoot + '/config/postProcessing/testNaming', {
                    'pattern': pattern,
                    'sports': 'True' // @TODO does this actually need to be a string or can it be a boolean?
                }, function (data) {
                    if (data) {
                        $('#naming_sports_example').text(data + '.ext');
                        $('#naming_sports_example_div').show();
                    } else {
                        $('#naming_sports_example_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {
                    'pattern': pattern,
                    'sports': 'True' // @TODO does this actually need to be a string or can it be a boolean?
                }, function (data) {
                    if (data === "invalid") {
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': 'This pattern is invalid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_sports_pattern').qtip('toggle', true);
                        $('#naming_sports_pattern').css('background-color', '#FFDDDD');
                    } else if (data === "seasonfolders") {
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': 'This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_sports_pattern').qtip('toggle', true);
                        $('#naming_sports_pattern').css('background-color', '#FFFFDD');
                    } else {
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': 'This pattern is valid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                        });
                        $('#naming_sports_pattern').qtip('toggle', false);
                        $('#naming_sports_pattern').css('background-color', '#FFFFFF');
                    }
                });
            }

            function fillAnimeExamples() {
                var example = {};
                example.pattern = $('#naming_anime_pattern').val();
                example.multi = $('#naming_anime_multi_ep :selected').val();
                example.animeType = $('input[name="naming_anime"]:checked').val();

                $.get(srRoot + '/config/postProcessing/testNaming', {
                    'pattern': example.pattern,
                    'anime_type': example.animeType
                }, function (data) {
                    if (data) {
                        $('#naming_example_anime').text(data + '.ext');
                        $('#naming_example_anime_div').show();
                    } else {
                        $('#naming_example_anime_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/testNaming', {
                    'pattern': example.pattern,
                    'multi': example.multi,
                    'anime_type': example.animeType
                }, function (data) {
                    if (data) {
                        $('#naming_example_multi_anime').text(data + '.ext');
                        $('#naming_example_multi_anime_div').show();
                    } else {
                        $('#naming_example_multi_anime_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {
                    'pattern': example.pattern,
                    'multi': example.multi,
                    'anime_type': example.animeType
                }, function (data) {
                    if (data === "invalid") {
                        $('#naming_pattern').qtip('option', {
                            'content.text': 'This pattern is invalid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFDDDD');
                    } else if (data === "seasonfolders") {
                        $('#naming_pattern').qtip('option', {
                            'content.text': 'This pattern would be invalid without the folders, using it will force "Flatten" off for all shows.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFFFDD');
                    } else {
                        $('#naming_pattern').qtip('option', {
                            'content.text': 'This pattern is valid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                        });
                        $('#naming_pattern').qtip('toggle', false);
                        $('#naming_pattern').css('background-color', '#FFFFFF');
                    }
                });
            }

            // @TODO all of these setup funcitons should be able to be rolled into a generic jQuery function

            function setupNaming() {
                // if it is a custom selection then show the text box
                if ($('#name_presets :selected').val().toLowerCase() === "custom...") {
                    $('#naming_custom').show();
                } else {
                    $('#naming_custom').hide();
                    $('#naming_pattern').val($('#name_presets :selected').attr('id'));
                }
                fillExamples();
            }

            function setupAbdNaming() {
                // if it is a custom selection then show the text box
                if ($('#name_abd_presets :selected').val().toLowerCase() === "custom...") {
                    $('#naming_abd_custom').show();
                } else {
                    $('#naming_abd_custom').hide();
                    $('#naming_abd_pattern').val($('#name_abd_presets :selected').attr('id'));
                }
                fillAbdExamples();
            }

            function setupSportsNaming() {
                // if it is a custom selection then show the text box
                if ($('#name_sports_presets :selected').val().toLowerCase() === "custom...") {
                    $('#naming_sports_custom').show();
                } else {
                    $('#naming_sports_custom').hide();
                    $('#naming_sports_pattern').val($('#name_sports_presets :selected').attr('id'));
                }
                fillSportsExamples();
            }

            function setupAnimeNaming() {
                // if it is a custom selection then show the text box
                if ($('#name_anime_presets :selected').val().toLowerCase() === "custom...") {
                    $('#naming_anime_custom').show();
                } else {
                    $('#naming_anime_custom').hide();
                    $('#naming_anime_pattern').val($('#name_anime_presets :selected').attr('id'));
                }
                fillAnimeExamples();
            }

            $('#unpack').on('change', function(){
                if(this.checked) {
                    isRarSupported();
                } else {
                    $('#unpack').qtip('toggle', false);
                }
            });

            // @TODO all of these on change funcitons should be able to be rolled into a generic jQuery function or maybe we could
            //       move all of the setup functions into these handlers?

            $('#name_presets').on('change', function(){
                setupNaming();
            });

            $('#name_abd_presets').on('change', function(){
                setupAbdNaming();
            });

            $('#naming_custom_abd').on('change', function(){
                setupAbdNaming();
            });

            $('#name_sports_presets').on('change', function(){
                setupSportsNaming();
            });

            $('#naming_custom_sports').on('change', function(){
                setupSportsNaming();
            });

            $('#name_anime_presets').on('change', function(){
                setupAnimeNaming();
            });

            $('#naming_custom_anime').on('change', function(){
                setupAnimeNaming();
            });

            $('input[name="naming_anime"]').on('click', function(){
                setupAnimeNaming();
            });

            // @TODO We might be able to change these from typewatch to _ debounce like we've done on the log page
            //       The main reason for doing this would be to use only open source stuff that's still being maintained

            $('#naming_multi_ep').on('change', fillExamples);
            $('#naming_pattern').on('focusout', fillExamples);
            $('#naming_pattern').on('keyup', function() {
                typewatch(function () {
                    fillExamples();
                }, 500);
            });

            $('#naming_anime_multi_ep').on('change', fillAnimeExamples);
            $('#naming_anime_pattern').on('focusout', fillAnimeExamples);
            $('#naming_anime_pattern').on('keyup', function() {
                typewatch(function () {
                    fillAnimeExamples();
                }, 500);
            });

            $('#naming_abd_pattern').on('focusout', fillExamples);
            $('#naming_abd_pattern').on('keyup', function() {
                typewatch(function () {
                    fillAbdExamples();
                }, 500);
            });

            $('#naming_sports_pattern').on('focusout', fillExamples);
            $('#naming_sports_pattern').on('keyup', function() {
                typewatch(function () {
                    fillSportsExamples();
                }, 500);
            });

            $('#naming_anime_pattern').on('focusout', fillExamples);
            $('#naming_anime_pattern').on('keyup', function() {
                typewatch(function () {
                    fillAnimeExamples();
                }, 500);
            });

            $('#show_naming_key').on('click', function(){
                $('#naming_key').toggle();
            });
            $('#show_naming_abd_key').on('click', function(){
                $('#naming_abd_key').toggle();
            });
            $('#show_naming_sports_key').on('click', function(){
                $('#naming_sports_key').toggle();
            });
            $('#show_naming_anime_key').on('click', function(){
                $('#naming_anime_key').toggle();
            });
            $('#do_custom').on('click', function(){
                $('#naming_pattern').val($('#name_presets :selected').attr('id'));
                $('#naming_custom').show();
                $('#naming_pattern').focus();
            });

            // @TODO We should see if these can be added with the on click or if we need to even call them on load
            setupNaming();
            setupAbdNaming();
            setupSportsNaming();
            setupAnimeNaming();

            // -- start of metadata options div toggle code --
            $('#metadataType').on('change keyup', function () {
                $(this).showHideMetadata();
            });

            $.fn.showHideMetadata = function () {
                $('.metadataDiv').each(function () {
                    var targetName = $(this).attr('id');
                    var selectedTarget = $('#metadataType :selected').val();

                    if (selectedTarget === targetName) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            };
            //initialize to show the div
            $(this).showHideMetadata();
            // -- end of metadata options div toggle code --

            $('.metadata_checkbox').on('click', function(){
                $(this).refreshMetadataConfig(false);
            });

            $.fn.refreshMetadataConfig = function (first) {
                var curMost = 0;
                var curMostProvider = '';

                $('.metadataDiv').each(function () {
                    var generatorName = $(this).attr('id');

                    var configArray = [];
                    var showMetadata = $("#" + generatorName + "_show_metadata").prop('checked');
                    var episodeMetadata = $("#" + generatorName + "_episode_metadata").prop('checked');
                    var fanart = $("#" + generatorName + "_fanart").prop('checked');
                    var poster = $("#" + generatorName + "_poster").prop('checked');
                    var banner = $("#" + generatorName + "_banner").prop('checked');
                    var episodeThumbnails = $("#" + generatorName + "_episode_thumbnails").prop('checked');
                    var seasonPosters = $("#" + generatorName + "_season_posters").prop('checked');
                    var seasonBanners = $("#" + generatorName + "_season_banners").prop('checked');
                    var seasonAllPoster = $("#" + generatorName + "_season_all_poster").prop('checked');
                    var seasonAllBanner = $("#" + generatorName + "_season_all_banner").prop('checked');

                    configArray.push(showMetadata ? '1' : '0');
                    configArray.push(episodeMetadata ? '1' : '0');
                    configArray.push(fanart ? '1' : '0');
                    configArray.push(poster ? '1' : '0');
                    configArray.push(banner ? '1' : '0');
                    configArray.push(episodeThumbnails ? '1' : '0');
                    configArray.push(seasonPosters ? '1' : '0');
                    configArray.push(seasonBanners ? '1' : '0');
                    configArray.push(seasonAllPoster ? '1' : '0');
                    configArray.push(seasonAllBanner ? '1' : '0');

                    var curNumber = 0;
                    for (var i = 0, len = configArray.length; i < len; i++) {
                        curNumber += parseInt(configArray[i]);
                    }
                    if (curNumber > curMost) {
                        curMost = curNumber;
                        curMostProvider = generatorName;
                    }

                    $("#" + generatorName + "_eg_show_metadata").attr('class', showMetadata ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_eg_episode_metadata").attr('class', episodeMetadata ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_eg_fanart").attr('class', fanart ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_eg_poster").attr('class', poster ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_eg_banner").attr('class', banner ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_eg_episode_thumbnails").attr('class', episodeThumbnails ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_eg_season_posters").attr('class', seasonPosters ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_eg_season_banners").attr('class', seasonBanners ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_eg_season_all_poster").attr('class', seasonAllPoster ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_eg_season_all_banner").attr('class', seasonAllBanner ? 'enabled' : 'disabled');
                    $("#" + generatorName + "_data").val(configArray.join('|'));

                });

                if (curMostProvider !== '' && first) {
                    $('#metadataType option[value=' + curMostProvider + ']').attr('selected', 'selected');
                    $(this).showHideMetadata();
                }
            };

            $(this).refreshMetadataConfig(true);
            $('img[title]').qtip({
                position: {
                    viewport: $(window),
                    at: 'bottom center',
                    my: 'top right'
                },
                style: {
                    tip: {
                        corner: true,
                        method: 'polygon'
                    },
                    classes: 'qtip-shadow qtip-dark'
                }
            });
            $('i[title]').qtip({
                position: {
                    viewport: $(window),
                    at: 'top center',
                    my: 'bottom center'
                },
                style: {
                    tip: {
                        corner: true,
                        method: 'polygon'
                    },
                    classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'
                }
            });
            $('.custom-pattern,#unpack').qtip({
                content: 'validating...',
                show: {
                    event: false,
                    ready: false
                },
                hide: false,
                position: {
                    viewport: $(window),
                    at: 'center left',
                    my: 'center right'
                },
                style: {
                    tip: {
                        corner: true,
                        method: 'polygon'
                    },
                    classes: 'qtip-rounded qtip-shadow qtip-red'
                }
            });
        },
        search: function() {
            $('#config-components').tabs();
            $('#nzb_dir').fileBrowser({ title: 'Select .nzb black hole/watch location' });
            $('#torrent_dir').fileBrowser({ title: 'Select .torrent black hole/watch location' });
            $('#torrent_path').fileBrowser({ title: 'Select .torrent download location' });

            $.fn.nzbMethodHandler = function() {
                var selectedProvider = $('#nzb_method :selected').val(),
                    blackholeSettings = '#blackhole_settings',
                    sabnzbdSettings = '#sabnzbd_settings',
                    testSABnzbd = '#testSABnzbd',
                    testSABnzbdResult = '#testSABnzbd_result',
                    nzbgetSettings = '#nzbget_settings';

                $('#nzb_method_icon').removeClass (function (index, css) {
                    return (css.match (/(^|\s)add-client-icon-\S+/g) || []).join(' ');
                });
                $('#nzb_method_icon').addClass('add-client-icon-' + selectedProvider.replace('_', '-'));

                $(blackholeSettings).hide();
                $(sabnzbdSettings).hide();
                $(testSABnzbd).hide();
                $(testSABnzbdResult).hide();
                $(nzbgetSettings).hide();

                if (selectedProvider.toLowerCase() === 'blackhole') {
                    $(blackholeSettings).show();
                } else if (selectedProvider.toLowerCase() === 'nzbget') {
                    $(nzbgetSettings).show();
                } else {
                    $(sabnzbdSettings).show();
                    $(testSABnzbd).show();
                    $(testSABnzbdResult).show();
                }
            };

            $.torrentMethodHandler = function() {
                $('#options_torrent_clients').hide();
                $('#options_torrent_blackhole').hide();

                var selectedProvider = $('#torrent_method :selected').val(),
                    host = ' host:port',
                    username = ' username',
                    password = ' password',
                    client = '',
                    optionPanel = '#options_torrent_blackhole',
                    rpcurl = ' RPC URL';

                $('#torrent_method_icon').removeClass (function (index, css) {
                    return (css.match (/(^|\s)add-client-icon-\S+/g) || []).join(' ');
                });
                $('#torrent_method_icon').addClass('add-client-icon-' + selectedProvider.replace('_', '-'));

                if (selectedProvider.toLowerCase() !== 'blackhole') {
                    $('#label_warning_deluge').hide();
                    $('#label_anime_warning_deluge').hide();
                    $('#host_desc_torrent').show();
                    $('#torrent_verify_cert_option').hide();
                    $('#torrent_verify_deluge').hide();
                    $('#torrent_verify_rtorrent').hide();
                    $('#torrent_auth_type_option').hide();
                    $('#torrent_path_option').show();
                    $('#torrent_path_option').find('.fileBrowser').show();
                    $('#torrent_seed_time_option').hide();
                    $('#torrent_high_bandwidth_option').hide();
                    $('#torrent_label_option').show();
                    $('#torrent_label_anime_option').show();
                    $('#path_synology').hide();
                    $('#torrent_paused_option').show();
                    $('#torrent_rpcurl_option').hide();

                    if (selectedProvider.toLowerCase() === 'utorrent') {
                        client = 'uTorrent';
                        $('#torrent_path_option').hide();
                        $('#torrent_seed_time_label').text('Minimum seeding time is');
                        $('#torrent_seed_time_option').show();
                        $('#host_desc_torrent').text('URL to your uTorrent client (e.g. http://localhost:8000)');
                    } else if (selectedProvider.toLowerCase() === 'transmission'){
                        client = 'Transmission';
                        $('#torrent_seed_time_label').text('Stop seeding when inactive for');
                        $('#torrent_seed_time_option').show();
                        $('#torrent_high_bandwidth_option').show();
                        $('#torrent_label_option').hide();
                        $('#torrent_label_anime_option').hide();
                        $('#torrent_rpcurl_option').show();
                        $('#host_desc_torrent').text('URL to your Transmission client (e.g. http://localhost:9091)');
                    } else if (selectedProvider.toLowerCase() === 'deluge'){
                        client = 'Deluge';
                        $('#torrent_verify_cert_option').show();
                        $('#torrent_verify_deluge').show();
                        $('#torrent_verify_rtorrent').hide();
                        $('#label_warning_deluge').show();
                        $('#label_anime_warning_deluge').show();
                        $('#torrent_username_option').hide();
                        $('#torrent_username').prop('value', '');
                        $('#host_desc_torrent').text('URL to your Deluge client (e.g. http://localhost:8112)');
                    } else if (selectedProvider.toLowerCase() === 'deluged'){
                        client = 'Deluge';
                        $('#torrent_verify_cert_option').hide();
                        $('#torrent_verify_deluge').hide();
                        $('#torrent_verify_rtorrent').hide();
                        $('#label_warning_deluge').show();
                        $('#label_anime_warning_deluge').show();
                        $('#torrent_username_option').show();
                        $('#host_desc_torrent').text('IP or Hostname of your Deluge Daemon (e.g. scgi://localhost:58846)');
                    } else if (selectedProvider.toLowerCase() === 'download_station'){
                        client = 'Synology DS';
                        $('#torrent_label_option').hide();
                        $('#torrent_label_anime_option').hide();
                        $('#torrent_paused_option').hide();
                        $('#torrent_path_option').find('.fileBrowser').hide();
                        $('#host_desc_torrent').text('URL to your Synology DS client (e.g. http://localhost:5000)');
                        $('#path_synology').show();
                    } else if (selectedProvider.toLowerCase() === 'rtorrent'){
                        client = 'rTorrent';
                        $('#torrent_paused_option').hide();
                        $('#host_desc_torrent').text('URL to your rTorrent client (e.g. scgi://localhost:5000 <br> or https://localhost/rutorrent/plugins/httprpc/action.php)');
                        $('#torrent_verify_cert_option').show();
                        $('#torrent_verify_deluge').hide();
                        $('#torrent_verify_rtorrent').show();
                        $('#torrent_auth_type_option').show();
                    } else if (selectedProvider.toLowerCase() === 'qbittorrent'){
                        client = 'qbittorrent';
                        $('#torrent_path_option').hide();
                        $('#label_warning_qbittorrent').show();
                        $('#label_anime_warning_qbittorrent').show();
                        $('#host_desc_torrent').text('URL to your qbittorrent client (e.g. http://localhost:8080)');
                    } else if (selectedProvider.toLowerCase() === 'mlnet'){
                        client = 'mlnet';
                        $('#torrent_path_option').hide();
                        $('#torrent_label_option').hide();
                        $('#torrent_verify_cert_option').hide();
                        $('#torrent_verify_deluge').hide();
                        $('#torrent_verify_rtorrent').hide();
                        $('#torrent_label_anime_option').hide();
                        $('#torrent_paused_option').hide();
                        $('#host_desc_torrent').text('URL to your MLDonkey (e.g. http://localhost:4080)');
                    }
                    $('#host_title').text(client + host);
                    $('#username_title').text(client + username);
                    $('#password_title').text(client + password);
                    $('#torrent_client').text(client);
                    $('#rpcurl_title').text(client + rpcurl);
                    optionPanel = '#options_torrent_clients';
                }
                $(optionPanel).show();
            };

            $('#torrent_host').on('input', function(){
                if($('#torrent_method :selected').val().toLowerCase() === 'rtorrent') {
                    var hostname = $('#torrent_host').val();
                    var isMatch = hostname.substr(0, 7) === "scgi://";

                    if(isMatch) {
                        $('#torrent_username_option').hide();
                        $('#torrent_username').prop('value', '');
                        $('#torrent_password_option').hide();
                        $('#torrent_password').prop('value', '');
                        $('#torrent_auth_type_option').hide();
                        $("#torrent_auth_type option[value=none]").attr('selected', 'selected');
                    } else {
                        $('#torrent_username_option').show();
                        $('#torrent_password_option').show();
                        $('#torrent_auth_type_option').show();
                    }
                }
            });

            $('#nzb_method').on('change', $(this).nzbMethodHandler);

            $(this).nzbMethodHandler();

            $('#testSABnzbd').on('click', function(){
                var sab = {};
                $('#testSABnzbd_result').html(loading);
                sab.host = $('#sab_host').val();
                sab.username = $('#sab_username').val();
                sab.password = $('#sab_password').val();
                sab.apiKey = $('#sab_apikey').val();

                $.get(srRoot + '/home/testSABnzbd', {
                    'host': sab.host,
                    'username': sab.username,
                    'password': sab.password,
                    'apikey': sab.apiKey
                }, function(data){
                    $('#testSABnzbd_result').html(data);
                });
            });

            $('#torrent_method').on('change', $.torrentMethodHandler);

            $.torrentMethodHandler();

            $('#test_torrent').on('click', function(){
                var torrent = {};
                $('#test_torrent_result').html(loading);
                torrent.method = $('#torrent_method :selected').val();
                torrent.host = $('#torrent_host').val();
                torrent.username = $('#torrent_username').val();
                torrent.password = $('#torrent_password').val();

                $.get(srRoot + '/home/testTorrent', {
                    'torrent_method': torrent.method,
                    'host': torrent.host,
                    'username': torrent.username,
                    'password': torrent.password
                }, function(data){
                    $('#test_torrent_result').html(data);
                });
            });
        },
        subtitles: function() {
            $.fn.showHideServices = function() {
                $('.serviceDiv').each(function(){
                    var serviceName = $(this).attr('id');
                    var selectedService = $('#editAService :selected').val();

                    if (selectedService+'Div' === serviceName){
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            };

            $.fn.addService = function(id, name, url, key, isDefault, showService) {
                if (url.match('/$') === null) { url = url + '/'; }

                if ($('#service_order_list > #'+id).length === 0 && showService !== false) {
                    var toAdd = '<li class="ui-state-default" id="' + id + '"> <input type="checkbox" id="enable_' + id + '" class="service_enabler" CHECKED> <a href="' + anonURL + url + '" class="imgLink" target="_new"><img src="' + srRoot + '/images/services/newznab.gif" alt="' + name + '" width="16" height="16"></a> ' + name + '</li>';

                    $('#service_order_list').append(toAdd);
                    $('#service_order_list').sortable("refresh");
                }
            };

            $.fn.deleteService = function(id) {
                $('#service_order_list > #'+id).remove();
            };

            $.fn.refreshServiceList = function() {
                var idArr = $("#service_order_list").sortable('toArray');
                var finalArr = [];
                $.each(idArr, function(key, val) {
                    var checked = + $('#enable_'+val).prop('checked') ? '1' : '0';
                    finalArr.push(val + ':' + checked);
                });
                $("#service_order").val(finalArr.join(' '));
            };

            $('#editAService').on('change', function(){
                $(this).showHideServices();
            });

            $('.service_enabler').on('click', function(){
                $(this).refreshServiceList();
            });

            // initialization stuff
            $(this).showHideServices();

            $("#service_order_list").sortable({
                placeholder: 'ui-state-highlight',
                update: function() {
                    $(this).refreshServiceList();
                },
                create: function() {
                    $(this).refreshServiceList();
                }
            });

            $("#service_order_list").disableSelection();
        },
        providers: function() {
            // @TODO This function need to be filled with ConfigProviders.js but can't be as we've got scope issues currently.
            console.log('This function need to be filled with ConfigProviders.js but can\'t be as we\'ve got scope issues currently.');
        }
    },
    home: {
        init: function(){

        },
        index: function(){
            // Resets the tables sorting, needed as we only use a single call for both tables in tablesorter
            $('.resetsorting').on('click', function(){
                $('table').trigger('filterReset');
            });

            // Handle filtering in the poster layout
            $('#filterShowName').on('input', _.debounce(function() {
                $('.show-grid').isotope({
                    filter: function () {
                      var name = $(this).attr('data-name').toLowerCase();
                      return name.indexOf($('#filterShowName').val().toLowerCase()) > -1;
                    }
                });
            }, 500));

            function resizePosters(newSize) {
                var fontSize, logoWidth, borderRadius, borderWidth;
                if (newSize < 125) { // small
                    borderRadius = 3;
                    borderWidth = 4;
                } else if (newSize < 175) { // medium
                    fontSize = 9;
                    logoWidth = 40;
                    borderRadius = 4;
                    borderWidth = 5;
                } else { // large
                    fontSize = 11;
                    logoWidth = 50;
                    borderRadius = 6;
                    borderWidth = 6;
                }

                // If there's a poster popup, remove it before resizing
                $('#posterPopup').remove();

                if (fontSize === undefined) {
                    $('.show-details').hide();
                } else {
                    $('.show-details').show();
                    $('.show-dlstats, .show-quality').css('fontSize', fontSize);
                    $('.show-network-image').css('width', logoWidth);
                }

                $('.show-container').css({
                    width: newSize,
                    borderWidth: borderWidth,
                    borderRadius: borderRadius
                });
            }

            var posterSize;
            if (typeof(Storage) !== 'undefined') {
                posterSize = parseInt(localStorage.getItem('posterSize'));
            }
            if (typeof(posterSize) !== 'number' || isNaN(posterSize)) {
                posterSize = 188;
            }
            resizePosters(posterSize);

            $('#posterSizeSlider').slider({
                min: 75,
                max: 250,
                value: posterSize,
                change: function (e, ui) {
                    if (typeof(Storage) !== 'undefined') {
                        localStorage.setItem('posterSize', ui.value);
                    }
                    resizePosters(ui.value);
                    $('.show-grid').isotope('layout');
                }
            });

            // This needs to be refined to work a little faster.
            $('.progressbar').each(function(){
                var percentage = $(this).data('progress-percentage');
                var classToAdd = percentage === 100 ? 100 : percentage > 80 ? 80 : percentage > 60 ? 60 : percentage > 40 ? 40 : 20;
                $(this).progressbar({ value:  percentage });
                if($(this).data('progress-text')) {
                    $(this).append('<div class="progressbarText" title="' + $(this).data('progress-tip') + '">' + $(this).data('progress-text') + '</div>');
                }
                $(this).find('.ui-progressbar-value').addClass('progress-' + classToAdd);
            });

            $("img#network").on('error', function(){
                $(this).parent().text($(this).attr('alt'));
                $(this).remove();
            });

            $("#showListTableShows:has(tbody tr), #showListTableAnime:has(tbody tr)").tablesorter({
                sortList: [[7,1],[2,0]],
                textExtraction: {
                    0: function(node) { return $(node).find('time').attr('datetime'); },
                    1: function(node) { return $(node).find('time').attr('datetime'); },
                    3: function(node) { return $(node).find("span").prop("title").toLowerCase(); },
                    4: function(node) { return $(node).find("span").text().toLowerCase(); },
                    5: function(node) { return $(node).find("span:first").text(); },
                    6: function(node) { return $(node).data('show-size'); },
                    7: function(node) { return $(node).find("img").attr("alt"); }
                },
                widgets: ['saveSort', 'zebra', 'stickyHeaders', 'filter', 'columnSelector'],
                headers: {
                    0: { sorter: 'realISODate' },
                    1: { sorter: 'realISODate' },
                    2: { sorter: 'loadingNames' },
                    4: { sorter: 'quality' },
                    5: { sorter: 'eps' },
                    6: { sorter: 'digit' },
                    7: { filter: 'parsed' }
                },
                widgetOptions: {
                    'filter_columnFilters': true,
                    'filter_hideFilters': true,
                    // 'filter_saveFilters': true,
                    filter_functions: { // jshint ignore:line
                        5: function(e, n, f) {
                            var test = false;
                            var pct = Math.floor((n % 1) * 1000);
                            if (f === '') {
                                test = true;
                            } else {
                                var result = f.match(/(<|<=|>=|>)\s+(\d+)/i);
                                if (result) {
                                    if (result[1] === "<") {
                                        if (pct < parseInt(result[2])) {
                                            test = true;
                                        }
                                    } else if (result[1] === "<=") {
                                        if (pct <= parseInt(result[2])) {
                                            test = true;
                                        }
                                    } else if (result[1] === ">=") {
                                        if (pct >= parseInt(result[2])) {
                                            test = true;
                                        }
                                    } else if (result[1] === ">") {
                                        if (pct > parseInt(result[2])) {
                                            test = true;
                                        }
                                    }
                                }

                                result = f.match(/(\d+)\s(-|to)\s+(\d+)/i);
                                if (result) {
                                    if ((result[2] === "-") || (result[2] === "to")) {
                                        if ((pct >= parseInt(result[1])) && (pct <= parseInt(result[3]))) {
                                            test = true;
                                        }
                                    }
                                }

                                result = f.match(/(=)?\s?(\d+)\s?(=)?/i);
                                if (result) {
                                    if ((result[1] === "=") || (result[3] === "=")) {
                                        if (parseInt(result[2]) === pct) {
                                            test = true;
                                        }
                                    }
                                }

                                if (!isNaN(parseFloat(f)) && isFinite(f)) {
                                    if (parseInt(f) === pct) {
                                        test = true;
                                    }
                                }
                            }
                            return test;
                        }
                    },
                    'columnSelector_mediaquery': false
                },
                sortStable: true,
                sortAppend: [[2,0]]
            });

            $('.show-grid').imagesLoaded(function () {
                $('.loading-spinner').hide();
                $('.show-grid').show().isotope({
                    itemSelector: '.show-container',
                    sortBy : getMeta('sickbeard.POSTER_SORTBY'),
                    sortAscending: getMeta('sickbeard.POSTER_SORTDIR'),
                    layoutMode: 'masonry',
                    masonry: {
                        isFitWidth: true
                    },
                    getSortData: {
                        name: function (itemElem) {
                            var name = $(itemElem).attr('data-name') || '';
                            return (metaToBool('sickbeard.SORT_ARTICLE') ? name : name.replace(/^((?:The|A|An)\s)/i, '')).toLowerCase();
                        },
                        network: '[data-network]',
                        date: function (itemElem) {
                            var date = $(itemElem).attr('data-date');
                            return date.length && parseInt(date, 10) || Number.POSITIVE_INFINITY;
                        },
                        progress: function (itemElem) {
                            var progress = $(itemElem).attr('data-progress');
                            return progress.length && parseInt(progress, 10) || Number.NEGATIVE_INFINITY;
                        }
                    }
                });

                // When posters are small enough to not display the .show-details
                // table, display a larger poster when hovering.
                var posterHoverTimer = null;
                $('.show-container').on('mouseenter', function () {
                    var poster = $(this);
                    if (poster.find('.show-details').css('display') !== 'none') {
                        return;
                    }
                    posterHoverTimer = setTimeout(function () {
                        posterHoverTimer = null;
                        $('#posterPopup').remove();
                        var popup = poster.clone().attr({
                            id: 'posterPopup'
                        });
                        var origLeft = poster.offset().left;
                        var origTop  = poster.offset().top;
                        popup.css({
                            position: 'absolute',
                            margin: 0,
                            top: origTop,
                            left: origLeft
                        });
                        popup.find('.show-details').show();
                        popup.on('mouseleave', function () {
                            $(this).remove();
                        });
                        popup.zIndex(9999);
                        popup.appendTo('body');

                        var height = 438, width = 250;
                        var newTop = (origTop+poster.height()/2)-(height/2);
                        var newLeft = (origLeft+poster.width()/2)-(width/2);

                        // Make sure the popup isn't outside the viewport
                        var margin = 5;
                        var scrollTop = $(window).scrollTop();
                        var scrollLeft = $(window).scrollLeft();
                        var scrollBottom = scrollTop + $(window).innerHeight();
                        var scrollRight = scrollLeft + $(window).innerWidth();
                        if (newTop < scrollTop+margin) { newTop = scrollTop+margin; }
                        if (newLeft < scrollLeft+margin) { newLeft = scrollLeft+margin; }
                        if (newTop+height+margin > scrollBottom) { newTop = scrollBottom-height-margin; }
                        if (newLeft+width+margin > scrollRight) { newLeft = scrollRight-width-margin; }

                        popup.animate({
                            top: newTop,
                            left: newLeft,
                            width: 250,
                            height: 438
                        });
                    }, 300);
                }).on('mouseleave', function () {
                    if (posterHoverTimer !== null) {
                        clearTimeout(posterHoverTimer);
                    }
                });
            });

            $('#postersort').on('change', function(){
                $('.show-grid').isotope({sortBy: $(this).val()});
                $.get($(this).find('option[value=' + $(this).val() +']').attr('data-sort'));
            });

            $('#postersortdirection').on('change', function(){
                $('.show-grid').isotope({sortAscending: ($(this).val() === 'true')});
                $.get($(this).find('option[value=' + $(this).val() +']').attr('data-sort'));
            });

            $('#popover').popover({
                placement: 'bottom',
                html: true, // required if content has HTML
                content: '<div id="popover-target"></div>'
            }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
                // call this function to copy the column selection code into the popover
                $.tablesorter.columnSelector.attachTo( $('#showListTableShows'), '#popover-target');
                if(metaToBool('sickbeard.ANIME_SPLIT_HOME')){
                    $.tablesorter.columnSelector.attachTo( $('#showListTableAnime'), '#popover-target');
                }

            });
        },
        displayShow: function() {
            $('#srRoot').ajaxEpSearch({'colorRow': true});

            $('#srRoot').ajaxEpSubtitlesSearch();

            $('#seasonJump').on('change', function(){
                var id = $('#seasonJump option:selected').val();
                if (id && id !== 'jump') {
                    var season = $('#seasonJump option:selected').data('season');
                    $('html,body').animate({scrollTop: $('[name ="' + id.substring(1) + '"]').offset().top - 50}, 'slow');
                    $('#collapseSeason-' + season).collapse('show');
                    location.hash = id;
                }
                $(this).val('jump');
            });

            $("#prevShow").on('click', function(){
                $('#pickShow option:selected').prev('option').prop('selected', 'selected');
                $("#pickShow").change();
            });

            $("#nextShow").on('click', function(){
                $('#pickShow option:selected').next('option').prop('selected', 'selected');
                $("#pickShow").change();
            });

            $('#changeStatus').on('click', function(){
                var srRoot = $('#srRoot').val();
                var epArr = [];

                $('.epCheck').each(function () {
                    if (this.checked === true) {
                        epArr.push($(this).attr('id'));
                    }
                });

                if (epArr.length === 0) { return false; }

                window.location.href = srRoot + '/home/setStatus?show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|') + '&status=' + $('#statusSelect').val();
            });

            $('.seasonCheck').on('click', function(){
                var seasCheck = this;
                var seasNo = $(seasCheck).attr('id');

                $('#collapseSeason-' + seasNo).collapse('show');
                $('.epCheck:visible').each(function () {
                    var epParts = $(this).attr('id').split('x');
                    if (epParts[0] === seasNo) {
                        this.checked = seasCheck.checked;
                    }
                });
            });

            var lastCheck = null;
            $('.epCheck').on('click', function (event) {

                if (!lastCheck || !event.shiftKey) {
                    lastCheck = this;
                    return;
                }

                var check = this;
                var found = 0;

                $('.epCheck').each(function() {
                    switch (found) {
                        case 2:
                            return false;
                        case 1:
                            this.checked = lastCheck.checked;
                    }

                    if (this === check || this === lastCheck) {
                        found++;
                    }
                });
            });

            // selects all visible episode checkboxes.
            $('.seriesCheck').on('click', function () {
                $('.epCheck:visible').each(function () {
                    this.checked = true;
                });
                $('.seasonCheck:visible').each(function () {
                    this.checked = true;
                });
            });

            // clears all visible episode checkboxes and the season selectors
            $('.clearAll').on('click', function () {
                $('.epCheck:visible').each(function () {
                    this.checked = false;
                });
                $('.seasonCheck:visible').each(function () {
                    this.checked = false;
                });
            });

            // handle the show selection dropbox
            $('#pickShow').on('change', function () {
                var srRoot = $('#srRoot').val();
                var val = $(this).val();
                if (val === 0) {
                    return;
                }
                window.location.href = srRoot + '/home/displayShow?show=' + val;
            });

            // show/hide different types of rows when the checkboxes are changed
            $("#checkboxControls input").on('change', function () {
                var whichClass = $(this).attr('id');
                $(this).showHideRows(whichClass);
            });

            // initially show/hide all the rows according to the checkboxes
            $("#checkboxControls input").each(function() {
                var status = $(this).prop('checked');
                $("tr." + $(this).attr('id')).each(function() {
                    if(status) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            });

            $.fn.showHideRows = function(whichClass) {
                var status = $('#checkboxControls > input, #' + whichClass).prop('checked');
                $("tr." + whichClass).each(function() {
                    if (status) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });

                // hide season headers with no episodes under them
                $('tr.seasonheader').each(function () {
                    var numRows = 0;
                    var seasonNo = $(this).attr('id');
                    $('tr.' + seasonNo + ' :visible').each(function () {
                        numRows++;
                    });
                    if (numRows === 0) {
                        $(this).hide();
                        $('#' + seasonNo + '-cols').hide();
                    } else {
                        $(this).show();
                        $('#' + seasonNo + '-cols').show();
                    }
                });
            };

            function setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode) {
                var srRoot = $('#srRoot').val();
                var showId = $('#showID').val();
                var indexer = $('#indexer').val();

                if (sceneSeason === '') { sceneSeason = null; }
                if (sceneEpisode === '') { sceneEpisode = null; }

                $.getJSON(srRoot + '/home/setSceneNumbering',{
                    'show': showId,
                    'indexer': indexer,
                    'forSeason': forSeason,
                    'forEpisode': forEpisode,
                    'sceneSeason': sceneSeason,
                    'sceneEpisode': sceneEpisode
                }, function(data) {
                    // Set the values we get back
                    if (data.sceneSeason === null || data.sceneEpisode === null) {
                        $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val('');
                    } else {
                        $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val(data.sceneSeason + 'x' + data.sceneEpisode);
                    }
                    if (!data.success) {
                        if (data.errorMessage) {
                            alert(data.errorMessage);
                        } else {
                            alert('Update failed.');
                        }
                    }
                });
            }

            function setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute) {
                var srRoot = $('#srRoot').val();
                var showId = $('#showID').val();
                var indexer = $('#indexer').val();

                if (sceneAbsolute === '') { sceneAbsolute = null; }

                $.getJSON(srRoot + '/home/setSceneNumbering', {
                    'show': showId,
                    'indexer': indexer,
                    'forAbsolute': forAbsolute,
                    'sceneAbsolute': sceneAbsolute
                },
                function(data) {
                    // Set the values we get back
                    if (data.sceneAbsolute === null) {
                        $('#sceneAbsolute_' + showId + '_' + forAbsolute).val('');
                    } else {
                        $('#sceneAbsolute_' + showId + '_' + forAbsolute).val(data.sceneAbsolute);
                    }
                    if (!data.success) {
                        if (data.errorMessage) {
                            alert(data.errorMessage);
                        } else {
                            alert('Update failed.');
                        }
                    }
                });
            }

            function setInputValidInvalid(valid, el) {
                if (valid) {
                    $(el).css({'background-color': '#90EE90','color': '#FFF', 'font-weight': 'bold'}); //green
                    return true;
                } else {
                    $(el).css({'background-color': '#FF0000','color': '#FFF!important', 'font-weight': 'bold'}); //red
                    return false;
                }
            }

            $('.sceneSeasonXEpisode').on('change', function() {
                // Strip non-numeric characters
                $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
                var forSeason = $(this).attr('data-for-season');
                var forEpisode = $(this).attr('data-for-episode');
                var m = $(this).val().match(/^(\d+)x(\d+)$/i);
                var onlyEpisode = $(this).val().match(/^(\d+)$/i);
                var sceneSeason = null, sceneEpisode = null;
                var isValid = false;
                if (m) {
                    sceneSeason = m[1];
                    sceneEpisode = m[2];
                    isValid = setInputValidInvalid(true, $(this));
                } else if (onlyEpisode) {
                    // For example when '5' is filled in instead of '1x5', asume it's the first season
                    sceneSeason = forSeason;
                    sceneEpisode = onlyEpisode[1];
                    isValid = setInputValidInvalid(true, $(this));
                } else {
                    isValid = setInputValidInvalid(false, $(this));
                }
                // Only perform the request when there is a valid input
                if (isValid){
                    setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode);
                }
            });

            $('.sceneAbsolute').on('change', function() {
                // Strip non-numeric characters
                $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
                var forAbsolute = $(this).attr('data-for-absolute');

                var m = $(this).val().match(/^(\d{1,3})$/i);
                var sceneAbsolute = null;
                if (m) {
                    sceneAbsolute = m[1];
                }
                setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute);
            });

            $('.addQTip').each(function () {
                $(this).css({'cursor':'help', 'text-shadow':'0px 0px 0.5px #666'});
                $(this).qtip({
                    show: {solo:true},
                    position: {viewport:$(window), my:'left center', adjust:{ y: -10, x: 2 }},
                    style: {tip:{corner:true, method:'polygon'}, classes:'qtip-rounded qtip-shadow ui-tooltip-sb'}
                });
            });
            $.fn.generateStars = function() {
                return this.each(function(i,e){
                    $(e).html($('<span/>').width($(e).text()*12));
                });
            };

            $('.imdbstars').generateStars();

            $("#showTable, #animeTable").tablesorter({
                widgets: ['saveSort', 'stickyHeaders', 'columnSelector'],
                widgetOptions : {
                    columnSelector_saveColumns: true, // jshint ignore:line
                    columnSelector_layout : '<br><label><input type="checkbox">{name}</label>', // jshint ignore:line
                    columnSelector_mediaquery: false, // jshint ignore:line
                    columnSelector_cssChecked : 'checked' // jshint ignore:line
                }
            });

            $('#popover').popover({
                placement: 'bottom',
                html: true, // required if content has HTML
                content: '<div id="popover-target"></div>'
            })
            // bootstrap popover event triggered when the popover opens
            .on('shown.bs.popover', function (){
                $.tablesorter.columnSelector.attachTo($("#showTable, #animeTable"), '#popover-target');
            });

            // Moved and rewritten this from displayShow. This changes the button when clicked for collapsing/expanding the
            // Season to Show Episodes or Hide Episodes.
            $(function() {
                $('.collapse.toggle').on('hide.bs.collapse', function () {
                    var reg = /collapseSeason-([0-9]+)/g;
                    var result = reg.exec(this.id);
                    $('#showseason-' + result[1]).text('Show Episodes');
                });
                $('.collapse.toggle').on('show.bs.collapse', function () {
                    var reg = /collapseSeason-([0-9]+)/g;
                    var result = reg.exec(this.id);
                    $('#showseason-' + result[1]).text('Hide Episodes');
                });
            });

        },
        postProcess: function() {
            $('#episodeDir').fileBrowser({ title: 'Select Unprocessed Episode Folder', key: 'postprocessPath' });
        },
        status: function() {
            $("#schedulerStatusTable").tablesorter({
                widgets: ['saveSort', 'zebra'],
                textExtraction: {
                    5: function(node) { return $(node).data('seconds'); },
                    6: function(node) { return $(node).data('seconds'); }
                },
                headers: {
                    5: { sorter: 'digit' },
                    6: { sorter: 'digit' }
                }
            });
            $("#queueStatusTable").tablesorter({
                widgets: ['saveSort', 'zebra'],
                sortList: [[3,0], [4,0], [2,1]]
            });
        },
        restart: function(){
            var currentPid = srPID;
            var checkIsAlive = setInterval(function(){
                $.get(srRoot + '/home/is_alive/', function(data) {
                    if (data.msg.toLowerCase() === 'nope') {
                        // if it's still initializing then just wait and try again
                        $('#restart_message').show();
                    } else {
                        // if this is before we've even shut down then just try again later
                        if (currentPid === '' || data.msg === currentPid) {
                            $('#shut_down_loading').hide();
                            $('#shut_down_success').show();
                            currentPid = data.msg;
                        } else {
                            clearInterval(checkIsAlive);
                            $('#restart_loading').hide();
                            $('#restart_success').show();
                            $('#refresh_message').show();
                            setTimeout(function(){
                                window.location = srRoot + '/' + srDefaultPage + '/';
                            }, 5000);
                        }
                    }
                }, 'jsonp');
            }, 100);
        }
    },
    manage: {
        init: function() {
            $.makeEpisodeRow = function(indexerId, season, episode, name, checked) {
                var row = '';
                row += ' <tr class="' + $('#row_class').val() + ' show-' + indexerId + '">';
                row += '  <td class="tableleft" align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
                row += '  <td>' + season + 'x' + episode + '</td>';
                row += '  <td class="tableright" style="width: 100%">' + name + '</td>';
                row += ' </tr>';

                return row;
            };

            $.makeSubtitleRow = function(indexerId, season, episode, name, subtitles, checked) {
                var row = '';
                row += '<tr class="good show-' + indexerId + '">';
                row += '<td align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
                row += '<td style="width: 2%;">' + season + 'x' + episode + '</td>';
                if (subtitles.length > 0) {
                    row += '<td style="width: 8%;">';
                    subtitles = subtitles.split(',');
                    for (var i in subtitles) {
                        if (subtitles.hasOwnProperty(i)) {
                            row += '<img src="' + srRoot + '/images/subtitles/flags/' + subtitles[i] + '.png" width="16" height="11" alt="' + subtitles[i] + '" />&nbsp;';
                        }
                    }
                    row += '</td>';
                } else {
                    row += '<td style="width: 8%;">None</td>';
                }
                row += '<td>' + name + '</td>';
                row += '</tr>';

                return row;
            };
        },
        index: function() {
            $('.resetsorting').on('click', function(){
                $('table').trigger('filterReset');
            });

            $("#massUpdateTable:has(tbody tr)").tablesorter({
                sortList: [[1,0]],
                textExtraction: {
                    2: function(node) { return $(node).find("span").text().toLowerCase(); },
                    3: function(node) { return $(node).find("img").attr("alt"); },
                    4: function(node) { return $(node).find("img").attr("alt"); },
                    5: function(node) { return $(node).find("img").attr("alt"); },
                    6: function(node) { return $(node).find("img").attr("alt"); },
                    7: function(node) { return $(node).find("img").attr("alt"); },
                    8: function(node) { return $(node).find("img").attr("alt"); },
                    9: function(node) { return $(node).find("img").attr("alt"); },
                },
                widgets: ['zebra', 'filter', 'columnSelector'],
                headers: {
                    0: { sorter: false, filter: false},
                    1: { sorter: 'showNames'},
                    2: { sorter: 'quality'},
                    3: { sorter: 'sports'},
                    4: { sorter: 'scene'},
                    5: { sorter: 'anime'},
                    6: { sorter: 'flatfold'},
                    7: { sorter: 'paused'},
                    8: { sorter: 'subtitle'},
                    9: { sorter: 'default_ep_status'},
                    10: { sorter: 'status'},
                    11: { sorter: false},
                    12: { sorter: false},
                    13: { sorter: false},
                    14: { sorter: false},
                    15: { sorter: false},
                    16: { sorter: false}
                },
                widgetOptions: {
                    'columnSelector_mediaquery': false
                }
            });
            $('#popover').popover({
                placement: 'bottom',
                html: true, // required if content has HTML
                content: '<div id="popover-target"></div>'
            }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
                // call this function to copy the column selection code into the popover
                $.tablesorter.columnSelector.attachTo( $('#massUpdateTable'), '#popover-target');
            });
        },
        backlogOverview: function() {
            $('#pickShow').on('change', function(){
                var id = $(this).val();
                if (id) {
                    $('html,body').animate({scrollTop: $('#show-' + id).offset().top -25},'slow');
                }
            });
        },
        failedDownloads: function() {
            $("#failedTable:has(tbody tr)").tablesorter({
                widgets: ['zebra'],
                sortList: [[0,0]],
                headers: { 3: { sorter: false } }
            });
            $('#limit').on('change', function(){
                window.location.href = srRoot + '/manage/failedDownloads/?limit=' + $(this).val();
            });

            $('#submitMassRemove').on('click', function(){
                var removeArr = [];

                $('.removeCheck').each(function() {
                    if (this.checked === true) {
                        removeArr.push($(this).attr('id').split('-')[1]);
                    }
                });

                if (removeArr.length === 0) { return false; }

                window.location.href = srRoot + '/manage/failedDownloads?toRemove='+removeArr.join('|');
            });

            if($('.removeCheck').length){
                $('.removeCheck').each(function(name) {
                    var lastCheck = null;
                    $(name).click(function(event) {
                        if(!lastCheck || !event.shiftKey) {
                            lastCheck = this;
                            return;
                        }

                        var check = this;
                        var found = 0;

                        $(name+':visible').each(function() {
                            switch (found) {
                                case 2: return false;
                                case 1: this.checked = lastCheck.checked;
                            }

                            if (this === check || this === lastCheck) { found++; }
                        });
                    });
                });
            }
        },
        massEdit: function() {
            $('#location').fileBrowser({ title: 'Select Show Location' });
        },
        episodeStatuses: function() {
            $('.allCheck').on('click', function(){
                var indexerId = $(this).attr('id').split('-')[1];
                $('.' + indexerId + '-epcheck').prop('checked', $(this).prop('checked'));
            });

            $('.get_more_eps').on('click', function(){
                var curIndexerId = $(this).attr('id');
                var checked = $('#allCheck-' + curIndexerId).prop('checked');
                var lastRow = $('tr#' + curIndexerId);
                var clicked = $(this).attr('data-clicked');
                var action = $(this).attr('value');

                if(!clicked) {
                    $.getJSON(srRoot+'/manage/showEpisodeStatuses',{
                        'indexer_id': curIndexerId,
                        whichStatus: $('#oldStatus').val()
                    }, function (data) {
                        $.each(data, function(season,eps){
                            $.each(eps, function(episode, name) {
                                lastRow.after($.makeEpisodeRow(curIndexerId, season, episode, name, checked));
                            });
                        });
                    });
                    $(this).attr('data-clicked',1);
                    $(this).prop('value', 'Collapse');
                } else {
                    if (action.toLowerCase() === 'collapse') {
                        $('table tr').filter('.show-' + curIndexerId).hide();
                        $(this).prop('value', 'Expand');
                    } else if (action.toLowerCase() === 'expand') {
                        $('table tr').filter('.show-' + curIndexerId).show();
                        $(this).prop('value', 'Collapse');
                    }
                }
            });

            // selects all visible episode checkboxes.
            $('.selectAllShows').on('click', function(){
                $('.allCheck').each(function(){
                    this.checked = true;
                });
                $('input[class*="-epcheck"]').each(function(){
                    this.checked = true;
                });
            });

            // clears all visible episode checkboxes and the season selectors
            $('.unselectAllShows').on('click', function(){
                $('.allCheck').each(function(){
                    this.checked = false;
                });
                $('input[class*="-epcheck"]').each(function(){
                    this.checked = false;
                });
            });
        },
        subtitleMissed: function() {
            $('.allCheck').on('click', function(){
                var indexerId = $(this).attr('id').split('-')[1];
                $('.'+indexerId+'-epcheck').prop('checked', $(this).prop('checked'));
            });

            $('.get_more_eps').on('click', function(){
                var indexerId = $(this).attr('id');
                var checked = $('#allCheck-'+indexerId).prop('checked');
                var lastRow = $('tr#'+indexerId);
                var clicked = $(this).attr('data-clicked');
                var action = $(this).attr('value');

                if (!clicked) {
                    $.getJSON(srRoot + '/manage/showSubtitleMissed', {
                        'indexer_id': indexerId,
                        'whichSubs': $('#selectSubLang').val()
                    }, function(data) {
                        $.each(data, function(season, eps) {
                            $.each(eps, function(episode, data) {
                                lastRow.after($.makeSubtitleRow(indexerId, season, episode, data.name, data.subtitles, checked));
                            });
                        });
                    });
                    $(this).attr('data-clicked', 1);
                    $(this).prop('value', 'Collapse');
                } else {
                    if (action === 'Collapse') {
                        $('table tr').filter('.show-' + indexerId).hide();
                        $(this).prop('value', 'Expand');
                    } else if (action === 'Expand') {
                        $('table tr').filter('.show-' + indexerId).show();
                        $(this).prop('value', 'Collapse');
                    }
                }
            });

            // @TODO these two should be able to be merged by using a generic class for the selector

            // selects all visible episode checkboxes.
            $('.selectAllShows').on('click', function(){
                $('.allCheck').each(function(){
                    this.checked = true;
                });
                $('input[class*="-epcheck"]').each(function(){
                    this.checked = true;
                });
            });

            // clears all visible episode checkboxes and the season selectors
            $('.unselectAllShows').on('click', function(){
                $('.allCheck').each(function(){
                    this.checked = false;
                });
                $('input[class*="-epcheck"]').each(function(){
                    this.checked = false;
                });
            });
        }
    },
    history: {
        init: function() {

        },
        index: function() {
            $("#historyTable:has(tbody tr)").tablesorter({
                widgets: ['zebra', 'filter'],
                sortList: [[0,1]],
                textExtraction: (function(){
                    if(isMeta('sickbeard.HISTORY_LAYOUT', ['detailed'])){
                        return {
                            0: function(node) { return $(node).find('time').attr('datetime'); },
                            4: function(node) { return $(node).find("span").text().toLowerCase(); }
                        };
                    } else {
                        return {
                            0: function(node) { return $(node).find('time').attr('datetime'); },
                            1: function(node) { return $(node).find("span").text().toLowerCase(); },
                            2: function(node) { return $(node).attr("provider").toLowerCase(); },
                            5: function(node) { return $(node).attr("quality").toLowerCase(); }
                        };
                    }
                }()),
                headers: (function(){
                    if(isMeta('sickbeard.HISTORY_LAYOUT', ['detailed'])){
                        return {
                            0: { sorter: 'realISODate' },
                            4: { sorter: 'quality' }
                        };
                    } else {
                        return {
                            0: { sorter: 'realISODate' },
                            4: { sorter: false },
                            5: { sorter: 'quality' }
                        };
                    }
                }())
            });

            $('#history_limit').on('change', function() {
                var url = srRoot + '/history/?limit=' + $(this).val();
                window.location.href = url;
            });
        }
    },
    errorlogs: {
        init: function() {

        },
        index: function() {

        },
        viewlogs: function() {
            $('#minLevel,#logFilter,#logSearch').on('keyup change', _.debounce(function () {
                if ($('#logSearch').val().length > 0){
                    $('#logFilter option[value="<NONE>"]').prop('selected', true);
                    $('#minLevel option[value=5]').prop('selected', true);
                }
                $('#minLevel').prop('disabled', true);
                $('#logFilter').prop('disabled', true);
                document.body.style.cursor='wait';
                var url = srRoot + '/errorlogs/viewlog/?minLevel='+$('select[name=minLevel]').val()+'&logFilter='+$('select[name=logFilter]').val()+'&logSearch='+$('#logSearch').val();
                $.get(url, function(data){
                    history.pushState('data', '', url);
                    $('pre').html($(data).find('pre').html());
                    $('#minLevel').prop('disabled', false);
                    $('#logFilter').prop('disabled', false);
                    document.body.style.cursor='default';
                });
            }, 500));
        }
    },
    schedule: {
        init: function() {

        },
        index: function() {
            if(isMeta('sickbeard.COMING_EPS_LAYOUT', ['list'])){
                var sortCodes = {'date': 0, 'show': 2, 'network': 5};
                var sort = getMeta('sickbeard.COMING_EPS_SORT');
                var sortList = (sort in sortCodes) ? [[sortCodes[sort], 0]] : [[0, 0]];

                $('#showListTable:has(tbody tr)').tablesorter({
                    widgets: ['stickyHeaders', 'filter', 'columnSelector', 'saveSort'],
                    sortList: sortList,
                    textExtraction: {
                        0: function(node) { return $(node).find('time').attr('datetime'); },
                        1: function(node) { return $(node).find('time').attr('datetime'); },
                        7: function(node) { return $(node).find('span').text().toLowerCase(); }
                    },
                    headers: {
                        0: { sorter: 'realISODate' },
                        1: { sorter: 'realISODate' },
                        2: { sorter: 'loadingNames' },
                        4: { sorter: 'loadingNames' },
                        7: { sorter: 'quality' },
                        8: { sorter: false },
                        9: { sorter: false }
                    },
                    widgetOptions: {
                        'filter_columnFilters': true,
                        'filter_hideFilters': true,
                        'filter_saveFilters': true,
                        'columnSelector_mediaquery': false
                    }
                });

                $('#srRoot').ajaxEpSearch();
            }

            if(isMeta('sickbeard.COMING_EPS_LAYOUT', ['banner', 'poster'])){
                $('#srRoot').ajaxEpSearch({'size': 16, 'loadingImage': 'loading16' + themeSpinner + '.gif'});
                $('.ep_summary').hide();
                $('.ep_summaryTrigger').click(function() {
                    $(this).next('.ep_summary').slideToggle('normal', function() {
                        $(this).prev('.ep_summaryTrigger').attr('src', function(i, src) {
                            return $(this).next('.ep_summary').is(':visible') ? src.replace('plus','minus') : src.replace('minus','plus');
                        });
                    });
                });
            }

            $('#popover').popover({
                placement: 'bottom',
                html: true, // required if content has HTML
                content: '<div id="popover-target"></div>'
            }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
                // call this function to copy the column selection code into the popover
                $.tablesorter.columnSelector.attachTo( $('#showListTable'), '#popover-target');
            });
        }
    },
    addShows: {
        init: function() {
            $('#tabs').tabs({
                collapsible: true,
                selected: (metaToBool('sickbeard.SORT_ARTICLE') ? -1 : 0)
            });

            $.initRemoteShowGrid = function(){
                // Set defaults on page load
                $('#showsort').val('original');
                $('#showsortdirection').val('asc');

                $('#showsort').on('change', function() {
                    var sortCriteria;
                    switch (this.value) {
                        case 'original':
                            sortCriteria = 'original-order';
                            break;
                        case 'rating':
                            /* randomise, else the rating_votes can already
                             * have sorted leaving this with nothing to do.
                             */
                            $('#container').isotope({sortBy: 'random'});
                            sortCriteria = 'rating';
                            break;
                        case 'rating_votes':
                            sortCriteria = ['rating', 'votes'];
                            break;
                        case 'votes':
                            sortCriteria = 'votes';
                            break;
                        default:
                            sortCriteria = 'name';
                            break;
                    }
                    $('#container').isotope({
                        sortBy: sortCriteria
                    });
                });

                $('#showsortdirection').on('change', function() {
                    $('#container').isotope({
                        sortAscending: ('asc' === this.value)
                    });
                });

                $('#container').isotope({
                    sortBy: 'original-order',
                    layoutMode: 'fitRows',
                    getSortData: {
                        name: function(itemElem) {
                            var name = $(itemElem).attr('data-name') || '';
                            return (metaToBool('sickbeard.SORT_ARTICLE') ? name : name.replace(/^((?:The|A|An)\s)/i, '')).toLowerCase();
                        },
                        rating: '[data-rating] parseInt',
                        votes: '[data-votes] parseInt',
                    }
                });
            };

            $.fn.loadRemoteShows = function(path, loadingTxt, errorTxt) {
                $(this).html('<img id="searchingAnim" src="' + srRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" />&nbsp;' + loadingTxt);
                $(this).load(srRoot + path + ' #container', function(response, status) {
                    if (status === "error") {
                        $(this).empty().html(errorTxt);
                    } else {
                        $.initRemoteShowGrid();
                    }
                });
            };
        },
        index: function() {

        },
        newShow: function() {
            function updateBlackWhiteList(showName) {
                $('#white').children().remove();
                $('#black').children().remove();
                $('#pool').children().remove();

                if ($('#anime').prop('checked')) {
                    $('#blackwhitelist').show();
                    if (showName) {
                        $.getJSON(srRoot + '/home/fetch_releasegroups', {
                            'show_name': showName
                        }, function (data) {
                            if (data.result === 'success') {
                                $.each(data.groups, function(i, group) {
                                    var option = $("<option>");
                                    option.attr("value", group.name);
                                    option.html(group.name + ' | ' + group.rating + ' | ' + group.range);
                                    option.appendTo('#pool');
                                });
                            }
                        });
                    }
                } else {
                    $('#blackwhitelist').hide();
                }
            }

            function updateSampleText() {
                // if something's selected then we have some behavior to figure out

                var showName, sepChar;
                // if they've picked a radio button then use that
                if ($('input:radio[name=whichSeries]:checked').length) {
                    showName = $('input:radio[name=whichSeries]:checked').val().split('|')[4];
                } else if ($('input:hidden[name=whichSeries]').length && $('input:hidden[name=whichSeries]').val().length) { // if we provided a show in the hidden field, use that
                    showName = $('#providedName').val();
                } else {
                    showName = '';
                }
                updateBlackWhiteList(showName);
                var sampleText = 'Adding show <b>' + showName + '</b> into <b>';

                // if we have a root dir selected, figure out the path
                if ($('#rootDirs option:selected').length) {
                    var rootDirectoryText = $('#rootDirs option:selected').val();
                    if (rootDirectoryText.indexOf('/') >= 0) {
                        sepChar = '/';
                    } else if (rootDirectoryText.indexOf('\\') >= 0) {
                        sepChar = '\\';
                    } else {
                        sepChar = '';
                    }

                    if (rootDirectoryText.substr(sampleText.length - 1) !== sepChar) {
                        rootDirectoryText += sepChar;
                    }
                    rootDirectoryText += '<i>||</i>' + sepChar;

                    sampleText += rootDirectoryText;
                } else if ($('#fullShowPath').length && $('#fullShowPath').val().length) {
                    sampleText += $('#fullShowPath').val();
                } else {
                    sampleText += 'unknown dir.';
                }

                sampleText += '</b>';

                // if we have a show name then sanitize and use it for the dir name
                if (showName.length) {
                    $.get(srRoot + '/addShows/sanitizeFileName', {name: showName}, function (data) {
                        $('#displayText').html(sampleText.replace('||', data));
                    });
                // if not then it's unknown
                } else {
                    $('#displayText').html(sampleText.replace('||', '??'));
                }

                // also toggle the add show button
                if (($("#rootDirs option:selected").length || ($('#fullShowPath').length && $('#fullShowPath').val().length)) &&
                    ($('input:radio[name=whichSeries]:checked').length) || ($('input:hidden[name=whichSeries]').length && $('input:hidden[name=whichSeries]').val().length)) {
                    $('#addShowButton').attr('disabled', false);
                } else {
                    $('#addShowButton').attr('disabled', true);
                }
            }

            var searchRequestXhr = null;
            function searchIndexers() {
                if (!$('#nameToSearch').val().length) { return; }

                if (searchRequestXhr) { searchRequestXhr.abort(); }

                var searchingFor = $('#nameToSearch').val().trim() + ' on ' + $('#providedIndexer option:selected').text() + ' in ' + $('#indexerLangSelect').val();
                $('#searchResults').empty().html('<img id="searchingAnim" src="' + srRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" /> searching ' + searchingFor + '...');

                searchRequestXhr = $.ajax({
                    url: srRoot + '/addShows/searchIndexersForShowName',
                    data: {
                        'search_term': $('#nameToSearch').val().trim(),
                        'lang': $('#indexerLangSelect').val(),
                        'indexer': $('#providedIndexer').val()},
                    timeout: parseInt($('#indexer_timeout').val(), 10) * 1000,
                    dataType: 'json',
                    error: function () {
                        $('#searchResults').empty().html('search timed out, try again or try another indexer');
                    },
                    success: function (data) {
                        var firstResult = true;
                        var resultStr = '<fieldset>\n<legend class="legendStep">Search Results:</legend>\n';
                        var checked = '';

                        if (data.results.length === 0) {
                            resultStr += '<b>No results found, try a different search.</b>';
                        } else {
                            $.each(data.results, function(index, obj) {
                                if (firstResult) {
                                    checked = ' checked';
                                    firstResult = false;
                                } else {
                                    checked = '';
                                }

                                var whichSeries = obj.join('|');

                                resultStr += '<input type="radio" id="whichSeries" name="whichSeries" value="' + whichSeries.replace(/"/g, '')  + '"' + checked + ' /> ';
                                if (data.langid && data.langid !== '') {
                                    resultStr += '<a href="' + anonURL + obj[2] + obj[3] + '&lid=' + data.langid + '" onclick=\"window.open(this.href, \'_blank\'); return false;\" ><b>' + obj[4] + '</b></a>';
                                } else {
                                    resultStr += '<a href="' + anonURL + obj[2] + obj[3] + '" onclick=\"window.open(this.href, \'_blank\'); return false;\" ><b>' + obj[4] + '</b></a>';
                                }

                                if (obj[5] !== null) {
                                    var startDate = new Date(obj[5]);
                                    var today = new Date();
                                    if (startDate > today) {
                                        resultStr += ' (will debut on ' + obj[5] + ')';
                                    } else {
                                        resultStr += ' (started on ' + obj[5] + ')';
                                    }
                                }

                                if (obj[0] !== null) {
                                    resultStr += ' [' + obj[0] + ']';
                                }

                                resultStr += '<br>';
                            });
                            resultStr += '</ul>';
                        }
                        resultStr += '</fieldset>';
                        $('#searchResults').html(resultStr);
                        updateSampleText();
                        myform.loadsection(0);
                    }
                });
            }

            $('#searchName').click(function () { searchIndexers(); });

            if ($('#nameToSearch').length && $('#nameToSearch').val().length) {
                $('#searchName').click();
            }

            $('#addShowButton').click(function () {
                // if they haven't picked a show don't let them submit
                if (!$('input:radio[name="whichSeries"]:checked').val() && !$('input:hidden[name="whichSeries"]').val().length) {
                    alert('You must choose a show to continue');
                    return false;
                }
                generateBlackWhiteList();
                $('#addShowForm').submit();
            });

            $('#skipShowButton').click(function () {
                $('#skipShow').val('1');
                $('#addShowForm').submit();
            });

            $('#qualityPreset').change(function () {
                myform.loadsection(2);
            });

            /***********************************************
            * jQuery Form to Form Wizard- (c) Dynamic Drive (www.dynamicdrive.com)
            * This notice MUST stay intact for legal use
            * Visit http://www.dynamicdrive.com/ for this script and 100s more.
            ***********************************************/

            function goToStep(num) {
                $('.step').each(function () {
                    if ($.data(this, 'section') + 1 === num) {
                        $(this).click();
                    }
                });
            }

            $('#nameToSearch').focus();

            // @TODO we need to move to real forms instead of this
            var myform = new formtowizard({ // jshint ignore:line
                formid: 'addShowForm',
                revealfx: ['slide', 500],
                oninit: function () {
                    updateSampleText();
                    if ($('input:hidden[name=whichSeries]').length && $('#fullShowPath').length) {
                        goToStep(3);
                    }
                }
            });

            $('#rootDirText').change(updateSampleText);
            $('#searchResults').on('change', '#whichSeries', updateSampleText);

            $('#nameToSearch').keyup(function(event) {
                if (event.keyCode === 13) {
                    $('#searchName').click();
                }
            });

            $('#anime').change (function() {
                updateSampleText();
                myform.loadsection(2);
            });

        },
        addExistingShow: function(){
            $('#tableDiv').on('click', '#checkAll', function() {
                var seasCheck = this;
                $('.dirCheck').each(function() {
                    this.checked = seasCheck.checked;
                });
            });

            $('#submitShowDirs').on('click', function() {
                var dirArr = [];
                $('.dirCheck').each(function() {
                    if (this.checked === true) {
                        var show = $(this).attr('id');
                        var indexer = $(this).closest('tr').find('select').val();
                        dirArr.push(encodeURIComponent(indexer + '|' + show));
                    }
                });

                if (dirArr.length === 0) {
                    return false;
                }

                var url = srRoot + '/addShows/addExistingShows?promptForSettings=' + ($('#promptForSettings').prop('checked') ? 'on' : 'off') + '&shows_to_add=' + dirArr.join('&shows_to_add=');
                if(url.length < 2083) {
                    window.location.href = url;
                } else {
                    alert("You've selected too many shows, please uncheck some and try again.");
                }
            });

            function loadContent() {
                var url = '';
                $('.dir_check').each(function(i,w) {
                    if ($(w).is(':checked')) {
                        if (url.length) {
                            url += '&';
                        }
                        url += 'rootDir=' + encodeURIComponent($(w).attr('id'));
                    }
                });

                $('#tableDiv').html('<img id="searchingAnim" src="' + srRoot + '/images/loading32.gif" height="32" width="32" /> loading folders...');
                $.post(srRoot + '/addShows/massAddTable/', url, function(data) {
                    $('#tableDiv').html(data);
                    $("#addRootDirTable").tablesorter({
                        //sortList: [[1,0]],
                        widgets: ['zebra'],
                        headers: {
                            0: { sorter: false }
                        }
                    });
                });
            }

            var lastTxt = '';
            // @TODO this needs a real name, for now this fixes the issue of the page not loading at all,
            //       before I added this I couldn't get the directories to show in the table
            var a = function() {
                if (lastTxt === $('#rootDirText').val()) {
                    return false;
                } else {
                    lastTxt = $('#rootDirText').val();
                }
                $('#rootDirStaticList').html('');
                $('#rootDirs option').each(function(i, w) {
                    $('#rootDirStaticList').append('<li class="ui-state-default ui-corner-all"><input type="checkbox" class="cb dir_check" id="' + $(w).val() + '" checked=checked> <label for="' + $(w).val() + '"><b>' + $(w).val() + '</b></label></li>');
                });
                loadContent();
            };

            a();

            $('#rootDirText').on('change', a);

            $('#rootDirStaticList').on('click', '.dir_check', loadContent);

            $('#tableDiv').on('click', '.showManage', function(event) {
                event.preventDefault();
                $("#tabs").tabs('option', 'active', 0);
                $('html,body').animate({scrollTop:0}, 1000);
            });
        },
        recommendedShows: function(){
            $('#recommendedShows').loadRemoteShows(
                '/addShows/getRecommendedShows/',
                'Loading recommended shows...',
                'Trakt timed out, refresh page to try again'
            );
        },
        trendingShows: function(){
            $('#trendingShows').loadRemoteShows(
                '/addShows/getTrendingShows/?traktList=' + $('#traktList').val(),
                'Loading trending shows...',
                'Trakt timed out, refresh page to try again'
            );

            $('#traktlistselection').on('change', function(e) {
                var traktList = e.target.value;
                window.history.replaceState({}, document.title, '?traktList=' + traktList);
                $('#trendingShows').loadRemoteShows(
                    '/addShows/getTrendingShows/?traktList=' + traktList,
                    'Loading trending shows...',
                    'Trakt timed out, refresh page to try again'
                );
            });
        },
        popularShows: function(){
            $.initRemoteShowGrid();
        }
    }
};

var UTIL = {
    exec: function(controller, action) {
        var ns = SICKRAGE;
        action = (action === undefined) ? "init" : action;

        if (controller !== "" && ns[controller] && typeof ns[controller][action] === "function") {
            ns[controller][action]();
        }
    },
    init: function() {
        var body = document.body,
        controller = body.getAttribute("data-controller"),
        action = body.getAttribute("data-action");

        UTIL.exec("common");
        UTIL.exec(controller);
        UTIL.exec(controller, action);
    }
};
if (navigator.userAgent.indexOf('PhantomJS') === -1) {
    $(document).ready(UTIL.init);
}
