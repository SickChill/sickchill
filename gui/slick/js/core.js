import log from './log';

import {
    getMeta,
    metaToBool,
    notifyModal
} from './utils';

const loading = `<img src="${srRoot}/images/loading16${themeSpinner}.gif" height="16" width="16" />`;

const configSuccess = function() {
    $('.config_submitter').each(function() {
        $(this).removeAttr('disabled');
        $(this).next().remove();
        $(this).show();
    });
    $('.config_submitter_refresh').each(function() {
        $(this).removeAttr('disabled');
        $(this).next().remove();
        $(this).show();
        window.location.href = srRoot + '/config/providers/';
    });
    $('#email_show').trigger('notify');
    $('#prowl_show').trigger('notify');
};

function addSiteMessage(level, tag, message) {
    level = level || 'danger';
    tag = tag || '';
    message = message || '';
    $.post(srRoot + '/ui/set_site_message', {level, tag, message}, siteMessages => {
        const messagesDiv = $('#site-messages');
        if (messagesDiv !== undefined) {
            messagesDiv.empty();
            for (const key in siteMessages) {
                if (siteMessages.hasOwnProperty(key)) {
                    messagesDiv.append('<div class="alert alert-' + siteMessages[key].level + ' upgrade-notification hidden-print" id="site-message-' + key + '" role="alert">' +
                        '<span>' + siteMessages[key].message + '</span><span class="glyphicon glyphicon-check site-message-dismiss pull-right" data-id="' + key + '"/>' +
                        '</div>');
                }
            }
        }
    });

    $('#site-messages').on('click', '.site-message-dismiss', function() {
        const messageID = $(this).data('id');
        $('#site-message-' + messageID).hide();
        $.post(srRoot + '/ui/dismiss-site-message', {index: messageID});
    });
}

function shiftReturn(array) {
    // Performs .shift() on array.
    // Returns the new array
    if (array.length <= 1) {
        return [];
    }
    array.shift();
    return array;
}

const __ = _; // Moves `underscore` to __
_ = function(str) {
    return str;
}; // Temporary (gets replaced)

