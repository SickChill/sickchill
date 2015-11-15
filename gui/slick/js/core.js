var srRoot = getMeta('srRoot'),
    themeSpinner = getMeta('themeSpinner'),
    anonURL = getMeta('anonURL'),
    topImageHtml = '<img src="' + srRoot + '/images/top.gif" width="31" height="11" alt="Jump to top" />',
    loading = '<img src="' + srRoot + '/images/loading16' + themeSpinner + '.gif" height="16" width="16" />';

function configSuccess(){
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
}

var SICKRAGE = {
    common: {
        init: function() {
            $("#config-components").tabs({
                activate: function (event, ui) {
                    var lastOpenedPanel = $(this).data("lastOpenedPanel"),
                        selected = $(this).tabs('option', 'selected');

                    if (!lastOpenedPanel) { lastOpenedPanel = $(ui.oldPanel); }

                    if (!$(this).data("topPositionTab")) { $(this).data("topPositionTab", $(ui.newPanel).position().top); }

                    //Dont use the builtin fx effects. This will fade in/out both tabs, we dont want that
                    //Fadein the new tab yourself
                    $(ui.newPanel).hide().fadeIn(0);

                    if (lastOpenedPanel) {
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
            if ((navigator.maxTouchPoints || 0) < 2) {
                $('.dropdown-toggle').on('click', function(e) {
                    var $this = $(this);
                    if ($this.attr('aria-expanded') === 'true') {
                        window.location.href = $this.attr('href');
                    }
                });
            }

            if(metaToBool('sickbeard.FUZZY_DATING')){
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
                var growlHost = $.trim($('#growl_host').val());
                var growlPassword = $.trim($('#growl_password').val());
                if (!growlHost) {
                    $('#testGrowl-result').html('Please fill out the necessary fields above.');
                    $('#growl_host').addClass('warning');
                    return;
                }
                $('#growl_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testGrowl-result').html(loading);
                $.get(srRoot + '/home/testGrowl', {'host': growlHost, 'password': growlPassword}).done(function (data) {
                    $('#testGrowl-result').html(data);
                    $('#testGrowl').prop('disabled', false);
                });
            });

            $('#testProwl').click(function () {
                var prowlApi = $.trim($('#prowl_api').val());
                var prowlPriority = $('#prowl_priority').val();
                if (!prowlApi) {
                    $('#testProwl-result').html('Please fill out the necessary fields above.');
                    $('#prowl_api').addClass('warning');
                    return;
                }
                $('#prowl_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testProwl-result').html(loading);
                $.get(srRoot + '/home/testProwl', {'prowl_api': prowlApi, 'prowl_priority': prowlPriority}).done(function (data) {
                    $('#testProwl-result').html(data);
                    $('#testProwl').prop('disabled', false);
                });
            });

            $('#testKODI').click(function () {
                var kodi_host = $.trim($('#kodi_host').val());
                var kodi_username = $.trim($('#kodi_username').val());
                var kodi_password = $.trim($('#kodi_password').val());
                if (!kodi_host) {
                    $('#testKODI-result').html('Please fill out the necessary fields above.');
                    $('#kodi_host').addClass('warning');
                    return;
                }
                $('#kodi_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testKODI-result').html(loading);
                $.get(srRoot + '/home/testKODI', {'host': kodi_host, 'username': kodi_username, 'password': kodi_password}).done(function (data) {
                    $('#testKODI-result').html(data);
                    $('#testKODI').prop('disabled', false);
                });
            });

            $('#testPMC').click(function () {
                var plex_host = $.trim($('#plex_host').val());
                var plex_client_username = $.trim($('#plex_client_username').val());
                var plex_client_password = $.trim($('#plex_client_password').val());
                if (!plex_host) {
                    $('#testPMC-result').html('Please fill out the necessary fields above.');
                    $('#plex_host').addClass('warning');
                    return;
                }
                $('#plex_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPMC-result').html(loading);
                $.get(srRoot + '/home/testPMC', {'host': plex_host, 'username': plex_client_username, 'password': plex_client_password}).done(function (data) {
                    $('#testPMC-result').html(data);
                    $('#testPMC').prop('disabled', false);
                });
            });

            $('#testPMS').click(function () {
                var plex_server_host = $.trim($('#plex_server_host').val());
                var plex_username = $.trim($('#plex_username').val());
                var plex_password = $.trim($('#plex_password').val());
                var plex_server_token = $.trim($('#plex_server_token').val());
                if (!plex_server_host) {
                    $('#testPMS-result').html('Please fill out the necessary fields above.');
                    $('#plex_server_host').addClass('warning');
                    return;
                }
                $('#plex_server_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPMS-result').html(loading);
                $.get(srRoot + '/home/testPMS', {'host': plex_server_host, 'username': plex_username, 'password': plex_password, 'plex_server_token': plex_server_token}).done(function (data) {
                    $('#testPMS-result').html(data);
                    $('#testPMS').prop('disabled', false);
                });
            });

            $('#testEMBY').click(function () {
                var emby_host = $('#emby_host').val();
                var emby_apikey = $('#emby_apikey').val();
                if (!emby_host || !emby_apikey) {
                    $('#testEMBY-result').html('Please fill out the necessary fields above.');
                    if (!emby_host) {
                        $('#emby_host').addClass('warning');
                    } else {
                        $('#emby_host').removeClass('warning');
                    }
                    if (!emby_apikey) {
                        $('#emby_apikey').addClass('warning');
                    } else {
                        $('#emby_apikey').removeClass('warning');
                    }
                    return;
                }
                $('#emby_host,#emby_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testEMBY-result').html(loading);
                $.get(srRoot + '/home/testEMBY', {'host': emby_host, 'emby_apikey': emby_apikey}).done(function (data) {
                    $('#testEMBY-result').html(data);
                    $('#testEMBY').prop('disabled', false);
                });
            });

            $('#testBoxcar').click(function() {
                var boxcar_username = $.trim($('#boxcar_username').val());
                if (!boxcar_username) {
                    $('#testBoxcar-result').html('Please fill out the necessary fields above.');
                    $('#boxcar_username').addClass('warning');
                    return;
                }
                $('#boxcar_username').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testBoxcar-result').html(loading);
                $.get(srRoot + '/home/testBoxcar', {'username': boxcar_username}).done(function (data) {
                    $('#testBoxcar-result').html(data);
                    $('#testBoxcar').prop('disabled', false);
                });
            });

            $('#testBoxcar2').click(function () {
                var boxcar2_accesstoken = $.trim($('#boxcar2_accesstoken').val());
                if (!boxcar2_accesstoken) {
                    $('#testBoxcar2-result').html('Please fill out the necessary fields above.');
                    $('#boxcar2_accesstoken').addClass('warning');
                    return;
                }
                $('#boxcar2_accesstoken').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testBoxcar2-result').html(loading);
                $.get(srRoot + '/home/testBoxcar2', {'accesstoken': boxcar2_accesstoken}).done(function (data) {
                    $('#testBoxcar2-result').html(data);
                    $('#testBoxcar2').prop('disabled', false);
                });
            });

            $('#testPushover').click(function () {
                var pushover_userkey = $('#pushover_userkey').val();
                var pushover_apikey = $('#pushover_apikey').val();
                if (!pushover_userkey || !pushover_apikey) {
                    $('#testPushover-result').html('Please fill out the necessary fields above.');
                    if (!pushover_userkey) {
                        $('#pushover_userkey').addClass('warning');
                    } else {
                        $('#pushover_userkey').removeClass('warning');
                    }
                    if (!pushover_apikey) {
                        $('#pushover_apikey').addClass('warning');
                    } else {
                        $('#pushover_apikey').removeClass('warning');
                    }
                    return;
                }
                $('#pushover_userkey,#pushover_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPushover-result').html(loading);
                $.get(srRoot + '/home/testPushover', {'userKey': pushover_userkey, 'apiKey': pushover_apikey}).done(function (data) {
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
                var twitter_key = $.trim($('#twitter_key').val());
                if (!twitter_key) {
                    $('#testTwitter-result').html('Please fill out the necessary fields above.');
                    $('#twitter_key').addClass('warning');
                    return;
                }
                $('#twitter_key').removeClass('warning');
                $('#testTwitter-result').html(loading);
                $.get(srRoot + '/home/twitterStep2', {'key': twitter_key}, function(data) {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#testTwitter').click(function() {
                $.get(srRoot + '/home/testTwitter', function(data) {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#settingsNMJ').click(function() {
                if (!$('#nmj_host').val()) {
                    alert('Please fill in the Popcorn IP address');
                    $('#nmj_host').focus();
                    return;
                }
                $('#testNMJ-result').html(loading);
                var nmj_host = $('#nmj_host').val();

                $.get(srRoot + '/home/settingsNMJ', {'host': nmj_host}, function (data) {
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
                var nmj_host = $.trim($('#nmj_host').val());
                var nmj_database = $('#nmj_database').val();
                var nmj_mount = $('#nmj_mount').val();
                if (!nmj_host) {
                    $('#testNMJ-result').html('Please fill out the necessary fields above.');
                    $('#nmj_host').addClass('warning');
                    return;
                }
                $('#nmj_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testNMJ-result').html(loading);
                $.get(srRoot + '/home/testNMJ', {'host': nmj_host, 'database': nmj_database, 'mount': nmj_mount}).done(function (data) {
                    $('#testNMJ-result').html(data);
                    $('#testNMJ').prop('disabled', false);
                });
            });

            $('#settingsNMJv2').click(function() {
                if (!$('#nmjv2_host').val()) {
                    alert('Please fill in the Popcorn IP address');
                    $('#nmjv2_host').focus();
                    return;
                }
                $('#testNMJv2-result').html(loading);
                var nmjv2_host = $('#nmjv2_host').val();
                var nmjv2_dbloc;
                var radios = document.getElementsByName('nmjv2_dbloc');
                for(var i = 0, len = radios.length; i < len; i++) {
                    if (radios[i].checked) {
                        nmjv2_dbloc=radios[i].value;
                        break;
                    }
                }

                var nmjv2_dbinstance=$('#NMJv2db_instance').val();
                $.get(srRoot + '/home/settingsNMJv2', {'host': nmjv2_host,'dbloc': nmjv2_dbloc,'instance': nmjv2_dbinstance}, function (data){
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
                var nmjv2_host = $.trim($('#nmjv2_host').val());
                if (!nmjv2_host) {
                    $('#testNMJv2-result').html('Please fill out the necessary fields above.');
                    $('#nmjv2_host').addClass('warning');
                    return;
                }
                $('#nmjv2_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testNMJv2-result').html(loading);
                $.get(srRoot + '/home/testNMJv2', {'host': nmjv2_host}) .done(function (data) {
                    $('#testNMJv2-result').html(data);
                    $('#testNMJv2').prop('disabled', false);
                });
            });

            $('#testFreeMobile').click(function () {
                var freemobile_id = $.trim($('#freemobile_id').val());
                var freemobile_apikey = $.trim($('#freemobile_apikey').val());
                if (!freemobile_id || !freemobile_apikey) {
                    $('#testFreeMobile-result').html('Please fill out the necessary fields above.');
                    if (!freemobile_id) {
                        $('#freemobile_id').addClass('warning');
                    } else {
                        $('#freemobile_id').removeClass('warning');
                    }
                    if (!freemobile_apikey) {
                        $('#freemobile_apikey').addClass('warning');
                    } else {
                        $('#freemobile_apikey').removeClass('warning');
                    }
                    return;
                }
                $('#freemobile_id,#freemobile_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testFreeMobile-result').html(loading);
                $.get(srRoot + '/home/testFreeMobile', {'freemobile_id': freemobile_id, 'freemobile_apikey': freemobile_apikey}).done(function (data) {
                    $('#testFreeMobile-result').html(data);
                    $('#testFreeMobile').prop('disabled', false);
                });
            });

            $('#TraktGetPin').click(function () {
                var trakt_pin_url = $('#trakt_pin_url').val();
                var w;
                w = window.open(trakt_pin_url, "popUp", "toolbar=no, scrollbars=no, resizable=no, top=200, left=200, width=650, height=550");
                 $('#trakt_pin').removeClass('hide');
            });

            $('#trakt_pin').on('keyup change', function(){
                var trakt_pin = $('#trakt_pin').val();

                if (trakt_pin.length !== 0) {
                    $('#TraktGetPin').addClass('hide');
                    $('#authTrakt').removeClass('hide');
                } else {
                    $('#TraktGetPin').removeClass('hide');
                    $('#authTrakt').addClass('hide');
                }
            });

            $('#authTrakt').click(function() {
                var trakt_pin = $('#trakt_pin').val();
                if (trakt_pin.length !== 0) {
                    $.get(srRoot + '/home/getTraktToken', { "trakt_pin": trakt_pin }).done(function (data) {
                        $('#testTrakt-result').html(data);
                        $('#authTrakt').addClass('hide');
                        $('#trakt_pin').addClass('hide');
                        $('#TraktGetPin').addClass('hide');
                    });
                }
            });

            $('#testTrakt').click(function () {
                var trakt_username = $.trim($('#trakt_username').val());
                var trakt_trending_blacklist = $.trim($('#trakt_blacklist_name').val());
                if (!trakt_username) {
                    $('#testTrakt-result').html('Please fill out the necessary fields above.');
                    if (!trakt_username) {
                        $('#trakt_username').addClass('warning');
                    } else {
                        $('#trakt_username').removeClass('warning');
                    }
                    return;
                }

                if (/\s/g.test(trakt_trending_blacklist)) {
                    $('#testTrakt-result').html('Check blacklist name; the value need to be a trakt slug');
                    $('#trakt_blacklist_name').addClass('warning');
                    return;
                }
                $('#trakt_username').removeClass('warning');
                $('#trakt_blacklist_name').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testTrakt-result').html(loading);
                $.get(srRoot + '/home/testTrakt', {'username': trakt_username, 'blacklist_name': trakt_trending_blacklist}).done(function (data) {
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
                        $.get(srRoot + '/home/testEmail', {host: host, port: port, smtp_from: from, use_tls: tls, user: user, pwd: pwd, to: to}, function (msg) {
                            $('#testEmail-result').html(msg);
                        });
                    }
                }
            });

            $('#testNMA').click(function () {
                var nma_api = $.trim($('#nma_api').val());
                var nma_priority = $('#nma_priority').val();
                if (!nma_api) {
                    $('#testNMA-result').html('Please fill out the necessary fields above.');
                    $('#nma_api').addClass('warning');
                    return;
                }
                $('#nma_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testNMA-result').html(loading);
                $.get(srRoot + '/home/testNMA', {'nma_api': nma_api, 'nma_priority': nma_priority}).done(function (data) {
                    $('#testNMA-result').html(data);
                    $('#testNMA').prop('disabled', false);
                });
            });

            $('#testPushalot').click(function () {
                var pushalot_authorizationtoken = $.trim($('#pushalot_authorizationtoken').val());
                if (!pushalot_authorizationtoken) {
                    $('#testPushalot-result').html('Please fill out the necessary fields above.');
                    $('#pushalot_authorizationtoken').addClass('warning');
                    return;
                }
                $('#pushalot_authorizationtoken').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPushalot-result').html(loading);
                $.get(srRoot + '/home/testPushalot', {'authorizationToken': pushalot_authorizationtoken}).done(function (data) {
                    $('#testPushalot-result').html(data);
                    $('#testPushalot').prop('disabled', false);
                });
            });

            $('#testPushbullet').click(function () {
                var pushbullet_api = $.trim($('#pushbullet_api').val());
                if (!pushbullet_api) {
                    $('#testPushbullet-result').html('Please fill out the necessary fields above.');
                    $('#pushbullet_api').addClass('warning');
                    return;
                }
                $('#pushbullet_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPushbullet-result').html(loading);
                $.get(srRoot + '/home/testPushbullet', {'api': pushbullet_api}).done(function (data) {
                    $('#testPushbullet-result').html(data);
                    $('#testPushbullet').prop('disabled', false);
                });
            });

            function get_pushbullet_devices(msg){
                if(msg) { $('#testPushbullet-result').html(loading); }

                var pushbullet_api = $("#pushbullet_api").val();

                if(!pushbullet_api) {
                    $('#testPushbullet-result').html("You didn't supply a Pushbullet api key");
                    $("#pushbullet_api").focus();
                    return false;
                }

                $.get(srRoot + "/home/getPushbulletDevices", {'api': pushbullet_api}, function (data) {
                    var devices = jQuery.parseJSON(data).devices;
                    var current_pushbullet_device = $("#pushbullet_device").val();
                    $("#pushbullet_device_list").html('');
                    for (var i = 0, len = devices.length; i < len; i++) {
                        if(devices[i].active === true) {
                            if(current_pushbullet_device == devices[i].iden) {
                                $("#pushbullet_device_list").append('<option value="'+devices[i].iden+'" selected>' + devices[i].nickname + '</option>');
                            } else {
                                $("#pushbullet_device_list").append('<option value="'+devices[i].iden+'">' + devices[i].nickname + '</option>');
                            }
                        }
                    }
                    if (current_pushbullet_device === '') {
                        $("#pushbullet_device_list").prepend('<option value="" selected>All devices</option>');
                    } else {
                        $("#pushbullet_device_list").prepend('<option value="">All devices</option>');
                    }
                    if(msg) $('#testPushbullet-result').html(msg);
                });

                $("#pushbullet_device_list").change(function(){
                    $("#pushbullet_device").val($("#pushbullet_device_list").val());
                    $('#testPushbullet-result').html("Don't forget to save your new pushbullet settings.");
                });
            }

            $('#getPushbulletDevices').click(function(){
                get_pushbullet_devices("Device list updated. Please choose a device to push to.");
            });

            // we have to call this function on dom ready to create the devices select
            get_pushbullet_devices();

            $('#email_show').change(function() {
                var key = parseInt($('#email_show').val(), 10);
                $('#email_show_list').val(key >= 0 ? notify_data[key.toString()].list : '');
            });

            // Update the internal data struct anytime settings are saved to the server
            $('#email_show').bind('notify', function() {
                load_show_notify_lists();
            });

            function load_show_notify_lists() {
                $.get(srRoot + "/home/loadShowNotifyLists", function(data) {
                    var list, html, s;
                    list = $.parseJSON(data);
                    notify_data = list;
                    if (list._size === 0) return;
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
            load_show_notify_lists();

            $('#email_show_save').click(function() {
                $.post(srRoot + "/home/saveShowNotifyList", { show: $('#email_show').val(), emails: $('#email_show_list').val()}, function (data) {
                    // Reload the per show notify lists to reflect changes
                    load_show_notify_lists();
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

            function israr_supported() {
                var pattern = $('#naming_pattern').val();
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

            function fill_examples() {
                var pattern = $('#naming_pattern').val();
                var multi = $('#naming_multi_ep :selected').val();
                var anime_type = $('input[name="naming_anime"]:checked').val();

                $.get(srRoot + '/config/postProcessing/testNaming', {pattern: pattern, anime_type: 3}, function (data) {
                    if (data) {
                        $('#naming_example').text(data + '.ext');
                        $('#naming_example_div').show();
                    } else {
                        $('#naming_example_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/testNaming', {pattern: pattern, multi: multi, anime_type: 3}, function (data) {
                    if (data) {
                        $('#naming_example_multi').text(data + '.ext');
                        $('#naming_example_multi_div').show();
                    } else {
                        $('#naming_example_multi_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {pattern: pattern, multi: multi, anime_type: anime_type}, function (data) {
                    if (data == "invalid") {
                        $('#naming_pattern').qtip('option', {
                            'content.text': 'This pattern is invalid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFDDDD');
                    } else if (data == "seasonfolders") {
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

            function fill_abd_examples() {
                var pattern = $('#naming_abd_pattern').val();

                $.get(srRoot + '/config/postProcessing/testNaming', {pattern: pattern, abd: 'True'}, function (data) {
                    if (data) {
                        $('#naming_abd_example').text(data + '.ext');
                        $('#naming_abd_example_div').show();
                    } else {
                        $('#naming_abd_example_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {pattern: pattern, abd: 'True'}, function (data) {
                    if (data == "invalid") {
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': 'This pattern is invalid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_abd_pattern').qtip('toggle', true);
                        $('#naming_abd_pattern').css('background-color', '#FFDDDD');
                    } else if (data == "seasonfolders") {
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

            function fill_sports_examples() {
                var pattern = $('#naming_sports_pattern').val();

                $.get(srRoot + '/config/postProcessing/testNaming', {pattern: pattern, sports: 'True'}, function (data) {
                    if (data) {
                        $('#naming_sports_example').text(data + '.ext');
                        $('#naming_sports_example_div').show();
                    } else {
                        $('#naming_sports_example_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {pattern: pattern, sports: 'True'}, function (data) {
                    if (data == "invalid") {
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': 'This pattern is invalid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_sports_pattern').qtip('toggle', true);
                        $('#naming_sports_pattern').css('background-color', '#FFDDDD');
                    } else if (data == "seasonfolders") {
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

            function fill_anime_examples() {
                var pattern = $('#naming_anime_pattern').val();
                var multi = $('#naming_anime_multi_ep :selected').val();
                var anime_type = $('input[name="naming_anime"]:checked').val();

                $.get(srRoot + '/config/postProcessing/testNaming', {pattern: pattern, anime_type: anime_type}, function (data) {
                    if (data) {
                        $('#naming_example_anime').text(data + '.ext');
                        $('#naming_example_anime_div').show();
                    } else {
                        $('#naming_example_anime_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/testNaming', {pattern: pattern, multi: multi, anime_type: anime_type}, function (data) {
                    if (data) {
                        $('#naming_example_multi_anime').text(data + '.ext');
                        $('#naming_example_multi_anime_div').show();
                    } else {
                        $('#naming_example_multi_anime_div').hide();
                    }
                });

                $.get(srRoot + '/config/postProcessing/isNamingValid', {pattern: pattern, multi: multi, anime_type: anime_type}, function (data) {
                    if (data == "invalid") {
                        $('#naming_pattern').qtip('option', {
                            'content.text': 'This pattern is invalid.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFDDDD');
                    } else if (data == "seasonfolders") {
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

            function setup_naming() {
                // if it is a custom selection then show the text box
                if ($('#name_presets :selected').val() == "Custom...") {
                    $('#naming_custom').show();
                } else {
                    $('#naming_custom').hide();
                    $('#naming_pattern').val($('#name_presets :selected').attr('id'));
                }
                fill_examples();
            }

            function setup_abd_naming() {
                // if it is a custom selection then show the text box
                if ($('#name_abd_presets :selected').val() == "Custom...") {
                    $('#naming_abd_custom').show();
                } else {
                    $('#naming_abd_custom').hide();
                    $('#naming_abd_pattern').val($('#name_abd_presets :selected').attr('id'));
                }
                fill_abd_examples();
            }

            function setup_sports_naming() {
                // if it is a custom selection then show the text box
                if ($('#name_sports_presets :selected').val() == "Custom...") {
                    $('#naming_sports_custom').show();
                } else {
                    $('#naming_sports_custom').hide();
                    $('#naming_sports_pattern').val($('#name_sports_presets :selected').attr('id'));
                }
                fill_sports_examples();
            }

            function setup_anime_naming() {
                // if it is a custom selection then show the text box
                if ($('#name_anime_presets :selected').val() == "Custom...") {
                    $('#naming_anime_custom').show();
                } else {
                    $('#naming_anime_custom').hide();
                    $('#naming_anime_pattern').val($('#name_anime_presets :selected').attr('id'));
                }
                fill_anime_examples();
            }

            $('#unpack').on('change', function(){
                if(this.checked) {
                    israr_supported();
                } else {
                    $('#unpack').qtip('toggle', false);
                }
            });

            $('#name_presets').on('change', function(){
                setup_naming();
            });

            $('#name_abd_presets').on('change', function(){
                setup_abd_naming();
            });

            $('#naming_custom_abd').on('change', function(){
                setup_abd_naming();
            });

            $('#name_sports_presets').on('change', function(){
                setup_sports_naming();
            });

            $('#naming_custom_sports').on('change', function(){
                setup_sports_naming();
            });

            $('#name_anime_presets').on('change', function(){
                setup_anime_naming();
            });

            $('#naming_custom_anime').on('change', function(){
                setup_anime_naming();
            });

            $('input[name="naming_anime"]').on('click', function(){
                setup_anime_naming();
            });

            $('#naming_multi_ep').change(fill_examples);
            $('#naming_pattern').focusout(fill_examples);
            $('#naming_pattern').keyup(function () {
                typewatch(function () {
                    fill_examples();
                }, 500);
            });

            $('#naming_anime_multi_ep').change(fill_anime_examples);
            $('#naming_anime_pattern').focusout(fill_anime_examples);
            $('#naming_anime_pattern').keyup(function () {
                typewatch(function () {
                    fill_anime_examples();
                }, 500);
            });

            $('#naming_abd_pattern').focusout(fill_examples);
            $('#naming_abd_pattern').keyup(function () {
                typewatch(function () {
                    fill_abd_examples();
                }, 500);
            });

            $('#naming_sports_pattern').focusout(fill_examples);
            $('#naming_sports_pattern').keyup(function () {
                typewatch(function () {
                    fill_sports_examples();
                }, 500);
            });

            $('#naming_anime_pattern').focusout(fill_examples);
            $('#naming_anime_pattern').keyup(function () {
                typewatch(function () {
                    fill_anime_examples();
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
            setup_naming();
            setup_abd_naming();
            setup_sports_naming();
            setup_anime_naming();

            // -- start of metadata options div toggle code --
            $('#metadataType').on('change keyup', function () {
                $(this).showHideMetadata();
            });

            $.fn.showHideMetadata = function () {
                $('.metadataDiv').each(function () {
                    var targetName = $(this).attr('id');
                    var selectedTarget = $('#metadataType :selected').val();

                    if (selectedTarget == targetName) {
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
                var cur_most = 0;
                var cur_most_provider = '';

                $('.metadataDiv').each(function () {
                    var generator_name = $(this).attr('id');

                    var config_arr = [];
                    var show_metadata = $("#" + generator_name + "_show_metadata").prop('checked');
                    var episode_metadata = $("#" + generator_name + "_episode_metadata").prop('checked');
                    var fanart = $("#" + generator_name + "_fanart").prop('checked');
                    var poster = $("#" + generator_name + "_poster").prop('checked');
                    var banner = $("#" + generator_name + "_banner").prop('checked');
                    var episode_thumbnails = $("#" + generator_name + "_episode_thumbnails").prop('checked');
                    var season_posters = $("#" + generator_name + "_season_posters").prop('checked');
                    var season_banners = $("#" + generator_name + "_season_banners").prop('checked');
                    var season_all_poster = $("#" + generator_name + "_season_all_poster").prop('checked');
                    var season_all_banner = $("#" + generator_name + "_season_all_banner").prop('checked');

                    config_arr.push(show_metadata ? '1' : '0');
                    config_arr.push(episode_metadata ? '1' : '0');
                    config_arr.push(fanart ? '1' : '0');
                    config_arr.push(poster ? '1' : '0');
                    config_arr.push(banner ? '1' : '0');
                    config_arr.push(episode_thumbnails ? '1' : '0');
                    config_arr.push(season_posters ? '1' : '0');
                    config_arr.push(season_banners ? '1' : '0');
                    config_arr.push(season_all_poster ? '1' : '0');
                    config_arr.push(season_all_banner ? '1' : '0');

                    var cur_num = 0;
                    for (var i = 0, len = config_arr.length; i < len; i++) {
                        cur_num += parseInt(config_arr[i]);
                    }
                    if (cur_num > cur_most) {
                        cur_most = cur_num;
                        cur_most_provider = generator_name;
                    }

                    $("#" + generator_name + "_eg_show_metadata").attr('class', show_metadata ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_eg_episode_metadata").attr('class', episode_metadata ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_eg_fanart").attr('class', fanart ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_eg_poster").attr('class', poster ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_eg_banner").attr('class', banner ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_eg_episode_thumbnails").attr('class', episode_thumbnails ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_eg_season_posters").attr('class', season_posters ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_eg_season_banners").attr('class', season_banners ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_eg_season_all_poster").attr('class', season_all_poster ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_eg_season_all_banner").attr('class', season_all_banner ? 'enabled' : 'disabled');
                    $("#" + generator_name + "_data").val(config_arr.join('|'));

                });

                if (cur_most_provider !== '' && first) {
                    $('#metadataType option[value=' + cur_most_provider + ']').attr('selected', 'selected');
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
                    label = ' label',
                    directory = ' directory',
                    client = '',
                    optionPanel = '#options_torrent_blackhole';
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
                $('#test_torrent_result').html(loading);
                var torrent_method = $('#torrent_method :selected').val();
                var torrent_host = $('#torrent_host').val();
                var torrent_username = $('#torrent_username').val();
                var torrent_password = $('#torrent_password').val();

                $.get(srRoot + '/home/testTorrent', {'torrent_method': torrent_method, 'host': torrent_host, 'username': torrent_username, 'password': torrent_password}, function(data){
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
            // controller-wide code
        },
        show: function() {
            // action-specific code
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
