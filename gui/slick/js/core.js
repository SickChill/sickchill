// @TODO Move these into common.ini when possible,
//       currently we can't do that as browser.js and a few others need it before this is loaded
var srRoot = getMeta('srRoot'),
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
};

var SICKRAGE = {
    common: {
        init: function() {
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
        }
    },
    config: {
        init: function() {
            $('#config-components').tabs();

            $(".enabler").each(function(){
                if (!$(this).prop('checked')) { $('#content_'+$(this).attr('id')).hide(); }
            });

            $(".enabler").click(function() {
                if ($(this).prop('checked')){
                    $('#content_'+$(this).attr('id')).fadeIn("fast", "linear");
                } else {
                    $('#content_'+$(this).attr('id')).fadeOut("fast", "linear");
                }
            });

            $(".viewIf").click(function() {
                if ($(this).prop('checked')) {
                    $('.hide_if_'+$(this).attr('id')).css('display','none');
                    $('.show_if_'+$(this).attr('id')).fadeIn("fast", "linear");
                } else {
                    $('.show_if_'+$(this).attr('id')).css('display','none');
                    $('.hide_if_'+$(this).attr('id')).fadeIn("fast", "linear");
                }
            });

            $(".datePresets").click(function() {
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

            $('#api_key').click(function(){
                $('#api_key').select();
            });

            $("#generate_new_apikey").click(function(){
                $.get(srRoot + '/config/general/generateApiKey', function(data){
                    if (data.error !== undefined) {
                        alert(data.error);
                        return;
                    }
                    $('#api_key').val(data);
                });
            });

            $('#branchCheckout').click(function() {
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
            $('#Backup').click(function() {
                $("#Backup").attr("disabled", true);
                $('#Backup-result').html(loading);
                var backupDir = $("#backupDir").val();
                $.get(srRoot + "/config/backuprestore/backup", {'backupDir': backupDir})
                    .done(function (data) {
                        $('#Backup-result').html(data);
                        $("#Backup").attr("disabled", false);
                    });
            });
            $('#Restore').click(function() {
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

            $(".enabler").each(function(){
                if (!$(this).prop('checked')) { $('#content_'+$(this).attr('id')).hide(); }
            });

            $(".enabler").click(function() {
                if ($(this).prop('checked')){
                    $('#content_'+$(this).attr('id')).fadeIn("fast", "linear");
                } else {
                    $('#content_'+$(this).attr('id')).fadeOut("fast", "linear");
                }
            });

            $(".viewIf").click(function() {
                if ($(this).prop('checked')) {
                    $('.hide_if_'+$(this).attr('id')).css('display','none');
                    $('.show_if_'+$(this).attr('id')).fadeIn("fast", "linear");
                } else {
                    $('.show_if_'+$(this).attr('id')).css('display','none');
                    $('.hide_if_'+$(this).attr('id')).fadeIn("fast", "linear");
                }
            });

            $(".datePresets").click(function() {
                var def = $('#date_presets').val();
                if ($(this).prop('checked') && '%x' == def) { // jshint ignore:line
                    def = '%a, %b %d, %Y';
                    $('#date_use_system_default').html('1');
                } else if (!$(this).prop('checked') && '1' == $('#date_use_system_default').html()){ // jshint ignore:line
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

            $('#api_key').click(function(){
                $('#api_key').select();
            });

            $("#generate_new_apikey").click(function(){
                $.get(srRoot + '/config/general/generateApiKey', function(data){
                    if (data.error !== undefined) {
                        alert(data.error);
                        return;
                    }
                    $('#api_key').val(data);
                });
            });

            $('#branchCheckout').click(function() {
                var url = srRoot+'/home/branchCheckout?branch='+$("#branchVersion").val();
                var checkDBversion = srRoot + "/home/getDBcompare";
                $.getJSON(checkDBversion, function(data){
                    if (data.status.toLowerCase() === "success") {
                        if (data.message.toLowerCase() === "equal") {
                            //Checkout Branch
                            window.location.href = url;
                        }
                        if (data.message.toLowerCase() === "upgrade") {
                            if ( confirm("Changing branch will upgrade your database.\nYou won't be able to downgrade afterward.\nDo you want to continue?") ) {
                                //Checkout Branch
                                window.location.href = url;
                            }
                        }
                        if (data.message.toLowerCase() === "downgrade") {
                            alert("Can't switch branch as this will result in a database downgrade.");
                        }
                    }
                });
            });
        },
        notifications: function() {
            $('#config-components').tabs();

            $('#testGrowl').click(function () {
                var growl = {};
                growl.host = $.trim($('#growl_host').val());
                growl.password = $.trim($('#growl_password').val());
                if (!growl.ost) {
                    $('#testGrowl-result').html('Please fill out the necessary fields above.');
                    $('#growl_host').addClass('warning');
                    return;
                }
                $('#growl_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testGrowl-result').html(loading);
                $.get(srRoot + '/home/testGrowl', {'host': growl.host, 'password': growl.password}).done(function (data) {
                    $('#testGrowl-result').html(data);
                    $('#testGrowl').prop('disabled', false);
                });
            });

            $('#testProwl').click(function () {
                var prowl = {};
                prowl.api = $.trim($('#prowl_api').val());
                prowl.priority = $('#prowl_priority').val();
                if (!prowl.ai) {
                    $('#testProwl-result').html('Please fill out the necessary fields above.');
                    $('#prowl_api').addClass('warning');
                    return;
                }
                $('#prowl_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testProwl-result').html(loading);
                $.get(srRoot + '/home/testProwl', {'prowl_api': prowl.api, 'prowl_priority': prowl.priority}).done(function (data) {
                    $('#testProwl-result').html(data);
                    $('#testProwl').prop('disabled', false);
                });
            });

            $('#testKODI').click(function () {
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
                $.get(srRoot + '/home/testKODI', {'host': kodi.host, 'username': kodi.username, 'password': kodi.password}).done(function (data) {
                    $('#testKODI-result').html(data);
                    $('#testKODI').prop('disabled', false);
                });
            });

            $('#testPMC').click(function () {
                var plex = {};
                plex.client = {};
                plex.client.host = $.trim($('#plex_host').val());
                plex.client.username = $.trim($('#plex_client_username').val());
                plex.client.password = $.trim($('#plex_client_password').val());
                if (!plex.host) {
                    $('#testPMC-result').html('Please fill out the necessary fields above.');
                    $('#plex_host').addClass('warning');
                    return;
                }
                $('#plex_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPMC-result').html(loading);
                $.get(srRoot + '/home/testPMC', {'host': plex.client.host, 'username': plex.client.username, 'password': plex.client.password}).done(function (data) {
                    $('#testPMC-result').html(data);
                    $('#testPMC').prop('disabled', false);
                });
            });

            $('#testPMS').click(function () {
                var plex = {};
                plex.server = {};
                plex.server.host = $.trim($('#plex_server_host').val());
                plex.username = $.trim($('#plex_username').val());
                plex.password = $.trim($('#plex_password').val());
                plex.server.token = $.trim($('#plex_server_token').val());
                if (!plex.server.host) {
                    $('#testPMS-result').html('Please fill out the necessary fields above.');
                    $('#plex_server_host').addClass('warning');
                    return;
                }
                $('#plex_server_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPMS-result').html(loading);
                $.get(srRoot + '/home/testPMS', {'host': plex.server.host, 'username': plex.username, 'password': plex.password, 'plex_server_token': plex.server.token}).done(function (data) {
                    $('#testPMS-result').html(data);
                    $('#testPMS').prop('disabled', false);
                });
            });

            $('#testEMBY').click(function () {
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
                $.get(srRoot + '/home/testEMBY', {'host': emby.host, 'emby_apikey': emby.apikey}).done(function (data) {
                    $('#testEMBY-result').html(data);
                    $('#testEMBY').prop('disabled', false);
                });
            });

            $('#testBoxcar').click(function() {
                var boxcar = {};
                boxcar.username = $.trim($('#boxcar_username').val());
                if (!boxcar.username) {
                    $('#testBoxcar-result').html('Please fill out the necessary fields above.');
                    $('#boxcar_username').addClass('warning');
                    return;
                }
                $('#boxcar_username').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testBoxcar-result').html(loading);
                $.get(srRoot + '/home/testBoxcar', {'username': boxcar.username}).done(function (data) {
                    $('#testBoxcar-result').html(data);
                    $('#testBoxcar').prop('disabled', false);
                });
            });

            $('#testBoxcar2').click(function () {
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
                $.get(srRoot + '/home/testBoxcar2', {'accesstoken': boxcar2.accesstoken}).done(function (data) {
                    $('#testBoxcar2-result').html(data);
                    $('#testBoxcar2').prop('disabled', false);
                });
            });

            $('#testPushover').click(function () {
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
                $.get(srRoot + '/home/testPushover', {'userKey': pushover.userkey, 'apiKey': pushover.apikey}).done(function (data) {
                    $('#testPushover-result').html(data);
                    $('#testPushover').prop('disabled', false);
                });
            });

            $('#testLibnotify').click(function() {
                $('#testLibnotify-result').html(loading);
                $.get(srRoot + '/home/testLibnotify', function (data) {
                    $('#testLibnotify-result').html(data);
                });
            });

            $('#twitterStep1').click(function() {
                $('#testTwitter-result').html(loading);
                $.get(srRoot + '/home/twitterStep1', function (data) {
                    window.open(data);
                }).done(function() {
                    $('#testTwitter-result').html('<b>Step1:</b> Confirm Authorization');
                });
            });

            $('#twitterStep2').click(function () {
                var twitter = {};
                twitter.key = $.trim($('#twitter_key').val());
                if (!twitter.key) {
                    $('#testTwitter-result').html('Please fill out the necessary fields above.');
                    $('#twitter_key').addClass('warning');
                    return;
                }
                $('#twitter_key').removeClass('warning');
                $('#testTwitter-result').html(loading);
                $.get(srRoot + '/home/twitterStep2', {'key': twitter.key}, function(data) {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#testTwitter').click(function() {
                $.get(srRoot + '/home/testTwitter', function(data) {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#settingsNMJ').click(function() {
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

            $('#testNMJ').click(function () {
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
                $.get(srRoot + '/home/testNMJ', {'host': nmj.host, 'database': nmj.database, 'mount': nmj.mount}).done(function (data) {
                    $('#testNMJ-result').html(data);
                    $('#testNMJ').prop('disabled', false);
                });
            });

            $('#settingsNMJv2').click(function() {
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
                $.get(srRoot + '/home/settingsNMJv2', {'host': nmjv2.host,'dbloc': nmjv2.dbloc,'instance': nmjv2.dbinstance}, function (data){
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

            $('#testNMJv2').click(function () {
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
                $.get(srRoot + '/home/testNMJv2', {'host': nmjv2.host}) .done(function (data) {
                    $('#testNMJv2-result').html(data);
                    $('#testNMJv2').prop('disabled', false);
                });
            });

            $('#testFreeMobile').click(function () {
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
                $.get(srRoot + '/home/testFreeMobile', {'freemobile_id': freemobile.id, 'freemobile_apikey': freemobile.apikey}).done(function (data) {
                    $('#testFreeMobile-result').html(data);
                    $('#testFreeMobile').prop('disabled', false);
                });
            });

            $('#TraktGetPin').click(function () {
                var trakt = {};
                trakt.pinUrl = $('#trakt_pin_url').val();
                window.open(trakt.pinUrl, "popUp", "toolbar=no, scrollbars=no, resizable=no, top=200, left=200, width=650, height=550");
                $('#trakt_pin').removeClass('hide');
            });

            $('#trakt_pin').on('keyup change', function(){
                var trakt = {};
                trakt.pin = $('#trakt_pin').val();

                if (trakt.pin.length !== 0) {
                    $('#TraktGetPin').addClass('hide');
                    $('#authTrakt').removeClass('hide');
                } else {
                    $('#TraktGetPin').removeClass('hide');
                    $('#authTrakt').addClass('hide');
                }
            });

            $('#authTrakt').click(function() {
                var trakt = {};
                trakt.pin = $('#trakt_pin').val();
                if (trakt.pin.length !== 0) {
                    $.get(srRoot + '/home/getTraktToken', { "trakt_pin": trakt.pin }).done(function (data) {
                        $('#testTrakt-result').html(data);
                        $('#authTrakt').addClass('hide');
                        $('#trakt_pin').addClass('hide');
                        $('#TraktGetPin').addClass('hide');
                    });
                }
            });

            $('#testTrakt').click(function () {
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
                    $('#testTrakt-result').html('Check blacklist name; the value need to be a trakt slug');
                    $('#trakt_blacklist_name').addClass('warning');
                    return;
                }
                $('#trakt_username').removeClass('warning');
                $('#trakt_blacklist_name').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testTrakt-result').html(loading);
                $.get(srRoot + '/home/testTrakt', {'username': trakt.username, 'blacklist_name': trakt.trendingBlacklist}).done(function (data) {
                    $('#testTrakt-result').html(data);
                    $('#testTrakt').prop('disabled', false);
                });
            });

            $('#testEmail').click(function () {
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
                            host: host,
                            port: port,
                            smtp_from: from, // jshint ignore:line
                            use_tls: tls, // jshint ignore:line
                            user: user,
                            pwd: pwd,
                            to: to
                        }, function (msg) {
                            $('#testEmail-result').html(msg);
                        });
                    }
                }
            });

            $('#testNMA').click(function () {
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
                $.get(srRoot + '/home/testNMA', {'nma_api': nma.api, 'nma_priority': nma.priority}).done(function (data) {
                    $('#testNMA-result').html(data);
                    $('#testNMA').prop('disabled', false);
                });
            });

            $('#testPushalot').click(function () {
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
                $.get(srRoot + '/home/testPushalot', {'authorizationToken': pushalot.authToken}).done(function (data) {
                    $('#testPushalot-result').html(data);
                    $('#testPushalot').prop('disabled', false);
                });
            });

            $('#testPushbullet').click(function () {
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
                $.get(srRoot + '/home/testPushbullet', {'api': pushbullet.api}).done(function (data) {
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

                $.get(srRoot + "/home/getPushbulletDevices", {'api': pushbullet.api}, function (data) {
                    pushbullet.devices = jQuery.parseJSON(data).devices;
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
                    if (pushbullet.currentDevice === '') {
                        $("#pushbullet_device_list").prepend('<option value="" selected>All devices</option>');
                    } else {
                        $("#pushbullet_device_list").prepend('<option value="">All devices</option>');
                    }
                    if(msg) {
                        $('#testPushbullet-result').html(msg);
                    }
                });

                $("#pushbullet_device_list").change(function(){
                    $("#pushbullet_device").val($("#pushbullet_device_list").val());
                    $('#testPushbullet-result').html("Don't forget to save your new pushbullet settings.");
                });
            }

            $('#getPushbulletDevices').click(function(){
                getPushbulletDevices("Device list updated. Please choose a device to push to.");
            });

            // we have to call this function on dom ready to create the devices select
            getPushbulletDevices();

            // @TODO Find out what notify_data actually does since it doesn't seem to be a real function
            $('#email_show').change(function() {
                var key = parseInt($('#email_show').val(), 10);
                $('#email_show_list').val(key >= 0 ? notify_data[key.toString()].list : ''); // jshint ignore:line
            });

            // Update the internal data struct anytime settings are saved to the server
            $('#email_show').bind('notify', function() {
                loadShowNotifyLists();
            });

            function loadShowNotifyLists() {
                $.get(srRoot + "/home/loadShowNotifyLists", function(data) {
                    var list, html, s;
                    list = $.parseJSON(data); // @TODO The line below this is the same as the $('#email_show') function above
                    notify_data = list; // jshint ignore:line
                    if (list._size === 0) { return; }
                    html = '<option value="-1">-- Select --</option>';
                    for (s in list) {
                        if (s.charAt(0) !== '_') {
                            html += '<option value="' + list[s].id + '">' + $('<div/>').text(list[s].name).html() + '</option>';
                        }
                    }
                    $('#email_show').html(html);
                    $('#email_show_list').val('');
                });
            }
            // Load the per show notify lists everytime this page is loaded
            loadShowNotifyLists();

            $('#email_show_save').click(function() {
                $.post(srRoot + "/home/saveShowNotifyList", {
                    show: $('#email_show').val(),
                    emails: $('#email_show_list').val()
                }, function() {
                    // Reload the per show notify lists to reflect changes
                    loadShowNotifyLists();
                });
            });

            // show instructions for plex when enabled
            $('#use_plex').click(function() {
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
                    pattern: example.pattern,
                    anime_type: 3 // jshint ignore:line
                }, function (data) {
                    if (data) {
                        $('#naming_example').text(data + '.ext');
                        $('#naming_example_div').show();
                    } else {
                        $('#naming_example_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: 3 // jshint ignore:line
                }, function (data) {
                    if (data) {
                        $('#naming_example_multi').text(data + '.ext');
                        $('#naming_example_multi_div').show();
                    } else {
                        $('#naming_example_multi_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: example.animeType // jshint ignore:line
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
                    pattern: pattern,
                    abd: 'True'
                }, function (data) {
                    if (data) {
                        $('#naming_abd_example').text(data + '.ext');
                        $('#naming_abd_example_div').show();
                    } else {
                        $('#naming_abd_example_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {
                    pattern: pattern,
                    abd: 'True'
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
                    pattern: pattern,
                    sports: 'True'
                }, function (data) {
                    if (data) {
                        $('#naming_sports_example').text(data + '.ext');
                        $('#naming_sports_example_div').show();
                    } else {
                        $('#naming_sports_example_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {
                    pattern: pattern,
                    sports: 'True'
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
                    pattern: example.pattern,
                    anime_type: example.animeType // jshint ignore:line
                }, function (data) {
                    if (data) {
                        $('#naming_example_anime').text(data + '.ext');
                        $('#naming_example_anime_div').show();
                    } else {
                        $('#naming_example_anime_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: example.animeType // jshint ignore:line
                }, function (data) {
                    if (data) {
                        $('#naming_example_multi_anime').text(data + '.ext');
                        $('#naming_example_multi_anime_div').show();
                    } else {
                        $('#naming_example_multi_anime_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: example.animeType // jshint ignore:line
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

            $('#naming_multi_ep').change(fillExamples);
            $('#naming_pattern').focusout(fillExamples);
            $('#naming_pattern').keyup(function () {
                typewatch(function () {
                    fillExamples();
                }, 500);
            });

            $('#naming_anime_multi_ep').change(fillAnimeExamples);
            $('#naming_anime_pattern').focusout(fillAnimeExamples);
            $('#naming_anime_pattern').keyup(function () {
                typewatch(function () {
                    fillAnimeExamples();
                }, 500);
            });

            $('#naming_abd_pattern').focusout(fillExamples);
            $('#naming_abd_pattern').keyup(function () {
                typewatch(function () {
                    fillAbdExamples();
                }, 500);
            });

            $('#naming_sports_pattern').focusout(fillExamples);
            $('#naming_sports_pattern').keyup(function () {
                typewatch(function () {
                    fillSportsExamples();
                }, 500);
            });

            $('#naming_anime_pattern').focusout(fillExamples);
            $('#naming_anime_pattern').keyup(function () {
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

            function toggleTorrentTitle(){
                if ($('#use_torrents').prop('checked')){
                    $('#no_torrents').show();
                } else {
                    $('#no_torrents').hide();
                }
            }

            $.fn.nzbMethodHandler = function() {
                var selectedProvider = $('#nzb_method :selected').val(),
                    blackholeSettings = '#blackhole_settings',
                    sabnzbdSettings = '#sabnzbd_settings',
                    testSABnzbd = '#testSABnzbd',
                    testSABnzbdResult = '#testSABnzbd_result',
                    nzbgetSettings = '#nzbget_settings';

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

            $.fn.rtorrentScgi = function(){
                var selectedProvider = $('#torrent_method :selected').val();

                if (selectedProvider.toLowerCase() === 'rtorrent') {
                    var hostname = $('#torrent_host').prop('value');
                    var isMatch = hostname.substr(0, 7) === "scgi://";

                    if (isMatch) {
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
            };

            $.fn.torrentMethodHandler = function() {
                $('#options_torrent_clients').hide();
                $('#options_torrent_blackhole').hide();

                var selectedProvider = $('#torrent_method :selected').val(),
                    host = ' host:port',
                    username = ' username',
                    password = ' password',
                    client = '',
                    optionPanel = '#options_torrent_blackhole',
                    rpcurl = ' RPC URL';

                if (selectedProvider.toLowerCase() !== 'blackhole') {
                    var label_warning_deluge = '#label_warning_deluge',
                        label_anime_warning_deluge = '#label_anime_warning_deluge',
                        host_desc_rtorrent = '#host_desc_rtorrent',
                        host_desc_torrent = '#host_desc_torrent',
                        torrent_verify_cert_option = '#torrent_verify_cert_option',
                        torrent_path_option = '#torrent_path_option',
                        torrent_seed_time_option = '#torrent_seed_time_option',
                        torrent_high_bandwidth_option = '#torrent_high_bandwidth_option',
                        torrent_label_option = '#torrent_label_option',
                        torrent_label_anime_option = '#torrent_label_anime_option',
                        path_synology = '#path_synology',
                        torrent_paused_option = '#torrent_paused_option';

                    $(label_warning_deluge).hide();
                    $(label_anime_warning_deluge).hide();
                    $(label_anime_warning_deluge).hide();
                    $(host_desc_rtorrent).hide();
                    $(host_desc_torrent).show();
                    $(torrent_verify_cert_option).hide();
                    $(torrent_verify_deluge).hide();
                    $(torrent_verify_rtorrent).hide();
                    $(torrent_auth_type_option).hide();
                    $(torrent_path_option).show();
                    $(torrent_path_option).find('.fileBrowser').show();
                    $(torrent_seed_time_option).hide();
                    $(torrent_high_bandwidth_option).hide();
                    $(torrent_label_option).show();
                    $(torrent_label_anime_option).show();
                    $(path_synology).hide();
                    $(torrent_paused_option).show();
                    $(torrent_rpcurl_option).hide();
                    $(this).rtorrentScgi();

                    if (selectedProvider.toLowerCase() === 'utorrent') {
                        client = 'uTorrent';
                        $(torrent_path_option).hide();
                        $('#torrent_seed_time_label').text('Minimum seeding time is');
                        $(torrent_seed_time_option).show();
                        $('#host_desc_torrent').text('URL to your uTorrent client (e.g. http://localhost:8000)');
                    } else if (selectedProvider.toLowerCase() === 'transmission'){
                        client = 'Transmission';
                        $('#torrent_seed_time_label').text('Stop seeding when inactive for');
                        $(torrent_seed_time_option).show();
                        $(torrent_high_bandwidth_option).show();
                        $(torrent_label_option).hide();
                        $(torrent_label_anime_option).hide();
                        $(torrent_rpcurl_option).show();
                        $('#host_desc_torrent').text('URL to your Transmission client (e.g. http://localhost:9091)');
                    } else if (selectedProvider.toLowerCase() === 'deluge'){
                        client = 'Deluge';
                        $(torrent_verify_cert_option).show();
                        $(torrent_verify_deluge).show();
                        $(torrent_verify_rtorrent).hide();
                        $(label_warning_deluge).show();
                        $(label_anime_warning_deluge).show();
                        $('#torrent_username_option').hide();
                        $('#torrent_username').prop('value', '');
                        $('#host_desc_torrent').text('URL to your Deluge client (e.g. http://localhost:8112)');
                    } else if ('deluged' == selectedProvider){
                        client = 'Deluge';
                        $(torrent_verify_cert_option).hide();
                        $(torrent_verify_deluge).hide();
                        $(torrent_verify_rtorrent).hide();
                        $(label_warning_deluge).show();
                        $(label_anime_warning_deluge).show();
                        $('#torrent_username_option').show();
                        $('#host_desc_torrent').text('IP or Hostname of your Deluge Daemon (e.g. scgi://localhost:58846)');
                    } else if ('download_station' == selectedProvider){
                        client = 'Synology DS';
                        $(torrent_label_option).hide();
                        $(torrent_label_anime_option).hide();
                        $('#torrent_paused_option').hide();
                        $(torrent_path_option).find('.fileBrowser').hide();
                        $('#host_desc_torrent').text('URL to your Synology DS client (e.g. http://localhost:5000)');
                        $(path_synology).show();
                    } else if ('rtorrent' == selectedProvider){
                        client = 'rTorrent';
                        $(torrent_paused_option).hide();
                        $('#host_desc_torrent').text('URL to your rTorrent client (e.g. scgi://localhost:5000 <br> or https://localhost/rutorrent/plugins/httprpc/action.php)');
                        $(torrent_verify_cert_option).show();
                        $(torrent_verify_deluge).hide();
                        $(torrent_verify_rtorrent).show();
                        $(torrent_auth_type_option).show();
                    } else if ('qbittorrent' == selectedProvider){
                        client = 'qbittorrent';
                        $(torrent_path_option).hide();
                        $(torrent_label_option).hide();
                        $(torrent_label_anime_option).hide();
                        $('#host_desc_torrent').text('URL to your qbittorrent client (e.g. http://localhost:8080)');
                    } else if ('mlnet' == selectedProvider){
                        client = 'mlnet';
                        $(torrent_path_option).hide();
                        $(torrent_label_option).hide();
                        $(torrent_verify_cert_option).hide();
                        $(torrent_verify_deluge).hide();
                        $(torrent_verify_rtorrent).hide();
                        $(torrent_label_anime_option).hide();
                        $(torrent_paused_option).hide();
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

            $('#nzb_method').change($(this).nzbMethodHandler);

            $(this).nzbMethodHandler();

            $('#testSABnzbd').click(function(){
                $('#testSABnzbd_result').html(loading);
                var sab_host = $('#sab_host').val();
                var sab_username = $('#sab_username').val();
                var sab_password = $('#sab_password').val();
                var sab_apiKey = $('#sab_apikey').val();

                $.get(srRoot + '/home/testSABnzbd', {'host': sab_host, 'username': sab_username, 'password': sab_password, 'apikey': sab_apiKey}, function(data){
                    $('#testSABnzbd_result').html(data);
                });
            });

            $('#torrent_method').change($(this).torrentMethodHandler);

            $(this).torrentMethodHandler();

            $('#use_torrents').click(function(){
                toggleTorrentTitle();
            });

            $('#test_torrent').click(function(){
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

            $('#torrent_host').change($(this).rtorrentScgi);
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

            $('#editAService').change(function(){
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
                }
            });

            $("#service_order_list").disableSelection();
        },
        providers: function() {
            // @TODO This function need to be filled with ConfigProviders.js but can't be as we've got scope issues currently.
            console.log('This function need to be filled with ConfigProviders.js but can\'t be as we\'ve got scope issues currently.');
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
                row += '<td style="width: 1%;">' + season + 'x' + episode + '</td>';
                row += '<td>' + name + '</td>';
                row += '<td style="float: right;">';
                subtitles = subtitles.split(',');
                for (var i in subtitles) {
                    if (subtitles.hasOwnProperty(i)) {
                        row += '<img src="/images/subtitles/flags/' + subtitles[i] + '.png" width="16" height="11" alt="' + subtitles[i] + '" />&nbsp;';
                    }
                }
                row += '</td>';
                row += '</tr>';

                return row;
            }
        },
        index: function() {
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
                widgets: ['zebra'],
                headers: {
                    0: { sorter: false},
                    1: { sorter: 'showNames'},
                    2: { sorter: 'quality'},
                    3: { sorter: 'sports'},
                    4: { sorter: 'scene'},
                    5: { sorter: 'anime'},
                    6: { sorter: 'flatfold'},
                    7: { sorter: 'archive_firstmatch'},
                    8: { sorter: 'paused'},
                    9: { sorter: 'subtitle'},
                    10: { sorter: 'default_ep_status'},
                    11: { sorter: 'status'},
                    12: { sorter: false},
                    13: { sorter: false},
                    14: { sorter: false},
                    15: { sorter: false},
                    16: { sorter: false},
                    17: { sorter: false}
                }
            });
        },
        backlogOverview: function() {
            $('#pickShow').change(function(){
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
            $('#limit').change(function(){
                window.location.href = srRoot + '/manage/failedDownloads/?limit=' + $(this).val();
            });
        },
        massEdit: function() {
            $('#location').fileBrowser({ title: 'Select Show Location' });
        },
        episodeStatuses: function() {
            $('.allCheck').click(function(){
                var indexerId = $(this).attr('id').split('-')[1];
                $('.' + indexerId + '-epcheck').prop('checked', $(this).prop('checked'));
            });

            $('.get_more_eps').click(function(){
                var curIndexerId = $(this).attr('id');
                var checked = $('#allCheck-' + curIndexerId).prop('checked');
                var lastRow = $('tr#' + curIndexerId);
                var clicked = $(this).attr('data-clicked');
                var action = $(this).attr('value');

                if(!clicked) {
                    $.getJSON(srRoot+'/manage/showEpisodeStatuses',{
                        indexer_id: curIndexerId, // jshint ignore:line
                        whichStatus: $('#oldStatus').val()
                    }, function (data) {
                        $.each(data, function(season,eps){
                            $.each(eps, function(episode, name) {
                                //alert(season+'x'+episode+': '+name);
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
            $('.selectAllShows').click(function(){
                $('.allCheck').each(function(){
                    this.checked = true;
                });
                $('input[class*="-epcheck"]').each(function(){
                    this.checked = true;
                });
            });

            // clears all visible episode checkboxes and the season selectors
            $('.unselectAllShows').click(function(){
                $('.allCheck').each(function(){
                    this.checked = false;
                });
                $('input[class*="-epcheck"]').each(function(){
                    this.checked = false;
                });
            });
        },
        subtitleMissed: function() {
            $('.allCheck').click(function(){
                var indexerId = $(this).attr('id').split('-')[1];
                $('.'+indexerId+'-epcheck').prop('checked', $(this).prop('checked'));
            });

            $('.get_more_eps').click(function(){
                var indexerId = $(this).attr('id');
                var checked = $('#allCheck-'+indexerId).prop('checked');
                var lastRow = $('tr#'+indexerId);
                var clicked = $(this).attr('data-clicked');
                var action = $(this).attr('value');

                if (!clicked) {
                    $.getJSON(srRoot + '/manage/showSubtitleMissed', {
                        indexer_id: indexerId, // jshint ignore:line
                        whichSubs: $('#selectSubLang').val()
                    }, function(data) {
                        $.each(data, function(season, eps) {
                            $.each(eps, function(episode, data) {
                                lastRow.after($.makeEpisodeRow(indexerId, season, episode, data.name, data.subtitles, checked));
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

            // selects all visible episode checkboxes.
            $('.selectAllShows').click(function(){
                $('.allCheck').each(function(){
                    this.checked = true;
                });
                $('input[class*="-epcheck"]').each(function(){
                    this.checked = true;
                });
            });

            // clears all visible episode checkboxes and the season selectors
            $('.unselectAllShows').click(function(){
                $('.allCheck').each(function(){
                    this.checked = false;
                });
                $('input[class*="-epcheck"]').each(function(){
                    this.checked = false;
                });
            });
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

$(document).ready(UTIL.init);