var SICKRAGE = {
    common: {
        init() {
            (function init() {
                const imgDefer = document.getElementsByTagName('img');
                for (let i = 0; i < imgDefer.length; i++) {
                    if (imgDefer[i].getAttribute('data-src')) {
                        imgDefer[i].setAttribute('src', imgDefer[i].getAttribute('data-src'));
                    }
                }
                if (metaToBool('sickbeard.SICKRAGE_BACKGROUND')) {
                    $.backstretch(srRoot + '/ui/sickrage_background');
                    $('.backstretch').css('opacity', getMeta('sickbeard.FANART_BACKGROUND_OPACITY')).fadeIn('500');
                }
            })();

            addSiteMessage(); // Show existing messages on ready.

            $.confirm.options = {
                confirmButton: 'Yes',
                cancelButton: 'Cancel',
                dialogClass: 'modal-dialog',
                post: false,
                confirm(e) {
                    location.href = e.context.href;
                }
            };

            $('a.shutdown').confirm({
                title: 'Shutdown',
                text: 'Are you sure you want to shutdown SickRage?'
            });

            $('a.restart').confirm({
                title: 'Restart',
                text: 'Are you sure you want to restart SickRage?'
            });

            $('a.removeshow').confirm({
                title: 'Remove Show',
                text: 'Are you sure you want to remove <span class="footerhighlight">' + $('#showtitle').data('showname') +
                    '</span> from the database?<br><br>' +
                    '<input type="checkbox" id="deleteFiles" name="deleteFiles"/>&nbsp;' +
                    '<label for="deleteFiles" class="red-text">Check to delete files as well. IRREVERSIBLE</label>',
                confirm(e) {
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

            $('#config-components').tabs({
                activate(event, ui) {
                    let lastOpenedPanel = $(this).data('lastOpenedPanel');

                    if (!lastOpenedPanel) {
                        lastOpenedPanel = $(ui.oldPanel);
                    }

                    if (!$(this).data('topPositionTab')) {
                        $(this).data('topPositionTab', $(ui.newPanel).position().top);
                    }

                    // Dont use the builtin fx effects. This will fade in/out both tabs, we dont want that
                    // Fadein the new tab yourself
                    $(ui.newPanel).hide().fadeIn(0);

                    if (lastOpenedPanel) {
                        // 1. Show the previous opened tab by removing the jQuery UI class
                        // 2. Make the tab temporary position:absolute so the two tabs will overlap
                        // 3. Set topposition so they will overlap if you go from tab 1 to tab 0
                        // 4. Remove position:absolute after animation
                        lastOpenedPanel
                            .toggleClass('ui-tabs-hide')
                            .css('position', 'absolute')
                            .css('top', $(this).data('topPositionTab') + 'px')
                            .fadeOut(0, function() {
                                $(this).css('position', '');
                            });
                    }

                    // Saving the last tab has been opened
                    $(this).data('lastOpenedPanel', $(ui.newPanel));
                }
            });

            // @TODO Replace this with a real touchscreen check
            // hack alert: if we don't have a touchscreen, and we are already hovering the mouse, then click should link instead of toggle
            if ((navigator.maxTouchPoints || 0) < 2) {
                $('.dropdown-toggle').on('click', function() {
                    const $this = $(this);
                    if ($this.attr('aria-expanded') === 'true') {
                        window.location.href = $this.attr('href');
                    }
                });
            }

            if (metaToBool('sickbeard.FUZZY_DATING')) {
                $.timeago.settings.allowFuture = true;
                $.timeago.settings.strings = {
                    prefixAgo: null,
                    prefixFromNow: 'In ',
                    suffixAgo: 'ago',
                    suffixFromNow: '',
                    seconds: 'less than a minute',
                    minute: 'about a minute',
                    minutes: '%d minutes',
                    hour: 'an hour',
                    hours: '%d hours',
                    day: 'a day',
                    days: '%d days',
                    month: 'a month',
                    months: '%d months',
                    year: 'a year',
                    years: '%d years',
                    wordSeparator: ' ',
                    numbers: []
                };
                $('[datetime]').timeago();
            }

            $(document.body).on('click', 'a[data-no-redirect]', function(e) {
                e.preventDefault();
                $.get($(this).attr('href'));
                return false;
            });

            $(document.body).on('click', '.bulkCheck', function() {
                const bulkCheck = this;
                const whichBulkCheck = $(bulkCheck).attr('id');

                $('.' + whichBulkCheck + ':visible').each(function() {
                    $(this).prop('checked', $(bulkCheck).prop('checked'));
                });
            });

            $('.enabler').each(function() {
                if (!$(this).prop('checked')) {
                    $('#content_' + $(this).attr('id')).hide();
                }
            });

            $('.enabler').on('change', function() {
                if ($(this).prop('checked')) {
                    $('#content_' + $(this).attr('id')).fadeIn('fast', 'linear');
                } else {
                    $('#content_' + $(this).attr('id')).fadeOut('fast', 'linear');
                }
            });
        },
        QualityChooser: {
            setFromPresets(preset) {
                // @TODO: Sometimes when switching too fast between presets,
                // it stops updating the selection on #anyQualities
                if (parseInt(preset, 10) === 0) {
                    $('#customQuality').show();
                    return;
                }
                $('#customQuality').hide();

                $('#anyQualities').find('option').each(function() {
                    const result = preset & $(this).val();
                    $(this).attr('selected', result > 0 ? 'selected' : false);
                });

                $('#bestQualities').find('option').each(function() {
                    const result = preset & ($(this).val() << 16);
                    $(this).attr('selected', result > 0 ? 'selected' : false);
                });
            },
            init() {
                const selfObj = this;
                const qualityPresets = $('#qualityPreset');

                qualityPresets.on('change', () => {
                    selfObj.setFromPresets(qualityPresets.find(':selected').val());
                });

                selfObj.setFromPresets(qualityPresets.find(':selected').val());
            }
        },
        updateBlackWhiteList(showName) {
            $('#white').children().remove();
            $('#black').children().remove();
            $('#pool').children().remove();

            if ($('#anime').prop('checked')) {
                $('#blackwhitelist').show();
                if (showName) {
                    $.getJSON(srRoot + '/home/fetch_releasegroups', {
                        show_name: showName // eslint-disable-line camelcase
                    }, data => {
                        if (data.result === 'success') {
                            $.each(data.groups, (i, group) => {
                                const option = $('<option>');
                                option.attr('value', group.name);
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
    },
    config: {
        init() {
            $('#config-components').tabs();

            $('.viewIf').on('click', function() {
                if ($(this).prop('checked')) {
                    $('.hide_if_' + $(this).attr('id')).css('display', 'none');
                    $('.show_if_' + $(this).attr('id')).fadeIn('fast', 'linear');
                } else {
                    $('.show_if_' + $(this).attr('id')).css('display', 'none');
                    $('.hide_if_' + $(this).attr('id')).fadeIn('fast', 'linear');
                }
            });

            $('.datePresets').on('click', function() {
                let def = $('#date_presets').val();
                if ($(this).prop('checked') && def === '%x') {
                    def = '%a, %b %d, %Y';
                    $('#date_use_system_default').html('1');
                } else if (!$(this).prop('checked') && $('#date_use_system_default').html() === '1') {
                    def = '%x';
                }

                $('#date_presets').attr('name', 'date_preset_old');
                $('#date_presets').attr('id', 'date_presets_old');

                $('#date_presets_na').attr('name', 'date_preset');
                $('#date_presets_na').attr('id', 'date_presets');

                $('#date_presets_old').attr('name', 'date_preset_na');
                $('#date_presets_old').attr('id', 'date_presets_na');

                if (def) {
                    $('#date_presets').val(def);
                }
            });

            // Bind 'myForm' and provide a simple callback function
            $('#configForm').ajaxForm({
                beforeSubmit() {
                    $('.config_submitter .config_submitter_refresh').each(function() {
                        $(this).attr('disabled', 'disabled');
                        $(this).after('<span><img src="' + srRoot + '/images/loading16' + themeSpinner + '.gif"> Saving...</span>');
                        $(this).hide();
                    });
                },
                success() {
                    setTimeout(() => {
                        'use strict';
                        configSuccess();
                    }, 2000);
                }
            });

            $('#api_key').on('click', () => {
                $('#api_key').select();
            });

            $('#generate_new_apikey').on('click', () => {
                $.get(srRoot + '/config/general/generateApiKey', data => {
                    if (data.error !== undefined) {
                        notifyModal(data.error);
                        return;
                    }
                    $('#api_key').val(data);
                });
            });

            $('#branchCheckout').on('click', () => {
                const url = srRoot + '/home/branchCheckout?branch=' + $('#branchVersion').val();
                const checkDBversion = srRoot + '/home/getDBcompare';
                $.getJSON(checkDBversion, data => {
                    if (data.status === 'success') {
                        if (data.message === 'downgrade') {
                            notifyModal('Can\'t switch branch as this will result in a database downgrade.');
                        } else {
                            let doUpgrade = true;
                            if (data.message === 'upgrade') {
                                doUpgrade = confirm('Changing branch will upgrade your database.\nYou won\'t be able to downgrade afterward.\nDo you want to continue?');
                            }
                            if (doUpgrade) {
                                window.location.href = url;
                            }
                        }
                    }
                });
            });

            // GitHub Auth Types
            function setupGithubAuthTypes() {
                const selected = parseInt($('input[name="git_auth_type"]').filter(':checked').val(), 10);

                $('div[name="content_github_auth_type"]').each(function(index) {
                    if (index === selected) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            }

            setupGithubAuthTypes();

            $('input[name="git_auth_type"]').on('click', () => {
                setupGithubAuthTypes();
            });

            $('#git_token').on('click', () => {
                $('#git_token').select();
            });

            $('#create_access_token').on('click', () => {
                notifyModal(
                    '<p>Copy the generated token and paste it in the token input box.</p>' +
                    '<p><a href="' + anonURL + 'https://github.com/settings/tokens/new?description=SickRage&scopes=user,gist,public_repo" target="_blank">' +
                    '<input class="btn" type="button" value="Continue to Github..."></a></p>');
                $('#git_token').select();
            });

            $('#manage_tokens').on('click', () => {
                window.open(anonURL + 'https://github.com/settings/tokens', '_blank');
            });
        },
        index() {
            $('#log_dir').fileBrowser({title: _('Select log file folder location')});
            $('#sickrage_background_path').fileBrowser({title: _('Select Background Image'), key: 'sickrage_background_path', includeFiles: 1, fileTypes: ['images']});
            $('#custom_css_path').fileBrowser({title: _('Select CSS file'), key: 'custom_css_path', includeFiles: 1, fileTypes: ['css']});
        },
        backupRestore() {
            $('#Backup').on('click', () => {
                $('#Backup').attr('disabled', true);
                $('#Backup-result').html(loading);
                const backupDir = $('#backupDir').val();
                $.get(srRoot + '/config/backuprestore/backup', {backupDir})
                    .done(data => {
                        $('#Backup-result').html(data);
                        $('#Backup').attr('disabled', false);
                    });
            });
            $('#Restore').on('click', () => {
                $('#Restore').attr('disabled', true);
                $('#Restore-result').html(loading);
                const backupFile = $('#backupFile').val();
                $.post(srRoot + '/config/backuprestore/restore', {backupFile})
                    .done(data => {
                        $('#Restore-result').html(data);
                        $('#Restore').attr('disabled', false);
                    });
            });

            $('#backupDir').fileBrowser({title: _('Select backup folder to save to'), key: 'backupPath'});
            $('#backupFile').fileBrowser({title: _('Select backup files to restore'), key: 'backupFile', includeFiles: 1});
            $('#config-components').tabs();
        },
        notifications() {
            $('#testGrowl').on('click', function() {
                const growl = {};
                growl.host = $.trim($('#growl_host').val());
                growl.password = $.trim($('#growl_password').val());
                if (!growl.host) {
                    $('#testGrowl-result').html(_('Please fill out the necessary fields above.'));
                    $('#growl_host').addClass('warning');
                    return;
                }
                $('#growl_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testGrowl-result').html(loading);
                $.get(srRoot + '/home/testGrowl', {
                    host: growl.host,
                    password: growl.password
                }).done(data => {
                    $('#testGrowl-result').html(data);
                    $('#testGrowl').prop('disabled', false);
                });
            });

            $('#testProwl').on('click', function() {
                const prowl = {};
                prowl.api = $.trim($('#prowl_api').val());
                prowl.priority = $('#prowl_priority').val();
                if (!prowl.api) {
                    $('#testProwl-result').html(_('Please fill out the necessary fields above.'));
                    $('#prowl_api').addClass('warning');
                    return;
                }
                $('#prowl_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testProwl-result').html(loading);
                $.get(srRoot + '/home/testProwl', {
                    prowl_api: prowl.api,
                    prowl_priority: prowl.priority
                }).done(data => {
                    $('#testProwl-result').html(data);
                    $('#testProwl').prop('disabled', false);
                });
            });

            $('#testKODI').on('click', function() {
                const kodi = {};
                kodi.host = $.trim($('#kodi_host').val());
                kodi.username = $.trim($('#kodi_username').val());
                kodi.password = $.trim($('#kodi_password').val());
                if (!kodi.host) {
                    $('#testKODI-result').html(_('Please fill out the necessary fields above.'));
                    $('#kodi_host').addClass('warning');
                    return;
                }
                $('#kodi_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testKODI-result').html(loading);
                $.get(srRoot + '/home/testKODI', {
                    host: kodi.host,
                    username: kodi.username,
                    password: kodi.password
                }).done(data => {
                    $('#testKODI-result').html(data);
                    $('#testKODI').prop('disabled', false);
                });
            });

            $('#testPHT').on('click', function() {
                const plex = {};
                plex.client = {};
                plex.client.host = $.trim($('#plex_client_host').val());
                plex.client.username = $.trim($('#plex_client_username').val());
                plex.client.password = $.trim($('#plex_client_password').val());
                if (!plex.client.host) {
                    $('#testPHT-result').html(_('Please fill out the necessary fields above.'));
                    $('#plex_client_host').addClass('warning');
                    return;
                }
                $('#plex_client_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPHT-result').html(loading);
                $.get(srRoot + '/home/testPHT', {
                    host: plex.client.host,
                    username: plex.client.username,
                    password: plex.client.password
                }).done(data => {
                    $('#testPHT-result').html(data);
                    $('#testPHT').prop('disabled', false);
                });
            });

            $('#testPMS').on('click', function() {
                const plex = {};
                plex.server = {};
                plex.server.host = $.trim($('#plex_server_host').val());
                plex.server.username = $.trim($('#plex_server_username').val());
                plex.server.password = $.trim($('#plex_server_password').val());
                plex.server.token = $.trim($('#plex_server_token').val());
                if (!plex.server.host) {
                    $('#testPMS-result').html(_('Please fill out the necessary fields above.'));
                    $('#plex_server_host').addClass('warning');
                    return;
                }
                $('#plex_server_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPMS-result').html(loading);
                $.get(srRoot + '/home/testPMS', {
                    host: plex.server.host,
                    username: plex.server.username,
                    password: plex.server.password,
                    plex_server_token: plex.server.token
                }).done(data => {
                    $('#testPMS-result').html(data);
                    $('#testPMS').prop('disabled', false);
                });
            });

            $('#testEMBY').on('click', function() {
                const emby = {};
                emby.host = $('#emby_host').val();
                emby.apikey = $('#emby_apikey').val();
                if (!emby.host || !emby.apikey) {
                    $('#testEMBY-result').html(_('Please fill out the necessary fields above.'));
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
                    host: emby.host,
                    emby_apikey: emby.apikey
                }).done(data => {
                    $('#testEMBY-result').html(data);
                    $('#testEMBY').prop('disabled', false);
                });
            });

            $('#testBoxcar2').on('click', function() {
                const boxcar2 = {};
                boxcar2.accesstoken = $.trim($('#boxcar2_accesstoken').val());
                if (!boxcar2.accesstoken) {
                    $('#testBoxcar2-result').html(_('Please fill out the necessary fields above.'));
                    $('#boxcar2_accesstoken').addClass('warning');
                    return;
                }
                $('#boxcar2_accesstoken').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testBoxcar2-result').html(loading);
                $.get(srRoot + '/home/testBoxcar2', {
                    accesstoken: boxcar2.accesstoken
                }).done(data => {
                    $('#testBoxcar2-result').html(data);
                    $('#testBoxcar2').prop('disabled', false);
                });
            });

            $('#testPushover').on('click', function() {
                const pushover = {};
                pushover.userkey = $('#pushover_userkey').val();
                pushover.apikey = $('#pushover_apikey').val();
                if (!pushover.userkey || !pushover.apikey) {
                    $('#testPushover-result').html(_('Please fill out the necessary fields above.'));
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
                    userKey: pushover.userkey,
                    apiKey: pushover.apikey
                }).done(data => {
                    $('#testPushover-result').html(data);
                    $('#testPushover').prop('disabled', false);
                });
            });

            $('#testLibnotify').on('click', () => {
                $('#testLibnotify-result').html(loading);
                $.get(srRoot + '/home/testLibnotify', data => {
                    $('#testLibnotify-result').html(data);
                });
            });

            $('#twitterStep1').on('click', () => {
                $('#testTwitter-result').html(loading);
                $.get(srRoot + '/home/twitterStep1', data => {
                    window.open(data);
                }).done(() => {
                    $('#testTwitter-result').html(_('<b>Step 1:</b> Confirm Authorization'));
                });
            });

            $('#twitterStep2').on('click', () => {
                const twitter = {};
                twitter.key = $.trim($('#twitter_key').val());
                if (!twitter.key) {
                    $('#testTwitter-result').html(_('Please fill out the necessary fields above.'));
                    $('#twitter_key').addClass('warning');
                    return;
                }
                $('#twitter_key').removeClass('warning');
                $('#testTwitter-result').html(loading);
                $.get(srRoot + '/home/twitterStep2', {
                    key: twitter.key
                }, data => {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#testTwitter').on('click', () => {
                $.post(srRoot + '/home/testTwitter', data => {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#testTwilio').on('click', () => {
                $('#testTwilio').addClass('disabled');
                $.post(srRoot + '/home/testTwilio', data => {
                    $('#testTwilio-result').html(data);
                }).always(() => {
                    $('#testTwilio').removeClass('disabled');
                });
            });

            $('#testSlack').on('click', () => {
                $.post(srRoot + '/home/testSlack', data => {
                    $('#testSlack-result').html(data);
                });
            });

            $('#testDiscord').on('click', () => {
                $.get(srRoot + '/home/testDiscord', data => {
                    $('#testDiscord-result').html(data);
                });
            });

            $('#settingsNMJ').on('click', () => {
                const nmj = {};
                if (!$('#nmj_host').val()) {
                    $('#nmj_host').focus();
                    notifyModal('Please fill in the Popcorn IP address');
                    return;
                }
                $('#testNMJ-result').html(loading);
                nmj.host = $('#nmj_host').val();

                $.post(srRoot + '/home/settingsNMJ', {host: nmj.host}, data => {
                    if (data === null) {
                        $('#nmj_database').removeAttr('readonly');
                        $('#nmj_mount').removeAttr('readonly');
                    }
                    const JSONData = $.parseJSON(data);
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

            $('#testNMJ').on('click', function() {
                const nmj = {};
                nmj.host = $.trim($('#nmj_host').val());
                nmj.database = $('#nmj_database').val();
                nmj.mount = $('#nmj_mount').val();
                if (!nmj.host) {
                    $('#testNMJ-result').html(_('Please fill out the necessary fields above.'));
                    $('#nmj_host').addClass('warning');
                    return;
                }
                $('#nmj_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testNMJ-result').html(loading);
                $.post(srRoot + '/home/testNMJ', {
                    host: nmj.host,
                    database: nmj.database,
                    mount: nmj.mount
                }).done(data => {
                    $('#testNMJ-result').html(data);
                    $('#testNMJ').prop('disabled', false);
                });
            });

            $('#settingsNMJv2').on('click', () => {
                const nmjv2 = {};
                if (!$('#nmjv2_host').val()) {
                    $('#nmjv2_host').focus();
                    notifyModal('Please fill in the Popcorn IP address', 'modal');
                    return;
                }
                $('#testNMJv2-result').html(loading);
                nmjv2.host = $('#nmjv2_host').val();
                nmjv2.dbloc = '';
                const radios = document.getElementsByName('nmjv2_dbloc');
                for (let i = 0, len = radios.length; i < len; i++) {
                    if (radios[i].checked) {
                        nmjv2.dbloc = radios[i].value;
                        break;
                    }
                }

                nmjv2.dbinstance = $('#NMJv2db_instance').val();
                $.post(srRoot + '/home/settingsNMJv2', {
                    host: nmjv2.host,
                    dbloc: nmjv2.dbloc,
                    instance: nmjv2.dbinstance
                }, data => {
                    if (data === null) {
                        $('#nmjv2_database').removeAttr('readonly');
                    }
                    const JSONData = $.parseJSON(data);
                    $('#testNMJv2-result').html(JSONData.message);
                    $('#nmjv2_database').val(JSONData.database);

                    if (JSONData.database) {
                        $('#nmjv2_database').attr('readonly', true);
                    } else {
                        $('#nmjv2_database').removeAttr('readonly');
                    }
                });
            });

            $('#testNMJv2').on('click', function() {
                const nmjv2 = {};
                nmjv2.host = $.trim($('#nmjv2_host').val());
                if (!nmjv2.host) {
                    $('#testNMJv2-result').html(_('Please fill out the necessary fields above.'));
                    $('#nmjv2_host').addClass('warning');
                    return;
                }
                $('#nmjv2_host').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testNMJv2-result').html(loading);
                $.post(srRoot + '/home/testNMJv2', {
                    host: nmjv2.host
                }).done(data => {
                    $('#testNMJv2-result').html(data);
                    $('#testNMJv2').prop('disabled', false);
                });
            });

            $('#testFreeMobile').on('click', function() {
                const freemobile = {};
                freemobile.id = $.trim($('#freemobile_id').val());
                freemobile.apikey = $.trim($('#freemobile_apikey').val());
                if (!freemobile.id || !freemobile.apikey) {
                    $('#testFreeMobile-result').html(_('Please fill out the necessary fields above.'));
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
                $.post(srRoot + '/home/testFreeMobile', {
                    freemobile_id: freemobile.id,
                    freemobile_apikey: freemobile.apikey
                }).done(data => {
                    $('#testFreeMobile-result').html(data);
                    $('#testFreeMobile').prop('disabled', false);
                });
            });

            $('#testTelegram').on('click', function() {
                const telegram = {};
                telegram.id = $.trim($('#telegram_id').val());
                telegram.apikey = $.trim($('#telegram_apikey').val());
                if (!telegram.id || !telegram.apikey) {
                    $('#testTelegram-result').html(_('Please fill out the necessary fields above.'));
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
                $.post(srRoot + '/home/testTelegram', {
                    telegram_id: telegram.id,
                    telegram_apikey: telegram.apikey
                }).done(data => {
                    $('#testTelegram-result').html(data);
                    $('#testTelegram').prop('disabled', false);
                });
            });

            $('#testJoin').on('click', function() {
                const join = {};
                join.id = $.trim($('#join_id').val());
                join.apikey = $.trim($('#join_apikey').val());
                if (!join.id || !join.apikey) {
                    $('#testJoin-result').html(_('Please fill out the necessary fields above.'));
                    if (!join.id) {
                        $('#join_id').addClass('warning');
                    } else {
                        $('#join_id').removeClass('warning');
                    }
                    if (!join.apikey) {
                        $('#join_apikey').addClass('warning');
                    } else {
                        $('#join_apikey').removeClass('warning');
                    }
                    return;
                }
                $('#join_id,#join_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testJoin-result').html(loading);
                $.post(srRoot + '/home/testJoin', {
                    join_id: join.id,
                    join_apikey: join.apikey
                }).done(data => {
                    $('#testJoin-result').html(data);
                    $('#testJoin').prop('disabled', false);
                });
            });

            $('#TraktGetPin').on('click', () => {
                window.open($('#trakt_pin_url').val(), 'popUp', 'toolbar=no, scrollbars=no, resizable=no, top=200, left=200, width=650, height=550');
                $('#trakt_pin').removeClass('hide');
            });

            $('#trakt_pin').on('keyup change', () => {
                if ($('#trakt_pin').val().length !== 0) {
                    $('#TraktGetPin').addClass('hide');
                    $('#authTrakt').removeClass('hide');
                } else {
                    $('#TraktGetPin').removeClass('hide');
                    $('#authTrakt').addClass('hide');
                }
            });

            $('#authTrakt').on('click', () => {
                const trakt = {};
                trakt.pin = $('#trakt_pin').val();
                if (trakt.pin.length !== 0) {
                    $.post(srRoot + '/home/getTraktToken', {
                        trakt_pin: trakt.pin
                    }).done(data => {
                        $('#testTrakt-result').html(data);
                        $('#authTrakt').addClass('hide');
                        $('#trakt_pin').addClass('hide');
                        $('#TraktGetPin').addClass('hide');
                    });
                }
            });

            $('#testTrakt').on('click', function() {
                const trakt = {};
                trakt.username = $.trim($('#trakt_username').val());
                trakt.trendingBlacklist = $.trim($('#trakt_blacklist_name').val());
                if (!trakt.username) {
                    $('#testTrakt-result').html(_('Please fill out the necessary fields above.'));
                    if (!trakt.username) {
                        $('#trakt_username').addClass('warning');
                    } else {
                        $('#trakt_username').removeClass('warning');
                    }
                    return;
                }

                if (/\s/g.test(trakt.trendingBlacklist)) {
                    $('#testTrakt-result').html(_('Check blacklist name; the value needs to be a trakt slug'));
                    $('#trakt_blacklist_name').addClass('warning');
                    return;
                }
                $('#trakt_username').removeClass('warning');
                $('#trakt_blacklist_name').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testTrakt-result').html(loading);
                $.post(srRoot + '/home/testTrakt', {
                    username: trakt.username,
                    blacklist_name: trakt.trendingBlacklist
                }).done(data => {
                    $('#testTrakt-result').html(data);
                    $('#testTrakt').prop('disabled', false);
                });
            });

            $('#testEmail').on('click', () => {
                let status, host, port, tls, from, user, pwd, err, to;
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
                        status.html('<p style="color: red;">' + _('You must provide a recipient email address!') + '</p>');
                    } else {
                        $.post(srRoot + '/home/testEmail', {
                            host,
                            port,
                            smtp_from: from, // @TODO we shouldn't be using any reserved words like "from"
                            use_tls: tls,
                            user,
                            pwd,
                            to
                        }, msg => {
                            $('#testEmail-result').html(msg);
                        });
                    }
                }
            });

            $('#testNMA').on('click', function() {
                const nma = {};
                nma.api = $.trim($('#nma_api').val());
                nma.priority = $('#nma_priority').val();
                if (!nma.api) {
                    $('#testNMA-result').html(_('Please fill out the necessary fields above.'));
                    $('#nma_api').addClass('warning');
                    return;
                }
                $('#nma_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testNMA-result').html(loading);
                $.post(srRoot + '/home/testNMA', {
                    nma_api: nma.api,
                    nma_priority: nma.priority
                }).done(data => {
                    $('#testNMA-result').html(data);
                    $('#testNMA').prop('disabled', false);
                });
            });

            $('#testPushalot').on('click', function() {
                const pushalot = {};
                pushalot.authToken = $.trim($('#pushalot_authorizationtoken').val());
                if (!pushalot.authToken) {
                    $('#testPushalot-result').html(_('Please fill out the necessary fields above.'));
                    $('#pushalot_authorizationtoken').addClass('warning');
                    return;
                }
                $('#pushalot_authorizationtoken').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPushalot-result').html(loading);
                $.post(srRoot + '/home/testPushalot', {
                    authorizationToken: pushalot.authToken
                }).done(data => {
                    $('#testPushalot-result').html(data);
                    $('#testPushalot').prop('disabled', false);
                });
            });

            $('#testPushbullet').on('click', function() {
                const pushbullet = {};
                pushbullet.api = $.trim($('#pushbullet_api').val());
                if (!pushbullet.api) {
                    $('#testPushbullet-result').html(_('Please fill out the necessary fields above.'));
                    $('#pushbullet_api').addClass('warning');
                    return;
                }
                $('#pushbullet_api').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPushbullet-result').html(loading);
                $.post(srRoot + '/home/testPushbullet', {
                    api: pushbullet.api
                }).done(data => {
                    $('#testPushbullet-result').html(data);
                    $('#testPushbullet').prop('disabled', false);
                });
            });

            function getPushbulletDevices(msg) {
                const pushbullet = {};
                pushbullet.api = $('#pushbullet_api').val();

                if (msg) {
                    $('#testPushbullet-result').html(loading);
                }

                if (!pushbullet.api) {
                    $('#testPushbullet-result').html(_('You didn\'t supply a Pushbullet api key'));
                    $('#pushbullet_api').focus();
                    return false;
                }

                $.post(srRoot + '/home/getPushbulletDevices', {
                    api: pushbullet.api
                }, data => {
                    pushbullet.devices = $.parseJSON(data).devices;
                    pushbullet.currentDevice = $('#pushbullet_device').val();
                    $('#pushbullet_device_list').html('');
                    for (let i = 0, len = pushbullet.devices.length; i < len; i++) {
                        if (pushbullet.devices[i].active === true) {
                            if (pushbullet.currentDevice === pushbullet.devices[i].iden) {
                                $('#pushbullet_device_list').append('<option value="' + pushbullet.devices[i].iden + '" selected>' + pushbullet.devices[i].nickname + '</option>');
                            } else {
                                $('#pushbullet_device_list').append('<option value="' + pushbullet.devices[i].iden + '">' + pushbullet.devices[i].nickname + '</option>');
                            }
                        }
                    }
                    $('#pushbullet_device_list').prepend('<option value="" ' + (pushbullet.currentDevice === '' ? 'selected' : '') + '>All devices</option>');
                    if (msg) {
                        $('#testPushbullet-result').html(msg);
                    }
                });

                $('#pushbullet_device_list').on('change', () => {
                    $('#pushbullet_device').val($('#pushbullet_device_list').val());
                    $('#testPushbullet-result').html(_('Don\'t forget to save your new pushbullet settings.'));
                });

                $.post(srRoot + '/home/getPushbulletChannels', {
                    api: pushbullet.api
                }, data => {
                    pushbullet.channels = $.parseJSON(data).channels;
                    pushbullet.currentChannel = $('#pushbullet_channel').val();
                    $('#pushbullet_channel_list').html('');
                    if (pushbullet.channels.length > 0) {
                        for (let i = 0, len = pushbullet.channels.length; i < len; i++) {
                            if (pushbullet.channels[i].active === true) {
                                $('#pushbullet_channel_list').append('<option value="' + pushbullet.channels[i].tag + '" selected>' + pushbullet.channels[i].name + '</option>');
                            } else {
                                $('#pushbullet_channel_list').append('<option value="' + pushbullet.channels[i].tag + '">' + pushbullet.channels[i].name + '</option>');
                            }
                        }
                        $('#pushbullet_channel_list').prepend('<option value="" ' + (pushbullet.currentChannel ? 'selected' : '') + '>No Channel</option>');
                        $('#pushbullet_channel_list').prop('disabled', false);
                    } else {
                        $('#pushbullet_channel_list').prepend('<option value>No Channels</option>');
                        $('#pushbullet_channel_list').prop('disabled', true);
                    }
                    if (msg) {
                        $('#testPushbullet-result').html(msg);
                    }

                    $('#pushbullet_channel_list').on('change', () => {
                        $('#pushbullet_channel').val($('#pushbullet_channel_list').val());
                        $('#testPushbullet-result').html(_('Don\'t forget to save your new pushbullet settings.'));
                    });
                });
            }

            $('#getPushbulletDevices').on('click', () => {
                getPushbulletDevices('Device list updated. Please choose a device to push to.');
            });

            // We have to call this function on dom ready to create the devices select
            getPushbulletDevices();

            $('#email_show').on('change', () => {
                const key = parseInt($('#email_show').val(), 10);
                $.getJSON(srRoot + '/home/loadShowNotifyLists', notifyData => {
                    if (notifyData._size > 0) {
                        $('#email_show_list').val(key >= 0 ? notifyData[key.toString()].list : '');
                    }
                });
            });
            $('#prowl_show').on('change', () => {
                const key = parseInt($('#prowl_show').val(), 10);
                $.getJSON(srRoot + '/home/loadShowNotifyLists', notifyData => {
                    if (notifyData._size > 0) {
                        $('#prowl_show_list').val(key >= 0 ? notifyData[key.toString()].prowl_notify_list : '');
                    }
                });
            });

            function loadShowNotifyLists() {
                $.getJSON(srRoot + '/home/loadShowNotifyLists', list => {
                    let html, s;
                    if (list._size === 0) {
                        return;
                    }

                    // Convert the 'list' object to a js array of objects so that we can sort it
                    const _list = [];
                    for (s in list) {
                        if (s.charAt(0) !== '_') {
                            _list.push(list[s]);
                        }
                    }
                    const sortedList = _list.sort((a, b) => {
                        if (a.name < b.name) {
                            return -1;
                        }
                        if (a.name > b.name) {
                            return 1;
                        }
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
            $('#email_show').on('notify', () => {
                loadShowNotifyLists();
            });
            $('#prowl_show').on('notify', () => {
                loadShowNotifyLists();
            });

            $('#email_show_save').on('click', () => {
                $.post(srRoot + '/home/saveShowNotifyList', {
                    show: $('#email_show').val(),
                    emails: $('#email_show_list').val()
                }, () => {
                    // Reload the per show notify lists to reflect changes
                    loadShowNotifyLists();
                });
            });
            $('#prowl_show_save').on('click', () => {
                $.post(srRoot + '/home/saveShowNotifyList', {
                    show: $('#prowl_show').val(),
                    prowlAPIs: $('#prowl_show_list').val()
                }, () => {
                    // Reload the per show notify lists to reflect changes
                    loadShowNotifyLists();
                });
            });

            // Show instructions for plex when enabled
            $('#use_plex_server').on('click', function() {
                if ($(this).is(':checked')) {
                    $('.plexinfo').removeClass('hide');
                } else {
                    $('.plexinfo').addClass('hide');
                }
            });
        },
        postProcessing() {
            $('#config-components').tabs();
            $('#tv_download_dir').fileBrowser({title: _('Select TV Download Directory')});
            $('#unpack_dir').fileBrowser({title: _('Select Unpack Directory')});

            // http://stackoverflow.com/questions/2219924/idiomatic-jquery-delayed-event-only-after-a-short-pause-in-typing-e-g-timew
            const typewatch = (function() {
                let timer = 0;
                return function(callback, ms) {
                    clearTimeout(timer);
                    timer = setTimeout(callback, ms);
                };
            })();

            function isRarSupported() {
                $.post(srRoot + '/config/postProcessing/isRarSupported', data => {
                    if (data !== 'supported') {
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
                const example = {};

                example.pattern = $('#naming_pattern').val();
                example.multi = $('#naming_multi_ep :selected').val();
                example.animeType = $('input[name="naming_anime"]:checked').val();

                $.post(srRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                    anime_type: 3
                }, data => {
                    if (data) {
                        $('#naming_example').text(data + '.ext');
                        $('#naming_example_div').show();
                    } else {
                        $('#naming_example_div').hide();
                    }
                });

                $.post(srRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: 3
                }, data => {
                    if (data) {
                        $('#naming_example_multi').text(data + '.ext');
                        $('#naming_example_multi_div').show();
                    } else {
                        $('#naming_example_multi_div').hide();
                    }
                });

                $.post(srRoot + '/config/postProcessing/isNamingValid', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: example.animeType
                }, data => {
                    let info;
                    if (data === 'invalid') {
                        info = _('This pattern is invalid.');
                        $('#naming_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFDDDD');
                    } else if (data === 'seasonfolders') {
                        info = _('This pattern would be invalid without the folders, using it will force "Season Folders" on for all shows.');
                        $('#naming_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFFFDD');
                    } else {
                        info = _('This pattern is valid.');
                        $('#naming_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                        });
                        $('#naming_pattern').qtip('toggle', false);
                        $('#naming_pattern').css('background-color', '#FFFFFF');
                    }
                    $('#naming_pattern').attr('title', info);
                });
            }

            function fillAbdExamples() {
                const pattern = $('#naming_abd_pattern').val();

                $.post(srRoot + '/config/postProcessing/testNaming', {
                    pattern,
                    abd: 'True'
                }, data => {
                    if (data) {
                        $('#naming_abd_example').text(data + '.ext');
                        $('#naming_abd_example_div').show();
                    } else {
                        $('#naming_abd_example_div').hide();
                    }
                });

                $.post(srRoot + '/config/postProcessing/isNamingValid', {
                    pattern,
                    abd: 'True'
                }, data => {
                    let info;
                    if (data === 'invalid') {
                        info = _('This pattern is invalid.');
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_abd_pattern').qtip('toggle', true);
                        $('#naming_abd_pattern').css('background-color', '#FFDDDD');
                    } else if (data === 'seasonfolders') {
                        info = _('This pattern would be invalid without the folders, using it will force "Season Folders" on for all shows.');
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_abd_pattern').qtip('toggle', true);
                        $('#naming_abd_pattern').css('background-color', '#FFFFDD');
                    } else {
                        info = _('This pattern is valid.');
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                        });
                        $('#naming_abd_pattern').qtip('toggle', false);
                        $('#naming_abd_pattern').css('background-color', '#FFFFFF');
                    }
                    $('#naming_abd_pattern').attr('title', info);
                });
            }

            function fillSportsExamples() {
                const pattern = $('#naming_sports_pattern').val();

                $.post(srRoot + '/config/postProcessing/testNaming', {
                    pattern,
                    sports: 'True' // @TODO does this actually need to be a string or can it be a boolean?
                }, data => {
                    if (data) {
                        $('#naming_sports_example').text(data + '.ext');
                        $('#naming_sports_example_div').show();
                    } else {
                        $('#naming_sports_example_div').hide();
                    }
                });

                $.post(srRoot + '/config/postProcessing/isNamingValid', {
                    pattern,
                    sports: 'True' // @TODO does this actually need to be a string or can it be a boolean?
                }, data => {
                    let info;
                    if (data === 'invalid') {
                        info = _('This pattern is invalid.');
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_sports_pattern').qtip('toggle', true);
                        $('#naming_sports_pattern').css('background-color', '#FFDDDD');
                    } else if (data === 'seasonfolders') {
                        info = _('This pattern would be invalid without the folders, using it will force "Season Folders" on for all shows.');
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_sports_pattern').qtip('toggle', true);
                        $('#naming_sports_pattern').css('background-color', '#FFFFDD');
                    } else {
                        info = _('This pattern is valid.');
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                        });
                        $('#naming_sports_pattern').qtip('toggle', false);
                        $('#naming_sports_pattern').css('background-color', '#FFFFFF');
                    }
                    $('#naming_sports_pattern').attr('title', info);
                });
            }

            function fillAnimeExamples() {
                const example = {};
                example.pattern = $('#naming_anime_pattern').val();
                example.multi = $('#naming_anime_multi_ep :selected').val();
                example.animeType = $('input[name="naming_anime"]:checked').val();

                $.post(srRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                    anime_type: example.animeType
                }, data => {
                    if (data) {
                        $('#naming_example_anime').text(data + '.ext');
                        $('#naming_example_anime_div').show();
                    } else {
                        $('#naming_example_anime_div').hide();
                    }
                });

                $.post(srRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: example.animeType
                }, data => {
                    if (data) {
                        $('#naming_example_multi_anime').text(data + '.ext');
                        $('#naming_example_multi_anime_div').show();
                    } else {
                        $('#naming_example_multi_anime_div').hide();
                    }
                });

                $.post(srRoot + '/config/postProcessing/isNamingValid', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: example.animeType
                }, data => {
                    let info;
                    if (data === 'invalid') {
                        info = _('This pattern is invalid.');
                        $('#naming_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFDDDD');
                    } else if (data === 'seasonfolders') {
                        info = _('This pattern would be invalid without the folders, using it will force "Season Folders" on for all shows.');
                        $('#naming_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red'
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFFFDD');
                    } else {
                        info = _('This pattern is valid.');
                        $('#naming_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green'
                        });
                        $('#naming_pattern').qtip('toggle', false);
                        $('#naming_pattern').css('background-color', '#FFFFFF');
                    }
                    $('#naming_pattern').attr('title', info);
                });
            }

            // @TODO all of these setup funcitons should be able to be rolled into a generic jQuery function

            function setupNaming() {
                // If it is a custom selection then show the text box
                if ($('#name_presets :selected').val().toLowerCase() === 'custom...') {
                    $('#naming_custom').show();
                } else {
                    $('#naming_custom').hide();
                    $('#naming_pattern').val($('#name_presets :selected').attr('id'));
                }
                fillExamples();
            }

            function setupAbdNaming() {
                // If it is a custom selection then show the text box
                if ($('#name_abd_presets :selected').val().toLowerCase() === 'custom...') {
                    $('#naming_abd_custom').show();
                } else {
                    $('#naming_abd_custom').hide();
                    $('#naming_abd_pattern').val($('#name_abd_presets :selected').attr('id'));
                }
                fillAbdExamples();
            }

            function setupSportsNaming() {
                // If it is a custom selection then show the text box
                if ($('#name_sports_presets :selected').val().toLowerCase() === 'custom...') {
                    $('#naming_sports_custom').show();
                } else {
                    $('#naming_sports_custom').hide();
                    $('#naming_sports_pattern').val($('#name_sports_presets :selected').attr('id'));
                }
                fillSportsExamples();
            }

            function setupAnimeNaming() {
                // If it is a custom selection then show the text box
                if ($('#name_anime_presets :selected').val().toLowerCase() === 'custom...') {
                    $('#naming_anime_custom').show();
                } else {
                    $('#naming_anime_custom').hide();
                    $('#naming_anime_pattern').val($('#name_anime_presets :selected').attr('id'));
                }
                fillAnimeExamples();
            }

            if (parseInt($('#unpack').val()) !== 1) {
                $('#content_unpack').hide();
            }

            $('#unpack').on('change', function() {
                switch (parseInt(this.value)) {
                    case 0: // Ignore
                    case 2: // Treat as video
                        $('#content_unpack').fadeOut('fast', 'linear');
                        $('#unpack').qtip('toggle', false);
                        break;
                    case 1: // Unpack
                        $('#content_unpack').fadeIn('fast', 'linear');
                        isRarSupported();
                        break;
                }
            });

            // @TODO all of these on change funcitons should be able to be rolled into a generic jQuery function or maybe we could
            //       move all of the setup functions into these handlers?

            $('#name_presets').on('change', () => {
                setupNaming();
            });

            $('#name_abd_presets').on('change', () => {
                setupAbdNaming();
            });

            $('#naming_custom_abd').on('change', () => {
                setupAbdNaming();
            });

            $('#name_sports_presets').on('change', () => {
                setupSportsNaming();
            });

            $('#naming_custom_sports').on('change', () => {
                setupSportsNaming();
            });

            $('#name_anime_presets').on('change', () => {
                setupAnimeNaming();
            });

            $('#naming_custom_anime').on('change', () => {
                setupAnimeNaming();
            });

            $('input[name="naming_anime"]').on('click', () => {
                setupAnimeNaming();
            });

            // @TODO We might be able to change these from typewatch to __.debounce like we've done on the log page
            //       The main reason for doing this would be to use only open source stuff that's still being maintained

            $('#naming_multi_ep').on('change', fillExamples);
            $('#naming_pattern').on('focusout', fillExamples);
            $('#naming_pattern').on('keyup', () => {
                typewatch(() => {
                    fillExamples();
                }, 500);
            });

            $('#naming_anime_multi_ep').on('change', fillAnimeExamples);
            $('#naming_anime_pattern').on('focusout', fillAnimeExamples);
            $('#naming_anime_pattern').on('keyup', () => {
                typewatch(() => {
                    fillAnimeExamples();
                }, 500);
            });

            $('#naming_abd_pattern').on('focusout', fillExamples);
            $('#naming_abd_pattern').on('keyup', () => {
                typewatch(() => {
                    fillAbdExamples();
                }, 500);
            });

            $('#naming_sports_pattern').on('focusout', fillExamples);
            $('#naming_sports_pattern').on('keyup', () => {
                typewatch(() => {
                    fillSportsExamples();
                }, 500);
            });

            $('#naming_anime_pattern').on('focusout', fillExamples);
            $('#naming_anime_pattern').on('keyup', () => {
                typewatch(() => {
                    fillAnimeExamples();
                }, 500);
            });

            $('#show_naming_key').on('click', () => {
                $('#naming_key').toggle();
            });
            $('#show_naming_abd_key').on('click', () => {
                $('#naming_abd_key').toggle();
            });
            $('#show_naming_sports_key').on('click', () => {
                $('#naming_sports_key').toggle();
            });
            $('#show_naming_anime_key').on('click', () => {
                $('#naming_anime_key').toggle();
            });
            $('#do_custom').on('click', () => {
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
            $('#metadataType').on('change keyup', function() {
                $(this).showHideMetadata();
            });

            $.fn.showHideMetadata = function() {
                $('.metadataDiv').each(function() {
                    const targetName = $(this).attr('id');
                    const selectedTarget = $('#metadataType :selected').val();

                    if (selectedTarget === targetName) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            };
            // Initialize to show the div
            $(this).showHideMetadata();
            // -- end of metadata options div toggle code --

            $('.metadata_checkbox').on('click', function() {
                $(this).refreshMetadataConfig(false);
            });

            $.fn.refreshMetadataConfig = function(first) {
                let curMost = 0;
                let curMostProvider = '';

                $('.metadataDiv').each(function() {
                    const generatorName = $(this).attr('id');

                    const configArray = [];
                    const showMetadata = $('#' + generatorName + '_show_metadata').prop('checked');
                    const episodeMetadata = $('#' + generatorName + '_episode_metadata').prop('checked');
                    const fanart = $('#' + generatorName + '_fanart').prop('checked');
                    const poster = $('#' + generatorName + '_poster').prop('checked');
                    const banner = $('#' + generatorName + '_banner').prop('checked');
                    const episodeThumbnails = $('#' + generatorName + '_episode_thumbnails').prop('checked');
                    const seasonPosters = $('#' + generatorName + '_season_posters').prop('checked');
                    const seasonBanners = $('#' + generatorName + '_season_banners').prop('checked');
                    const seasonAllPoster = $('#' + generatorName + '_season_all_poster').prop('checked');
                    const seasonAllBanner = $('#' + generatorName + '_season_all_banner').prop('checked');

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

                    let curNumber = 0;
                    for (let i = 0, len = configArray.length; i < len; i++) {
                        curNumber += parseInt(configArray[i]);
                    }
                    if (curNumber > curMost) {
                        curMost = curNumber;
                        curMostProvider = generatorName;
                    }

                    $('#' + generatorName + '_eg_show_metadata').attr('class', showMetadata ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_eg_episode_metadata').attr('class', episodeMetadata ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_eg_fanart').attr('class', fanart ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_eg_poster').attr('class', poster ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_eg_banner').attr('class', banner ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_eg_episode_thumbnails').attr('class', episodeThumbnails ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_eg_season_posters').attr('class', seasonPosters ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_eg_season_banners').attr('class', seasonBanners ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_eg_season_all_poster').attr('class', seasonAllPoster ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_eg_season_all_banner').attr('class', seasonAllBanner ? 'enabled' : 'disabled');
                    $('#' + generatorName + '_data').val(configArray.join('|'));
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
        search() {
            $('#config-components').tabs();
            $('#nzb_dir').fileBrowser({title: _('Select .nzb black hole/watch location')});
            $('#torrent_dir').fileBrowser({title: _('Select .torrent black hole/watch location')});
            $('#torrent_path').fileBrowser({title: _('Select .torrent download location')});

            $.fn.nzbMethodHandler = function() {
                let selectedProvider = $('#nzb_method :selected').val(),
                    blackholeSettings = '#blackhole_settings',
                    sabnzbdSettings = '#sabnzbd_settings',
                    testSABnzbd = '#testSABnzbd',
                    testSABnzbdResult = '#testSABnzbd_result',
                    nzbgetSettings = '#nzbget_settings',
                    downloadStationSettings = '#download_station_settings',
                    testDSM = '#testDSM',
                    testDSMResult = '#testDSM_result';

                $('#nzb_method_icon').removeClass((index, css) => {
                    return (css.match(/(^|\s)add-client-icon-\S+/g) || []).join(' ');
                });
                $('#nzb_method_icon').addClass('add-client-icon-' + selectedProvider.replace('_', '-'));

                $(blackholeSettings).hide();
                $(sabnzbdSettings).hide();
                $(testSABnzbd).hide();
                $(testSABnzbdResult).hide();
                $(nzbgetSettings).hide();
                $(downloadStationSettings).hide();
                $(testDSM).hide();
                $(testDSMResult).hide();

                if (selectedProvider.toLowerCase() === 'blackhole') {
                    $(blackholeSettings).show();
                } else if (selectedProvider.toLowerCase() === 'nzbget') {
                    $(nzbgetSettings).show();
                } else if (selectedProvider.toLowerCase() === 'download_station') {
                    $(downloadStationSettings).show();
                    $(testDSM).show();
                    $(testDSMResult).show();
                } else {
                    $(sabnzbdSettings).show();
                    $(testSABnzbd).show();
                    $(testSABnzbdResult).show();
                }
            };

            $.torrentMethodHandler = function() {
                $('#options_torrent_clients').hide();
                $('#options_torrent_blackhole').hide();

                let selectedProvider = $('#torrent_method :selected').val(),
                    host = ' host:port',
                    username = ' username',
                    password = ' password',
                    client = '',
                    optionPanel = '#options_torrent_blackhole',
                    rpcurl = ' RPC URL';

                $('#torrent_method_icon').removeClass((index, css) => {
                    return (css.match(/(^|\s)add-client-icon-\S+/g) || []).join(' ');
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
                    $('#torrent_host_option').show();
                    if (selectedProvider.toLowerCase() === 'utorrent') {
                        client = 'uTorrent';
                        $('#torrent_path_option').hide();
                        $('#torrent_seed_time_label').text(_('Minimum seeding time is'));
                        $('#torrent_seed_time_option').show();
                        $('#host_desc_torrent').text(_('URL to your uTorrent client (e.g. http://localhost:8000)'));
                    } else if (selectedProvider.toLowerCase() === 'transmission') {
                        client = 'Transmission';
                        $('#torrent_seed_time_label').text(_('Stop seeding when inactive for'));
                        $('#torrent_seed_time_option').show();
                        $('#torrent_high_bandwidth_option').show();
                        $('#torrent_label_option').hide();
                        $('#torrent_label_anime_option').hide();
                        $('#torrent_rpcurl_option').show();
                        $('#host_desc_torrent').text(_('URL to your Transmission client (e.g. http://localhost:9091)'));
                    } else if (selectedProvider.toLowerCase() === 'deluge') {
                        client = 'Deluge';
                        $('#torrent_verify_cert_option').show();
                        $('#torrent_verify_deluge').show();
                        $('#torrent_verify_rtorrent').hide();
                        $('#label_warning_deluge').show();
                        $('#label_anime_warning_deluge').show();
                        $('#torrent_username_option').hide();
                        $('#torrent_username').prop('value', '');
                        $('#host_desc_torrent').text(_('URL to your Deluge client (e.g. http://localhost:8112)'));
                    } else if (selectedProvider.toLowerCase() === 'deluged') {
                        client = 'Deluge';
                        $('#torrent_verify_cert_option').hide();
                        $('#torrent_verify_deluge').hide();
                        $('#torrent_verify_rtorrent').hide();
                        $('#label_warning_deluge').show();
                        $('#label_anime_warning_deluge').show();
                        $('#torrent_username_option').show();
                        $('#host_desc_torrent').text(_('IP or Hostname of your Deluge Daemon (e.g. scgi://localhost:58846)'));
                    } else if (selectedProvider.toLowerCase() === 'download_station') {
                        client = 'Synology DS';
                        $('#torrent_label_option').hide();
                        $('#torrent_label_anime_option').hide();
                        $('#torrent_paused_option').hide();
                        $('#torrent_path_option').find('.fileBrowser').hide();
                        $('#host_desc_torrent').text(_('URL to your Synology DS client (e.g. http://localhost:5000)'));
                        $('#path_synology').show();
                    } else if (selectedProvider.toLowerCase() === 'rtorrent') {
                        client = 'rTorrent';
                        $('#host_desc_torrent').html(_('URL to your rTorrent client (e.g. scgi://localhost:5000 <br> ' +
                                                        'or https://localhost/rutorrent/plugins/httprpc/action.php)'));
                        $('#torrent_verify_cert_option').show();
                        $('#torrent_verify_deluge').hide();
                        $('#torrent_verify_rtorrent').show();
                        $('#torrent_auth_type_option').show();
                    } else if (selectedProvider.toLowerCase() === 'qbittorrent') {
                        client = 'qbittorrent';
                        $('#torrent_path_option').hide();
                        $('#label_warning_qbittorrent').show();
                        $('#label_anime_warning_qbittorrent').show();
                        $('#host_desc_torrent').text(_('URL to your qBittorrent client (e.g. http://localhost:8080)'));
                    } else if (selectedProvider.toLowerCase() === 'mlnet') {
                        client = 'mlnet';
                        $('#torrent_path_option').hide();
                        $('#torrent_label_option').hide();
                        $('#torrent_verify_cert_option').hide();
                        $('#torrent_verify_deluge').hide();
                        $('#torrent_verify_rtorrent').hide();
                        $('#torrent_label_anime_option').hide();
                        $('#torrent_paused_option').hide();
                        $('#host_desc_torrent').text(_('URL to your MLDonkey (e.g. http://localhost:4080)'));
                    } else if (selectedProvider.toLowerCase() === 'putio') {
                        client = 'putio';
                        $('#torrent_path_option').hide();
                        $('#torrent_label_option').hide();
                        $('#torrent_verify_cert_option').hide();
                        $('#torrent_verify_deluge').hide();
                        $('#torrent_verify_rtorrent').hide();
                        $('#torrent_label_anime_option').hide();
                        $('#torrent_paused_option').hide();
                        $('#torrent_host_option').hide();
                        $('#host_desc_torrent').text(_('URL to your putio client (e.g. http://localhost:8080)'));
                        $('label[for="torrent_password"]').html(
                            '<a href="' + anonURL + 'https://app.put.io/oauth/apps/new" target="_blank">' +
                            _('Create a new OAuth app for put.io') + '</a>');
                        $('#username_title.component-title').text(_('Put.io Parent Folder'));
                        $('#password_title.component-title').text(_('Put.io OAuth Token'));
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

            $('#torrent_host').on('input', () => {
                if ($('#torrent_method :selected').val().toLowerCase() === 'rtorrent') {
                    const hostname = $('#torrent_host').val();
                    const isMatch = hostname.substr(0, 7) === 'scgi://';

                    if (isMatch) {
                        $('#torrent_username_option').hide();
                        $('#torrent_username').prop('value', '');
                        $('#torrent_password_option').hide();
                        $('#torrent_password').prop('value', '');
                        $('#torrent_auth_type_option').hide();
                        $('#torrent_auth_type option[value=none]').attr('selected', 'selected');
                    } else {
                        $('#torrent_username_option').show();
                        $('#torrent_password_option').show();
                        $('#torrent_auth_type_option').show();
                    }
                }
            });

            $('#nzb_method').on('change', $(this).nzbMethodHandler);

            $(this).nzbMethodHandler();

            $('#testSABnzbd').on('click', () => {
                const sab = {};
                $('#testSABnzbd_result').html(loading);
                sab.host = $('#sab_host').val();
                sab.username = $('#sab_username').val();
                sab.password = $('#sab_password').val();
                sab.apiKey = $('#sab_apikey').val();

                $.post(srRoot + '/home/testSABnzbd', {
                    host: sab.host,
                    username: sab.username,
                    password: sab.password,
                    apikey: sab.apiKey
                }, data => {
                    $('#testSABnzbd_result').html(data);
                });
            });

            $('#testDSM').on('click', () => {
                const dsm = {};
                $('#testDSM_result').html(loading);
                dsm.host = $('#syno_dsm_host').val();
                dsm.username = $('#syno_dsm_user').val();
                dsm.password = $('#syno_dsm_pass').val();

                $.post(srRoot + '/home/testDSM', {
                    host: dsm.host,
                    username: dsm.username,
                    password: dsm.password
                }, data => {
                    $('#testDSM_result').html(data);
                });
            });

            $('#torrent_method').on('change', $.torrentMethodHandler);

            $.torrentMethodHandler();

            $('#test_torrent').on('click', () => {
                const torrent = {};
                $('#test_torrent_result').html(loading);
                torrent.method = $('#torrent_method :selected').val();
                torrent.host = $('#torrent_host').val();
                torrent.username = $('#torrent_username').val();
                torrent.password = $('#torrent_password').val();

                $.post(srRoot + '/home/testTorrent', {
                    torrent_method: torrent.method,
                    host: torrent.host,
                    username: torrent.username,
                    password: torrent.password
                }, data => {
                    $('#test_torrent_result').html(data);
                });
            });
        },
        subtitles() {
            $.fn.showHideServices = function() {
                $('.serviceDiv').each(function() {
                    const serviceName = $(this).attr('id');
                    const selectedService = $('#editAService :selected').val();

                    if (selectedService + 'Div' === serviceName) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            };

            $.fn.addService = function(id, name, url, key, isDefault, showService) {
                if (url.match('/$') === null) {
                    url += '/';
                }

                if ($('#service_order_list > #' + id).length === 0 && showService !== false) {
                    const toAdd = '<li class="ui-state-default" id="' + id + '"> <input type="checkbox" id="enable_' + id + '" class="service_enabler" CHECKED> <a href="' + anonURL + url + '" class="imgLink" target="_new"><img src="' + srRoot + '/images/services/newznab.gif" alt="' + name + '" width="16" height="16"></a> ' + name + '</li>';

                    $('#service_order_list').append(toAdd);
                    $('#service_order_list').sortable('refresh');
                }
            };

            $.fn.deleteService = function(id) {
                $('#service_order_list > #' + id).remove();
            };

            $.fn.refreshServiceList = function() {
                const idArr = $('#service_order_list').sortable('toArray');
                const finalArr = [];
                $.each(idArr, (key, val) => {
                    const checked = Number($('#enable_' + val).prop('checked')) ? '1' : '0';
                    finalArr.push(val + ':' + checked);
                });
                $('#service_order').val(finalArr.join(' '));
            };

            $('#editAService').on('change', function() {
                $(this).showHideServices();
            });

            $('.service_enabler').on('click', function() {
                $(this).refreshServiceList();
            });

            // Initialization stuff
            $(this).showHideServices();

            $('#service_order_list').sortable({
                placeholder: 'ui-state-highlight',
                update() {
                    $(this).refreshServiceList();
                },
                create() {
                    $(this).refreshServiceList();
                }
            });

            $('#service_order_list').disableSelection();
        },
        providers() {
            log.info(`This function need to be filled with ConfigProviders.js but can't be as we've got scope issues currently.`);
        }
    },
    home: {
        init() {
            // Reset the layout for the activated tab (when using ui tabs)
            $('#showTabs').tabs({
                activate() {
                    $('.show-grid').isotope('layout');
                }
            });
        },
        displayShow() {
            if (metaToBool('sickbeard.FANART_BACKGROUND')) {
                $.backstretch(srRoot + '/showPoster/?show=' + $('#showID').attr('value') + '&which=fanart');
                $('.backstretch').css('opacity', getMeta('sickbeard.FANART_BACKGROUND_OPACITY')).fadeIn('500');
            }

            $('.displayShowTable').tablesorter({
                widgets: ['saveSort', 'stickyHeaders', 'columnSelector'],
                widgetOptions: {
                    columnSelector_saveColumns: true, // eslint-disable-line camelcase
                    columnSelector_layout: '<label><input type="checkbox"/>{name}</label>', // eslint-disable-line camelcase
                    columnSelector_mediaquery: false, // eslint-disable-line camelcase
                    columnSelector_cssChecked: 'checked', // eslint-disable-line camelcase
                    stickyHeaders_offset: 50 // eslint-disable-line camelcase
                }
            });

            $('#srRoot').ajaxEpSearch({colorRow: true});

            function enableLink(link) {
                link.on('click.disabled', false);
                link.prop('enableClick', '1');
                link.fadeTo('fast', 1);
            }

            function disableLink(link) {
                link.off('click.disabled');
                link.prop('enableClick', '0');
                link.fadeTo('fast', 0.5);
            }

            $('.epSubtitlesSearch').on('click', function() {
                if ($(this).prop('enableClick') === '0') {
                    return false;
                }
                disableLink($(this));

                const parent = $(this).parent();
                const subtitlesTd = parent.siblings('.col-subtitles');

                const icon = $(this).children('span');
                icon.prop('class', 'loading-spinner16');
                icon.prop('title', 'Searching');

                $.getJSON($(this).attr('href'), function(data) {
                    if (data.result.toLowerCase() !== 'failure' && data.result.toLowerCase() !== 'no subtitles downloaded') {
                        // Clear and update the subtitles column with new information
                        const subtitles = data.subtitles.split(',');
                        subtitlesTd.empty();
                        $.each(subtitles, (index, language) => {
                            if (language !== '') {
                                subtitlesTd.append($('<img/>').attr({src: srRoot + '/images/subtitles/flags/' + language + '.png', alt: language, width: 16, height: 11}));
                            }
                        });
                        icon.prop('class', 'displayshow-icon-sub');
                        enableLink($(this));
                    } else {
                        icon.prop('class', 'displayshow-icon-disable');
                    }
                    icon.prop('title', data.result);
                });
                return false;
            });

            $('.epRetrySubtitlesSearch').on('click', function() {
                if ($(this).prop('enableClick') === '0') {
                    return false;
                }

                const selectedEpisode = $(this);
                const subtitleModal = $('#confirmSubtitleDownloadModal');

                $('#confirmSubtitleDownloadModal .btn.btn-success').on('click', () => {
                    disableLink(selectedEpisode);
                    subtitleModal.modal('hide');

                    const img = selectedEpisode.children('img');
                    img.hide();

                    selectedEpisode.append($('<span/>').attr({class: 'loading-spinner16', title: 'Searching'}));
                    const icon = selectedEpisode.children('span');

                    $.getJSON(selectedEpisode.prop('href'), data => {
                        if (data.result.toLowerCase() === 'failure') {
                            icon.prop('class', 'displayshow-icon-disable');
                            icon.prop('title', 'Failed');
                        } else {
                            img.prop('title', 'Success');
                            img.prop('alt', 'Success');
                            icon.hide();
                            img.show();
                        }
                    });
                    enableLink(selectedEpisode);
                    return false;
                });
                subtitleModal.modal('show');
                return false;
            });

            $('#seasonJump').on('change', function() {
                const id = $('#seasonJump option:selected').val();
                if (id && id !== 'jump') {
                    const season = $('#seasonJump option:selected').data('season');
                    $('html,body').animate({scrollTop: $('[name ="' + id.substring(1) + '"]').offset().top - 50}, 'slow');
                    $('#collapseSeason-' + season).collapse('show');
                    location.hash = id;
                }
                $(this).val('jump');
            });

            $('#prevShow').on('click', () => {
                $('#pickShow option:selected').prev('option').prop('selected', 'selected');
                $('#pickShow').change();
            });

            $('#nextShow').on('click', () => {
                $('#pickShow option:selected').next('option').prop('selected', 'selected');
                $('#pickShow').change();
            });

            $('#changeStatus').on('click', () => {
                const srRoot = $('#srRoot').val();
                const epArr = [];

                $('.epCheck').each(function() {
                    if (this.checked === true) {
                        epArr.push($(this).attr('id'));
                    }
                });

                if (epArr.length === 0) {
                    return false;
                }

                const url = srRoot + '/home/setStatus';
                const params = 'show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|') + '&status=' + $('#statusSelect').val();
                $.post(url, params, () => {
                    location.reload(true);
                });
            });

            $('.seasonCheck').on('click', function() {
                const seasCheck = this;
                const seasNo = $(seasCheck).attr('id');
                $('#collapseSeason-' + seasNo).collapse('show');
                $('.epCheck:visible[id^="' + seasNo + 'x"]').each(function() {
                    this.checked = seasCheck.checked;
                });
            });

            let lastCheck = null;
            $('.epCheck').on('click', function(event) {
                if (!lastCheck || !event.shiftKey) {
                    lastCheck = this;
                    return;
                }

                const check = this;
                let found = 0;

                $('.epCheck').each(function() {
                    if (found === 2) {
                        return false;
                    }
                    if (found === 1) {
                        this.checked = lastCheck.checked;
                    }

                    if (this === check || this === lastCheck) {
                        found++;
                    }
                });
            });

            // Selects all visible episode checkboxes.
            $('.seriesCheck').on('click', () => {
                $('.epCheck:visible').each(function() {
                    this.checked = true;
                });
                $('.seasonCheck:visible').each(function() {
                    this.checked = true;
                });
            });

            // Clears all visible episode checkboxes and the season selectors
            $('.clearAll').on('click', () => {
                $('.epCheck:visible').each(function() {
                    this.checked = false;
                });
                $('.seasonCheck:visible').each(function() {
                    this.checked = false;
                });
            });

            // Handle the show selection dropbox
            $('#pickShow').on('change', function() {
                const srRoot = $('#srRoot').val();
                const val = $(this).val();
                if (val === 0) {
                    return;
                }
                window.location.href = srRoot + '/home/displayShow?show=' + val;
            });

            // Show/hide different types of rows when the checkboxes are changed
            $('#checkboxControls input').on('change', function() {
                const whichClass = $(this).attr('id');
                $(this).showHideRows(whichClass);
            });

            // Initially show/hide all the rows according to the checkboxes
            $('#checkboxControls input').each(function() {
                const status = $(this).prop('checked');
                $('tr.' + $(this).attr('id')).each(function() {
                    if (status) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            });

            $.fn.showHideRows = function(whichClass) {
                const status = $('#checkboxControls > input, #' + whichClass).prop('checked');
                $('tr.' + whichClass).each(function() {
                    if (status) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });

                // Hide season headers with no episodes under them
                $('tr.seasonheader').each(function() {
                    let numRows = 0;
                    const seasonNo = $(this).attr('id');
                    $('tr.' + seasonNo + ' :visible').each(() => {
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
                const srRoot = $('#srRoot').val();
                const showId = $('#showID').val();
                const indexer = $('#indexer').val();

                if (sceneSeason === '') {
                    sceneSeason = null;
                }
                if (sceneEpisode === '') {
                    sceneEpisode = null;
                }

                $.getJSON(srRoot + '/home/setSceneNumbering', {
                    show: showId,
                    indexer,
                    forSeason,
                    forEpisode,
                    sceneSeason,
                    sceneEpisode
                }, data => {
                    // Set the values we get back
                    if (data.sceneSeason === null || data.sceneEpisode === null) {
                        $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val('');
                    } else {
                        $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val(data.sceneSeason + 'x' + data.sceneEpisode);
                    }
                    if (!data.success) {
                        if (data.errorMessage) {
                            notifyModal(data.errorMessage);
                        } else {
                            notifyModal('Update failed.');
                        }
                    }
                });
            }

            function setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute) {
                const srRoot = $('#srRoot').val();
                const showId = $('#showID').val();
                const indexer = $('#indexer').val();

                if (sceneAbsolute === '') {
                    sceneAbsolute = null;
                }

                $.getJSON(srRoot + '/home/setSceneNumbering', {
                    show: showId,
                    indexer,
                    forAbsolute,
                    sceneAbsolute
                },
                data => {
                    // Set the values we get back
                    if (data.sceneAbsolute === null) {
                        $('#sceneAbsolute_' + showId + '_' + forAbsolute).val('');
                    } else {
                        $('#sceneAbsolute_' + showId + '_' + forAbsolute).val(data.sceneAbsolute);
                    }
                    if (!data.success) {
                        if (data.errorMessage) {
                            notifyModal(data.errorMessage);
                        } else {
                            notifyModal('Update failed.');
                        }
                    }
                });
            }

            function setInputValidInvalid(valid, el) {
                if (valid) {
                    $(el).css({'background-color': '#90EE90', color: '#FFF', 'font-weight': 'bold'}); // Green
                    return true;
                }
                $(el).css({'background-color': '#FF0000', color: '#FFF!important', 'font-weight': 'bold'}); // Red
                return false;
            }

            $('.sceneSeasonXEpisode').on('change', function() {
                // Strip non-numeric characters
                $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
                const forSeason = $(this).attr('data-for-season');
                const forEpisode = $(this).attr('data-for-episode');
                const m = $(this).val().match(/^(\d+)x(\d+)$/i);
                const onlyEpisode = $(this).val().match(/^(\d+)$/i);

                let sceneSeason = null;
                let sceneEpisode = null;
                let isValid = false;

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
                if (isValid) {
                    setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode);
                }
            });

            $('.sceneAbsolute').on('change', function() {
                // Strip non-numeric characters
                $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
                const forAbsolute = $(this).attr('data-for-absolute');

                const m = $(this).val().match(/^(\d{1,3})$/i);
                let sceneAbsolute = null;
                if (m) {
                    sceneAbsolute = m[1];
                }
                setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute);
            });

            $('.addQTip').each(function() {
                $(this).css({cursor: 'help', 'text-shadow': '0px 0px 0.5px #666'});
                $(this).qtip({
                    show: {solo: true},
                    position: {viewport: $(window), my: 'left center', adjust: {y: -10, x: 2}},
                    style: {tip: {corner: true, method: 'polygon'}, classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'}
                });
            });
            $.fn.generateStars = function() {
                return this.each((i, e) => {
                    $(e).html($('<span/>').width($(e).text() * 12));
                });
            };

            $('.imdbstars').generateStars();

            $('#popover').popover({
                placement: 'bottom',
                html: true, // Required if content has HTML
                content: '<div id="popover-target"></div>'
            })
            // Bootstrap popover event triggered when the popover opens
            .on('shown.bs.popover', () => {
                $('.displayShowTable').each((index, item) => {
                    $.tablesorter.columnSelector.attachTo(item, '#popover-target');
                });
            });

            // Moved and rewritten this from displayShow. This changes the button when clicked for collapsing/expanding the
            // Season to Show Episodes or Hide Episodes.
            $(() => {
                $('.collapse.toggle').on('hide.bs.collapse', function() {
                    const reg = /collapseSeason-([0-9]+)/g;
                    const result = reg.exec(this.id);
                    $('#showseason-' + result[1]).text(_('Show Episodes'));
                });
                $('.collapse.toggle').on('show.bs.collapse', function() {
                    const reg = /collapseSeason-([0-9]+)/g;
                    const result = reg.exec(this.id);
                    $('#showseason-' + result[1]).text(_('Hide Episodes'));
                });
            });
        },
        editShow() {
            let allExceptions = [];

            $('#location').fileBrowser({title: _('Select Show Location')});

            SICKRAGE.common.QualityChooser.init();

            // @TODO: Make anime button work like in addShow (opens the groups list without a refresh)
            /* $('#anime').change (function() {
                SICKRAGE.common.updateBlackWhiteList(getMeta('show.name'));
            }); */

            $('#submit').click(() => {
                const allExceptions = [];

                $('#exceptions_list option').each(function() {
                    allExceptions.push($(this).val());
                });

                $('#exceptions_list').val(allExceptions);

                if (metaToBool('show.is_anime')) {
                    generateBlackWhiteList();
                }
            });

            $('#addSceneName').click(() => {
                const sceneEx = $('#SceneName').val();
                const option = $('<option>');
                allExceptions = [];

                $('#exceptions_list option').each(function() {
                    allExceptions.push($(this).val());
                });

                $('#SceneName').val('');

                if ($.inArray(sceneEx, allExceptions) > -1 || (sceneEx === '')) {
                    return;
                }

                $('#SceneException').show();

                option.attr('value', sceneEx);
                option.html(sceneEx);
                return option.appendTo('#exceptions_list');
            });

            $('#removeSceneName').click(function() {
                $('#exceptions_list option:selected').remove();

                $(this).toggleSceneException();
            });

            $.fn.toggleSceneException = function() {
                allExceptions = [];

                $('#exceptions_list option').each(function() {
                    allExceptions.push($(this).val());
                });

                if (allExceptions === '') {
                    $('#SceneException').hide();
                } else {
                    $('#SceneException').show();
                }
            };

            $(this).toggleSceneException();
        },
        postProcess() {
            $('#episodeDir').fileBrowser({title: _('Select Unprocessed Episode Folder'), key: 'postprocessPath'});
        },
        status() {
            $('#schedulerStatusTable').tablesorter({
                widgets: ['saveSort', 'zebra'],
                textExtraction: {
                    5(node) {
                        return $(node).data('seconds');
                    },
                    6(node) {
                        return $(node).data('seconds');
                    }
                },
                headers: {
                    5: {sorter: 'digit'},
                    6: {sorter: 'digit'}
                }
            });
            $('#queueStatusTable').tablesorter({
                widgets: ['saveSort', 'zebra'],
                sortList: [[3, 0], [4, 0], [2, 1]]
            });
        },
        restart() {
            let currentPid = srPID;
            let checkIsAlive = setTimeout(() => {
                setInterval(() => {
                    $.post(srRoot + '/home/is-alive/', data => {
                        if (data === undefined || data.msg !== currentPid) {
                            $('#restart_message').show();
                            $('#shut_down_loading').hide();
                            $('#shut_down_success').show();
                        }
                        if (data !== undefined && data.msg !== 'nope' && data.msg !== currentPid) {
                            clearInterval(checkIsAlive);
                            $('#restart_loading').hide();
                            $('#restart_success').show();
                            $('#refresh_message').show();
                            srPID = currentPid = data.msg;
                            checkIsAlive = setInterval(() => {
                                $.post(srRoot + '/home/is-alive/', () => {
                                    clearInterval(checkIsAlive);
                                    setTimeout(() => {
                                        window.location = srRoot + '/' + srDefaultPage + '/';
                                    }, 2000);
                                }, 'jsonp');
                            }, 100);
                        }
                    }, 'jsonp').fail(() => {
                        $('#restart_message').show();
                        $('#shut_down_loading').hide();
                        $('#shut_down_success').show();
                    });
                }, 100);
            }, 500);
        }
    },
    manage: {
        init() {
            $.makeEpisodeRow = function(indexerId, season, episode, name, checked) {
                let row = '';
                row += ' <tr class="' + $('#row_class').val() + ' show-' + indexerId + '">';
                row += '  <td class="tableleft" align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
                row += '  <td>' + season + 'x' + episode + '</td>';
                row += '  <td class="tableright" style="width: 100%">' + name + '</td>';
                row += ' </tr>';

                return row;
            };

            $.makeSubtitleRow = function(indexerId, season, episode, name, subtitles, checked) {
                let row = '';
                row += '<tr class="good show-' + indexerId + '">';
                row += '<td align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
                row += '<td style="width: 2%;">' + season + 'x' + episode + '</td>';
                if (subtitles.length > 0) {
                    row += '<td style="width: 8%;">';
                    subtitles = subtitles.split(',');
                    for (const i in subtitles) {
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
        index() {
            $('.resetsorting').on('click', () => {
                $('table').trigger('filterReset');
            });

            $('#massUpdateTable:has(tbody tr)').tablesorter({
                sortList: [[1, 0]],
                textExtraction: {
                    2(node) {
                        return ($(node).find('img').attr('alt') || 'unknown').toLowerCase();
                    },  // Network
                    3(node) {
                        return $(node).find('span').attr('title').toLowerCase();
                    },  // Quality
                    4(node) {
                        return $(node).find('span').attr('title').toLowerCase();
                    },  // Sports
                    5(node) {
                        return $(node).find('span').attr('title').toLowerCase();
                    },  // Scene
                    6(node) {
                        return $(node).find('span').attr('title').toLowerCase();
                    },  // Anime
                    7(node) {
                        return $(node).find('span').attr('title').toLowerCase();
                    },  // Season Folders
                    8(node) {
                        return $(node).find('span').attr('title').toLowerCase();
                    },  // Paused
                    9(node) {
                        return $(node).find('span').attr('title').toLowerCase();
                    },  // Subtitle
                    10(node) {
                        return $(node).text().toLowerCase();
                    },  // Default Episode Status
                    11(node) {
                        return $(node).text().toLowerCase();
                    }  // Show Status
                },
                widgets: ['zebra', 'filter', 'columnSelector'],
                headers: {
                    0: {sorter: false, filter: false},
                    1: {sorter: 'loadingNames'},
                    2: {sorter: 'network'},
                    3: {sorter: 'quality'},
                    4: {sorter: 'sports'},
                    5: {sorter: 'scene'},
                    6: {sorter: 'anime'},
                    7: {sorter: 'flatfold'},
                    8: {sorter: 'paused'},
                    9: {sorter: 'subtitle'},
                    10: {sorter: 'default_ep_status'},
                    11: {sorter: 'status'},
                    12: {sorter: false},
                    13: {sorter: false},
                    14: {sorter: false},
                    15: {sorter: false},
                    16: {sorter: false},
                    17: {sorter: false}
                },
                widgetOptions: {
                    columnSelector_mediaquery: false
                }
            });
            $('#popover').popover({
                placement: 'bottom',
                html: true, // Required if content has HTML
                content: '<div id="popover-target"></div>'
            }).on('shown.bs.popover', () => { // Bootstrap popover event triggered when the popover opens
                // call this function to copy the column selection code into the popover
                $.tablesorter.columnSelector.attachTo($('#massUpdateTable'), '#popover-target');
            });

            $('.submitMassEdit').on('click', () => {
                const editArr = [];

                $('.editCheck').each(function() {
                    if (this.checked === true) {
                        editArr.push($(this).attr('id').split('-')[1]);
                    }
                });

                if (editArr.length === 0) {
                    return;
                }

                const submitForm = $(
                    '<form method=\'post\' action=\'' + srRoot + '/manage/massEdit\'>' +
                        '<input type=\'hidden\' name=\'toEdit\' value=\'' + editArr.join('|') + '\'/>' +
                    '</form>'
                );
                submitForm.appendTo('body');

                submitForm.submit();
            });

            $('.submitMassUpdate').on('click', () => {
                const updateArr = [];
                const refreshArr = [];
                const renameArr = [];
                const subtitleArr = [];
                const deleteArr = [];
                const removeArr = [];
                const metadataArr = [];

                $('.updateCheck').each(function() {
                    if (this.checked === true) {
                        updateArr.push($(this).attr('id').split('-')[1]);
                    }
                });

                $('.refreshCheck').each(function() {
                    if (this.checked === true) {
                        refreshArr.push($(this).attr('id').split('-')[1]);
                    }
                });

                $('.renameCheck').each(function() {
                    if (this.checked === true) {
                        renameArr.push($(this).attr('id').split('-')[1]);
                    }
                });

                $('.subtitleCheck').each(function() {
                    if (this.checked === true) {
                        subtitleArr.push($(this).attr('id').split('-')[1]);
                    }
                });

                $('.removeCheck').each(function() {
                    if (this.checked === true) {
                        removeArr.push($(this).attr('id').split('-')[1]);
                    }
                });

                let deleteCount = 0;

                $('.deleteCheck').each(function() {
                    if (this.checked === true) {
                        deleteCount++;
                    }
                });

                if (deleteCount >= 1) {
                    $.confirm({
                        title: 'Delete Shows',
                        text: 'You have selected to delete ' + deleteCount + ' show(s).  Are you sure you wish to continue? All files will be removed from your system.',
                        confirmButton: 'Yes',
                        cancelButton: 'Cancel',
                        dialogClass: 'modal-dialog',
                        post: false,
                        confirm() {
                            $('.deleteCheck').each(function() {
                                if (this.checked === true) {
                                    deleteArr.push($(this).attr('id').split('-')[1]);
                                }
                            });
                            if (updateArr.length + refreshArr.length + renameArr.length + subtitleArr.length + deleteArr.length + removeArr.length + metadataArr.length === 0) {
                                return false;
                            }
                            const url = srRoot + '/manage/massUpdate';
                            const params = 'toUpdate=' + updateArr.join('|') + '&toRefresh=' + refreshArr.join('|') + '&toRename=' + renameArr.join('|') + '&toSubtitle=' + subtitleArr.join('|') + '&toDelete=' + deleteArr.join('|') + '&toRemove=' + removeArr.join('|') + '&toMetadata=' + metadataArr.join('|');
                            $.post(url, params, () => {
                                location.reload(true);
                            });
                        }
                    });
                }
                if (updateArr.length + refreshArr.length + renameArr.length + subtitleArr.length + deleteArr.length + removeArr.length + metadataArr.length === 0) {
                    return false;
                }
                const url = srRoot + '/manage/massUpdate';
                const params = 'toUpdate=' + updateArr.join('|') + '&toRefresh=' + refreshArr.join('|') + '&toRename=' + renameArr.join('|') + '&toSubtitle=' + subtitleArr.join('|') + '&toDelete=' + deleteArr.join('|') + '&toRemove=' + removeArr.join('|') + '&toMetadata=' + metadataArr.join('|');
                $.post(url, params, () => {
                    location.reload(true);
                });
            });

            ['.editCheck', '.updateCheck', '.refreshCheck', '.renameCheck', '.deleteCheck', '.removeCheck'].forEach(name => {
                let lastCheck = null;

                $(name).on('click', function(event) {
                    if (!lastCheck || !event.shiftKey) {
                        lastCheck = this;
                        return;
                    }

                    const check = this;
                    let found = 0;

                    $(name).each(function() {
                        switch (found) {
                            case 2: return false;
                            case 1: if (!this.disabled) {
                                this.checked = lastCheck.checked;
                            }
                        }
                        if (this === check || this === lastCheck) {
                            found++;
                        }
                    });
                });
            });
        },
        backlogOverview() {
            $('#pickShow').on('change', function() {
                const id = $(this).val();
                if (id) {
                    $('html,body').animate({scrollTop: $('#show-' + id).offset().top - 25}, 'slow');
                }
            });
        },
        failedDownloads() {
            $('#failedTable:has(tbody tr)').tablesorter({
                widgets: ['zebra'],
                sortList: [[1, 0]],
                headers: {3: {sorter: false}}
            });
            $('#limit').on('change', function() {
                window.location.href = srRoot + '/manage/failedDownloads/?limit=' + $(this).val();
            });

            $('#submitMassRemove').on('click', () => {
                const removeArr = [];

                $('.removeCheck').each(function() {
                    if (this.checked === true) {
                        removeArr.push($(this).attr('id').split('-')[1]);
                    }
                });

                if (removeArr.length === 0) {
                    return false;
                }

                $.post(srRoot + '/manage/failedDownloads', 'toRemove=' + removeArr.join('|'), () => {
                    location.reload(true);
                });
            });

            if ($('.removeCheck').length) {
                $('.removeCheck').each(name => {
                    let lastCheck = null;
                    $(name).click(function(event) {
                        if (!lastCheck || !event.shiftKey) {
                            lastCheck = this;
                            return;
                        }

                        const check = this;
                        let found = 0;

                        $(name + ':visible').each(function() {
                            switch (found) {
                                case 2: return false;
                                case 1: this.checked = lastCheck.checked;
                            }

                            if (this === check || this === lastCheck) {
                                found++;
                            }
                        });
                    });
                });
            }
        },
        massEdit() {
            function findDirIndex(which) {
                const dirParts = which.split('_');
                return dirParts[dirParts.length - 1];
            }

            function editRootDir(path, options) {
                $('#new_root_dir_' + options.whichId).val(path);
                $('#new_root_dir_' + options.whichId).change();
            }

            $('.new_root_dir').change(function() {
                const curIndex = findDirIndex($(this).attr('id'));
                $('#display_new_root_dir_' + curIndex).html('<b>' + $(this).val() + '</b>');
            });

            $('.edit_root_dir').click(function() {
                const curIndex = findDirIndex($(this).attr('id'));
                const initialDir = $('#new_root_dir_' + curIndex).val();
                $(this).nFileBrowser(editRootDir, {initialDir, whichId: curIndex});
            });

            $('.delete_root_dir').click(function() {
                const curIndex = findDirIndex($(this).attr('id'));
                $('#new_root_dir_' + curIndex).val(null);
                $('#display_new_root_dir_' + curIndex).html('<b>' + _('DELETED') + '</b>');
            });

            SICKRAGE.common.QualityChooser.init();
        },
        episodeStatuses() {
            $('.allCheck').on('click', function() {
                const indexerId = $(this).attr('id').split('-')[1];
                $('.' + indexerId + '-epcheck').prop('checked', $(this).prop('checked'));
            });

            $('.get_more_eps').on('click', function() {
                const curIndexerId = $(this).attr('id');
                const checked = $('#allCheck-' + curIndexerId).prop('checked');
                const lastRow = $('tr#' + curIndexerId);
                const clicked = $(this).attr('data-clicked');
                const action = $(this).attr('value');

                if (!clicked) {
                    $.getJSON(srRoot + '/manage/showEpisodeStatuses', {
                        indexer_id: curIndexerId,
                        whichStatus: $('#oldStatus').val()
                    }, data => {
                        $.each(data, (season, eps) => {
                            $.each(eps, (episode, name) => {
                                lastRow.after($.makeEpisodeRow(curIndexerId, season, episode, name, checked));
                            });
                        });
                    });
                    $(this).attr('data-clicked', 1);
                    $(this).prop('value', 'Collapse');
                } else if (action.toLowerCase() === 'collapse') {
                    $('table tr').filter('.show-' + curIndexerId).hide();
                    $(this).prop('value', 'Expand');
                } else if (action.toLowerCase() === 'expand') {
                    $('table tr').filter('.show-' + curIndexerId).show();
                    $(this).prop('value', 'Collapse');
                }
            });

            // Selects all visible episode checkboxes.
            $('.selectAllShows').on('click', () => {
                $('.allCheck').each(function() {
                    this.checked = true;
                });
                $('input[class*="-epcheck"]').each(function() {
                    this.checked = true;
                });
            });

            // Clears all visible episode checkboxes and the season selectors
            $('.unselectAllShows').on('click', () => {
                $('.allCheck').each(function() {
                    this.checked = false;
                });
                $('input[class*="-epcheck"]').each(function() {
                    this.checked = false;
                });
            });
        },
        subtitleMissed() {
            $('.allCheck').on('click', function() {
                const indexerId = $(this).attr('id').split('-')[1];
                $('.' + indexerId + '-epcheck').prop('checked', $(this).prop('checked'));
            });

            $('.get_more_eps').on('click', function() {
                const indexerId = $(this).attr('id');
                const checked = $('#allCheck-' + indexerId).prop('checked');
                const lastRow = $('tr#' + indexerId);
                const clicked = $(this).attr('data-clicked');
                const action = $(this).attr('value');

                if (!clicked) {
                    $.getJSON(srRoot + '/manage/showSubtitleMissed', {
                        indexer_id: indexerId,
                        whichSubs: $('#selectSubLang').val()
                    }, data => {
                        $.each(data, (season, eps) => {
                            $.each(eps, (episode, data) => {
                                lastRow.after($.makeSubtitleRow(indexerId, season, episode, data.name, data.subtitles, checked));
                            });
                        });
                    });
                    $(this).attr('data-clicked', 1);
                    $(this).prop('value', 'Collapse');
                } else if (action === 'Collapse') {
                    $('table tr').filter('.show-' + indexerId).hide();
                    $(this).prop('value', 'Expand');
                } else if (action === 'Expand') {
                    $('table tr').filter('.show-' + indexerId).show();
                    $(this).prop('value', 'Collapse');
                }
            });

            // @TODO these two should be able to be merged by using a generic class for the selector

            // selects all visible episode checkboxes.
            $('.selectAllShows').on('click', () => {
                $('.allCheck').each(function() {
                    this.checked = true;
                });
                $('input[class*="-epcheck"]').each(function() {
                    this.checked = true;
                });
            });

            // Clears all visible episode checkboxes and the season selectors
            $('.unselectAllShows').on('click', () => {
                $('.allCheck').each(function() {
                    this.checked = false;
                });
                $('input[class*="-epcheck"]').each(function() {
                    this.checked = false;
                });
            });
        }
    },
    history: {
        init() {

        },
        index() {
            $('#historyTable:has(tbody tr)').tablesorter({
                widgets: ['zebra', 'filter'],
                sortList: [[0, 1]],
                textExtraction: (function() {
                    if (isMeta('sickbeard.HISTORY_LAYOUT', ['detailed'])) {
                        return {
                            0(node) {
                                return $(node).find('time').attr('datetime');
                            }, // Time
                            4(node) {
                                return $(node).find('span').text().toLowerCase();
                            } // Quality
                        };
                    }
                    const compactExtract = {
                        0(node) {
                            return $(node).find('time').attr('datetime');
                        }, // Time
                        2(node) {
                            return $(node).attr('provider').toLowerCase();
                        }
                    };

                    if (isMeta('sickbeard.USE_SUBTITLES', ['True'])) {
                        compactExtract[4] = function(node) {
                            return $(node).find('img').attr('title');
                        };  // Subtitles
                        compactExtract[5] = function(node) {
                            return $(node).find('span').text().toLowerCase();
                        }; // Quality
                    } else {
                        compactExtract[4] = function(node) {
                            return $(node).find('span').text().toLowerCase();
                        }; // Quality
                    }

                    return compactExtract;
                })(),
                headers: (function() {
                    if (isMeta('sickbeard.HISTORY_LAYOUT', ['detailed'])) {
                        return {
                            0: {sorter: 'realISODate'},
                            1: {sorter: 'loadingNames'},
                            4: {sorter: 'quality'},
                            5: {sorter: false, filter: false}
                        };
                    }
                    if (isMeta('sickbeard.USE_SUBTITLES', ['True'])) {
                        return {
                            0: {sorter: 'realISODate'},
                            1: {sorter: 'loadingNames'},
                            4: {sorter: false},
                            5: {sorter: 'quality'},
                            6: {sorter: false, filter: false}
                        };
                    }
                    return {
                        0: {sorter: 'realISODate'},
                        1: {sorter: 'loadingNames'},
                        4: {sorter: 'quality'},
                        5: {sorter: false, filter: false}
                    };
                })()
            });

            $('#history_limit').on('change', function() {
                const url = srRoot + '/history/?limit=' + $(this).val();
                window.location.href = url;
            });

            $('a.removehistory').on('click', () => {
                const removeArr = [];
                let removeCount = 0;

                $('.removeCheck').each(function() {
                    if (this.checked === true) {
                        removeArr.push(shiftReturn($(this).attr('id').split('-')));
                        removeCount++;
                    }
                });

                if (removeCount < 1) {
                    return false;
                }

                $.confirm({
                    title: 'Remove Logs',
                    text: 'You have selected to remove ' + removeCount + ' download history log(s).<br /><br />This cannot be undone.<br />Are you sure you wish to continue?',
                    confirmButton: 'Yes',
                    cancelButton: 'Cancel',
                    dialogClass: 'modal-dialog',
                    post: false,
                    confirm() {
                        const url = srRoot + '/history/removeHistory';
                        const params = 'toRemove=' + removeArr.join('|');
                        $.post(url, params, () => {
                            location.reload(true);
                        });
                    }
                });

                return false;
            });

            ['.removeCheck'].forEach(name => {
                let lastCheck = null;

                $(name).on('click', function(event) {
                    if (!lastCheck || !event.shiftKey) {
                        lastCheck = this;
                        return;
                    }

                    const check = this;
                    let found = 0;

                    $(name).each(function() {
                        if (found === 1 && !this.disabled) {
                            this.checked = lastCheck.checked;
                        } else if (found === 2) {
                            return false;
                        }

                        if (this === check || this === lastCheck) {
                            found++;
                        }
                    });
                });
            });
        }
    },
    errorlogs: {
        init() {

        },
        index() {

        },
        viewlogs() {
            $('#min_level,#log_filter,#log_search').on('keyup change', __.debounce(() => {
                if ($('#log_search').val().length > 0) {
                    $('#log_filter option[value="<NONE>"]').prop('selected', true);
                    $('#min_level option[value=5]').prop('selected', true);
                }
                $('#min_level').prop('disabled', true);
                $('#log_filter').prop('disabled', true);
                document.body.style.cursor = 'wait';
                const url = srRoot + '/errorlogs/viewlog/';
                const postData = 'min_level=' + $('select[name=min_level]').val() + '&log_filter=' + $('select[name=log_filter]').val() + '&log_search=' + $('#log_search').val();
                $.post(url, postData, data => {
                    history.pushState('data', '', url);
                    $('pre').html($(data).find('pre').html());
                    $('#min_level').prop('disabled', false);
                    $('#log_filter').prop('disabled', false);
                    document.body.style.cursor = 'default';
                });
            }, 500));

            function updateLogData() {
                if ($('#log_update_toggle').data('state') === 'active') {
                    const postData = 'min_level=' + $('select[name=min_level]').val() + '&log_filter=' + $('select[name=log_filter]').val() + '&log_search=' + $('#log_search').val();
                    const url = srRoot + '/errorlogs/viewlog/';
                    $.post(url, postData, data => {
                        $('pre').html($(data).find('pre').html());
                    });
                }
                setTimeout(() => {
                    'use strict';
                    updateLogData();
                }, 500);
            }
            updateLogData();

            $('#log_update_toggle').click(function() {
                const wasActive = $(this).data('state') === 'active'; // State before clicking
                $(this).data('state', wasActive ? 'paused' : 'active');
                $(this).find('i').toggleClass('fa-pause fa-play');
                $(this).find('span').text(wasActive ? _('Resume') : _('Pause'));
                $(this).attr('title', wasActive ? _('Resume updating the log on this page.') : _('Pause updating the log on this page.'));
                return false;
            });
        }
    },
    schedule: {
        init() {
            // Set webcal link for calendar subscription
            $('.btn-cal-subscribe').attr('href', document.location.href.replace(/https?/, 'webcal').replace('schedule', 'calendar'));
        },
        index() {
            if (isMeta('sickbeard.COMING_EPS_LAYOUT', ['list'])) {
                const sortCodes = {date: 0, show: 2, network: 5};
                const sort = getMeta('sickbeard.COMING_EPS_SORT');
                const sortList = (sort in sortCodes) ? [[sortCodes[sort], 0]] : [[0, 0]];

                $('.resetsorting').on('click', () => {
                    $('#showListTable').trigger('filterReset');
                });

                $('#showListTable:has(tbody tr)').tablesorter({
                    widgets: ['stickyHeaders', 'filter', 'columnSelector', 'saveSort'],
                    sortList,
                    textExtraction: {
                        0(node) {
                            return $(node).find('time').attr('datetime');
                        },
                        1(node) {
                            return $(node).find('time').attr('datetime');
                        },
                        7(node) {
                            return $(node).find('span').text().toLowerCase();
                        }
                    },
                    headers: {
                        0: {sorter: 'realISODate'},
                        1: {sorter: 'realISODate'},
                        2: {sorter: 'loadingNames'},
                        4: {sorter: 'loadingNames'},
                        7: {sorter: 'quality'},
                        8: {sorter: false},
                        9: {sorter: false}
                    },
                    widgetOptions: {
                        filter_columnFilters: true,
                        filter_hideFilters: true,
                        filter_saveFilters: true,
                        columnSelector_mediaquery: false,
                        stickyHeaders_offset: 50
                    }
                });

                $('#srRoot').ajaxEpSearch();
            }

            if (isMeta('sickbeard.COMING_EPS_LAYOUT', ['banner', 'poster'])) {
                $('#srRoot').ajaxEpSearch();
                $('.ep_summary').hide();
                $('.ep_summaryTrigger').click(function() {
                    $(this).next('.ep_summary').slideToggle('normal', function() {
                        $(this).prev('.ep_summaryTrigger').attr('src', function(i, src) {
                            return $(this).next('.ep_summary').is(':visible') ? src.replace('plus', 'minus') : src.replace('minus', 'plus');
                        });
                    });
                });
            }

            $('#popover').popover({
                placement: 'bottom',
                html: true, // Required if content has HTML
                content: '<div id="popover-target"></div>'
            }).on('shown.bs.popover', () => { // Bootstrap popover event triggered when the popover opens
                // call this function to copy the column selection code into the popover
                $.tablesorter.columnSelector.attachTo($('#showListTable'), '#popover-target');
            });
        }
    },
    addShows: {
        init() {
            $('#tabs').tabs({
                collapsible: true,
                selected: (metaToBool('sickbeard.SORT_ARTICLE') ? -1 : 0)
            });

            $.initRemoteShowGrid = function() {
                // Set defaults on page load
                $('#showsort').val('original');
                $('#showsortdirection').val('asc');

                $('#showsort').on('change', function() {
                    let sortCriteria;
                    switch (this.value) {
                        case 'original':
                            sortCriteria = 'original-order';
                            break;
                        case 'rating':
                            /* Randomise, else the rating_votes can already
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
                        sortAscending: (this.value === 'asc')
                    });
                });

                $('#container').isotope({
                    sortBy: 'original-order',
                    layoutMode: 'fitRows',
                    getSortData: {
                        name(itemElem) {
                            const name = $(itemElem).attr('data-name') || '';
                            return (metaToBool('sickbeard.SORT_ARTICLE') ? name : name.replace(/^((?:The|A|An)\s)/i, '')).toLowerCase();
                        },
                        rating: '[data-rating] parseInt',
                        votes: '[data-votes] parseInt'
                    }
                });
            };

            $.loadTraktImages = function() {
                const url = srRoot + '/addShows/getTrendingShowImage';
                let ajaxCount = 0;
                $('img.trakt-image').each(function() {
                    // Only load image from indexer when there is a indexer_id present in data-src-indexer-id
                    const indexerId = $(this).attr('data-src-indexer-id');
                    if (indexerId) {
                        // Use setTimemout to delay lookup for each lookup
                        // if this is not done, all retrieval of cache urls (by changing the src value) will be done after all retrieval of images
                        // this because the cache urls are appended to the request queue of the browser after the ajax calls for retrieval of images
                        setTimeout(() => {
                            $.post(url, {indexerId}, data => {
                                if (data) {
                                    // Replace src with cache location
                                    $('img.trakt-image[data-src-indexer-id="' + data + '"]').attr('src', $('img.trakt-image[data-src-indexer-id="' + data + '"]').attr('data-src-cache'));
                                }
                            });
                        }, 300 + (300 * ajaxCount));
                        ajaxCount++;
                    } else {
                        // No indexer_id present -> load it directly from cache
                        $(this).attr('src', $(this).attr('data-src-cache'));
                    }
                });
            };

            $.fn.loadRemoteShows = function(path, loadingTxt, errorTxt) {
                $(this).html('<img id="searchingAnim" src="' + srRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" />&nbsp;' + loadingTxt);
                $(this).load(srRoot + path + ' #container', function(response, status) {
                    if (status === 'error') {
                        $(this).empty().html(errorTxt);
                    } else {
                        $.initRemoteShowGrid();
                        $.loadTraktImages();
                    }
                });
            };

            $('#saveDefaultsButton').on('click', function() {
                const anyQualArray = [];
                const bestQualArray = [];
                $('#anyQualities option:selected').each((i, d) => {
                    anyQualArray.push($(d).val());
                });
                $('#bestQualities option:selected').each((i, d) => {
                    bestQualArray.push($(d).val());
                });

                $.post(srRoot + '/config/general/saveAddShowDefaults', {
                    defaultStatus: $('#statusSelect').val(),
                    anyQualities: anyQualArray.join(','),
                    bestQualities: bestQualArray.join(','),
                    defaultSeasonFolders: $('#season_folders').prop('checked'),
                    subtitles: $('#subtitles').prop('checked'),
                    anime: $('#anime').prop('checked'),
                    scene: $('#scene').prop('checked'),
                    defaultStatusAfter: $('#statusSelectAfter').val()
                });

                $(this).attr('disabled', true);
            });

            $('#statusSelect, #qualityPreset, #season_folders, #anyQualities, #bestQualities, #subtitles, #scene, #anime, #statusSelectAfter').change(() => {
                $('#saveDefaultsButton').attr('disabled', false);
            });

            SICKRAGE.common.QualityChooser.init();
        },
        index() {

        },
        newShow() {
            function updateSampleText() {
                // If something's selected then we have some behavior to figure out

                let showName, sepChar;
                // If they've picked a radio button then use that
                if ($('input:radio[name=whichSeries]:checked').length) {
                    showName = $('input:radio[name=whichSeries]:checked').val().split('|')[4];
                } else if ($('input:hidden[name=whichSeries]').length && $('input:hidden[name=whichSeries]').val().length) { // If we provided a show in the hidden field, use that
                    showName = $('#providedName').val();
                } else {
                    showName = '';
                }
                SICKRAGE.common.updateBlackWhiteList(showName);
                let sampleText = 'Adding show <b>' + showName + '</b> into <b>';

                // If we have a root dir selected, figure out the path
                if ($('#rootDirs option:selected').length) {
                    let rootDirectoryText = $('#rootDirs option:selected').val();
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

                // If we have a show name then sanitize and use it for the dir name
                if (showName.length) {
                    $.post(srRoot + '/addShows/sanitizeFileName', {name: showName}, data => {
                        $('#displayText').html(sampleText.replace('||', data));
                    });
                // If not then it's unknown
                } else {
                    $('#displayText').html(sampleText.replace('||', '??'));
                }

                // Also toggle the add show button
                if (($('#rootDirs option:selected').length || ($('#fullShowPath').length && $('#fullShowPath').val().length)) &&
                    ($('input:radio[name=whichSeries]:checked').length) || ($('input:hidden[name=whichSeries]').length && $('input:hidden[name=whichSeries]').val().length)) {
                    $('#addShowButton').attr('disabled', false);
                } else {
                    $('#addShowButton').attr('disabled', true);
                }
            }

            let searchRequestXhr = null;
            function searchIndexers() {
                if (!$('#nameToSearch').val().length) {
                    return;
                }

                if (searchRequestXhr) {
                    searchRequestXhr.abort();
                }

                const searchingFor = $('#nameToSearch').val().trim() + ' on ' + $('#providedIndexer option:selected').text() + ' in ' + $('#indexerLangSelect').val();
                $('#searchResults').empty().html('<img id="searchingAnim" src="' + srRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" /> ' + _('searching {searchingFor}...').replace(/{searchingFor}/, searchingFor));

                searchRequestXhr = $.ajax({
                    url: srRoot + '/addShows/searchIndexersForShowName',
                    data: {
                        search_term: $('#nameToSearch').val().trim(),
                        lang: $('#indexerLangSelect').val(),
                        indexer: $('#providedIndexer').val()},
                    timeout: parseInt($('#indexer_timeout').val(), 10) * 1000,
                    dataType: 'json',
                    error() {
                        $('#searchResults').empty().html(_('search timed out, try again or try another indexer'));
                    },
                    success(data) {
                        let firstResult = true;
                        let resultStr = '<fieldset>\n<legend class="legendStep">Search Results:</legend>\n';
                        let checked = '';

                        if (data.results.length === 0) {
                            resultStr += '<b>No results found, try a different search.</b>';
                        } else {
                            $.each(data.results, (index, obj) => {
                                if (firstResult) {
                                    checked = ' checked';
                                    firstResult = false;
                                } else {
                                    checked = '';
                                }

                                const whichSeries = obj.join('|');

                                resultStr += '<input type="radio" id="whichSeries" name="whichSeries" value="' + whichSeries.replace(/"/g, '') + '"' + checked + ' /> ';
                                if (data.langid && data.langid !== '') {
                                    resultStr += '<a href="' + anonURL + obj[2] + obj[3] + '&lid=' + data.langid + '" onclick=\"window.open(this.href, \'_blank\'); return false;\" ><b>' + obj[4] + '</b></a>';
                                } else {
                                    resultStr += '<a href="' + anonURL + obj[2] + obj[3] + '" onclick=\"window.open(this.href, \'_blank\'); return false;\" ><b>' + obj[4] + '</b></a>';
                                }

                                if (obj[5] !== null) {
                                    const startDate = new Date(obj[5]);
                                    const today = new Date();
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

            $('#searchName').click(() => {
                searchIndexers();
            });

            if ($('#nameToSearch').length && $('#nameToSearch').val().length) {
                $('#searchName').click();
            }

            $('#addShowButton').click(() => {
                // If they haven't picked a show don't let them submit
                if (!$('input:radio[name="whichSeries"]:checked').val() && !$('input:hidden[name="whichSeries"]').val().length) {
                    notifyModal('You must choose a show to continue');
                    return false;
                }
                generateBlackWhiteList();
                $('#addShowForm').submit();
            });

            $('#skipShowButton').click(() => {
                $('#skipShow').val('1');
                $('#addShowForm').submit();
            });

            /** *********************************************
            * JQuery Form to Form Wizard- (c) Dynamic Drive (www.dynamicdrive.com)
            * This notice MUST stay intact for legal use
            * Visit http://www.dynamicdrive.com/ for this script and 100s more.
            ********************************************** */

            function goToStep(num) {
                $('.step').each(function() {
                    if ($.data(this, 'section') + 1 === num) {
                        $(this).click();
                    }
                });
            }

            $('#nameToSearch').focus();

            // @TODO we need to move to real forms instead of this
            var myform = new formtowizard({
                formid: 'addShowForm',
                revealfx: ['slide', 500],
                oninit() {
                    updateSampleText();
                    if ($('input:hidden[name=whichSeries]').length && $('#fullShowPath').length) {
                        goToStep(3);
                    }
                }
            });

            $('#rootDirText').change(updateSampleText);
            $('#searchResults').on('change', '#whichSeries', updateSampleText);

            $('#nameToSearch').keyup(event => {
                if (event.keyCode === 13) {
                    $('#searchName').click();
                }
            });

            $('#anime').change(() => {
                updateSampleText();
                myform.loadsection(2);
            });

            $('#qualityPreset').change(() => {
                myform.loadsection(2);
            });
        },
        addExistingShow() {
            $('#tableDiv').on('click', '#checkAll', function() {
                const seasCheck = this;
                $('.dirCheck').each(function() {
                    this.checked = seasCheck.checked;
                });
            });

            $('#submitShowDirs').on('click', () => {
                const submitForm = $('#addShowForm');
                let selectedShows = false;
                $('.dirCheck').each(function() {
                    if (this.checked === true) {
                        const show = $(this).attr('id');
                        const indexer = $(this).closest('tr').find('select').val();
                        $('<input>', {
                            type: 'hidden',
                            name: 'shows_to_add',
                            value: indexer + '|' + show
                        }).appendTo(submitForm);
                        selectedShows = true;
                    }
                });

                if (selectedShows === false) {
                    return false;
                }

                $('<input>', {
                    type: 'hidden',
                    name: 'promptForSettings',
                    value: $('#promptForSettings').prop('checked') ? 'on' : 'off'
                }).appendTo(submitForm);

                submitForm.submit();
            });

            function loadContent() {
                let url = '';
                $('.dir_check').each((i, w) => {
                    if ($(w).is(':checked')) {
                        if (url.length) {
                            url += '&';
                        }
                        url += 'rootDir=' + encodeURIComponent($(w).attr('id'));
                    }
                });

                $('#tableDiv').html('<img id="searchingAnim" src="' + srRoot + '/images/loading32.gif" height="32" width="32" /> ' + _('loading folders...'));
                $.post(srRoot + '/addShows/massAddTable/', url, data => {
                    $('#tableDiv').html(data);
                    $('#addRootDirTable').tablesorter({
                        // SortList: [[1,0]],
                        widgets: ['zebra'],
                        headers: {
                            0: {sorter: false}
                        }
                    });
                });
            }

            let lastTxt = '';
            // @TODO this needs a real name, for now this fixes the issue of the page not loading at all,
            //       before I added this I couldn't get the directories to show in the table
            const a = function() {
                if (lastTxt === $('#rootDirText').val()) {
                    return false;
                }
                lastTxt = $('#rootDirText').val();

                $('#rootDirStaticList').html('');
                $('#rootDirs option').each((i, w) => {
                    $('#rootDirStaticList').append('<li class="ui-state-default ui-corner-all"><input type="checkbox" class="cb dir_check" id="' + $(w).val() + '" checked=checked> <label for="' + $(w).val() + '">' + $(w).val() + '</label></li>');
                });
                loadContent();
            };

            a();

            $('#rootDirText').on('change', a);

            $('#rootDirStaticList').on('click', '.dir_check', loadContent);

            $('#tableDiv').on('click', '.showManage', event => {
                event.preventDefault();
                $('#tabs').tabs('option', 'active', 0);
                $('html,body').animate({scrollTop: 0}, 1000);
            });
        },
        recommendedShows() {
            $('#recommendedShows').loadRemoteShows(
                '/addShows/getRecommendedShows/',
                'Loading recommended shows...',
                'Trakt timed out, refresh page to try again'
            );
        },
        trendingShows() {
            $('#trendingShows').loadRemoteShows(
                '/addShows/getTrendingShows/?traktList=' + $('#traktList').val(),
                'Loading trending shows...',
                'Trakt timed out, refresh page to try again'
            );

            $('#traktlistselection').on('change', e => {
                const traktList = e.target.value;
                window.history.replaceState({}, document.title, '?traktList=' + traktList);
                $('#trendingShows').loadRemoteShows(
                    '/addShows/getTrendingShows/?traktList=' + traktList,
                    'Loading trending shows...',
                    'Trakt timed out, refresh page to try again'
                );
            });
        },
        popularShows() {
            $.initRemoteShowGrid();
        }
    }
};
