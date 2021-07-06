function getMeta(pyVar) {
    return $('meta[data-var="' + pyVar + '"]').data('content');
}

const scRoot = getMeta('scRoot');
const srDefaultPage = getMeta('srDefaultPage');
const themeSpinner = getMeta('themeSpinner');
const anonURL = getMeta('anonURL');
const topImageHtml = '<img src="' + scRoot + '/images/top.gif" width="31" height="11" alt="Jump to top" />'; // eslint-disable-line no-unused-vars
const loading = '<img src="' + scRoot + '/images/loading16' + themeSpinner + '.gif" height="16" width="16" />';

let srPID = getMeta('srPID');

function configSuccess() {
    $('.config_submitter').each(function () {
        $(this).removeAttr('disabled');
        $(this).next().remove();
        $(this).show();
    });
    $('.config_submitter_refresh').each(function () {
        $(this).removeAttr('disabled');
        $(this).next().remove();
        $(this).show();
        window.location.href = scRoot + '/config/providers/';
    });
    $('#email_show').trigger('notify');
    $('#prowl_show').trigger('notify');
}

function metaToBool(pyVar) {
    let meta = $('meta[data-var="' + pyVar + '"]').data('content');
    if (meta === undefined) {
        console.log(pyVar + ' is empty, did you forget to add this to main.mako?');
        return meta;
    }

    meta = (Number.isNaN(meta) ? meta.toLowerCase() : meta.toString());
    meta = meta.toLowerCase();

    return !(meta === 'false' || meta === 'none' || meta === '0');
}

function isMeta(pyVar, result) {
    const reg = new RegExp(result.length > 1 ? result.join('|') : result);
    return (reg).test($('meta[data-var="' + pyVar + '"]').data('content'));
}

function notifyModal(message) {
    $('#site-notification-modal .modal-body').html(message);
    $('#site-notification-modal').modal();
}

function addSiteMessage(level = 'danger', tag = '', message = '') {
    $.post(scRoot + '/ui/set_site_message', {level, tag, message}, siteMessages => {
        const messagesDiv = $('#site-messages');
        if (messagesDiv !== undefined) {
            messagesDiv.empty();
            for (const key in siteMessages) {
                if ({}.hasOwnProperty.call(siteMessages, key)) {
                    messagesDiv.append('<div class="alert alert-' + siteMessages[key].level + ' upgrade-notification hidden-print" id="site-message-' + key + '" role="alert">'
                        + '<span>' + siteMessages[key].message + '</span><span class="glyphicon glyphicon-check site-message-dismiss pull-right" data-id="' + key + '"/>'
                        + '</div>');
                }
            }
        }
    });

    $('#site-messages').on('click', '.site-message-dismiss', function () {
        const messageID = $(this).data('id');
        $('#site-message-' + messageID).hide();
        $.post(scRoot + '/ui/dismiss-site-message', {index: messageID});
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
// Temporary (gets replaced)
window._ = function (string) {
    return string;
};

const SICKCHILL = {
    common: {
        init() {
            (function () {
                const imgDefer = document.querySelectorAll('img');
                for (const element of imgDefer) {
                    if (element.getAttribute('data-src')) {
                        element.setAttribute('src', element.getAttribute('data-src'));
                    }
                }

                if (metaToBool('settings.SICKCHILL_BACKGROUND')) {
                    $.backstretch(scRoot + '/ui/sickchill_background');
                    $('.backstretch').css('opacity', getMeta('settings.FANART_BACKGROUND_OPACITY')).fadeIn('500');
                }
            })();

            addSiteMessage(); // Show existing messages on ready.

            $.confirm.options = {
                confirmButton: 'Yes',
                cancelButton: 'Cancel',
                dialogClass: 'modal-dialog',
                post: false,
                confirm(event) {
                    location.href = event.context.href;
                },
            };

            $('a.shutdown').confirm({
                title: 'Shutdown',
                text: 'Are you sure you want to shutdown SickChill?',
            });

            $('a.restart').confirm({
                title: 'Restart',
                text: 'Are you sure you want to restart SickChill?',
            });

            $('a.removeshow').confirm({
                title: 'Remove Show',
                text: 'Are you sure you want to remove <span class="footerhighlight">' + $('#showtitle').data('showname')
                    + '</span> from the database?<br><br>'
                    + '<input type="checkbox" id="deleteFiles" name="deleteFiles"/>&nbsp;'
                    + '<label for="deleteFiles" class="red-text">Check to delete files as well. IRREVERSIBLE</label>',
                confirm(event) {
                    location.href = event.context.href + ($('#deleteFiles')[0].checked ? '&full=1' : '');
                },
            });

            $('a.clearhistory').confirm({
                title: 'Clear History',
                text: 'Are you sure you want to clear all download history?',
            });

            $('a.trimhistory').confirm({
                title: 'Trim History',
                text: 'Are you sure you want to trim all download history older than 30 days?',
            });

            $('a.submiterrors').confirm({
                title: 'Submit Errors',
                text: 'Are you sure you want to submit these errors ?<br><br><span class="red-text">Make sure SickChill is updated and trigger<br> this error with debug enabled before submitting</span>',
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
                            .fadeOut(0, function () {
                                $(this).css('position', '');
                            });
                    }

                    // Saving the last tab has been opened
                    $(this).data('lastOpenedPanel', $(ui.newPanel));
                },
            });

            // @TODO Replace this with a real touchscreen check
            // hack alert: if we don't have a touchscreen, and we are already hovering the mouse, then click should link instead of toggle
            if ((navigator.maxTouchPoints || 0) < 2) {
                $('.dropdown-toggle').on('click', function () {
                    const $this = $(this);
                    if ($this.attr('aria-expanded') === 'true') {
                        window.location.href = $this.attr('href');
                    }
                });
            }

            if (metaToBool('settings.FUZZY_DATING')) {
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
                    numbers: [],
                };
                $('[datetime]').timeago();
            }

            $(document.body).on('click', 'a[data-no-redirect]', event => {
                const element = $(event.currentTarget).preventDefault();
                $.get(element.attr('href'));

                return false;
            });

            $(document.body).on('click', '.bulkCheck', event => {
                const element = $(event.currentTarget);
                const whichBulkCheck = element.attr('id');

                $('.' + whichBulkCheck + ':visible').each(function () {
                    $(this).prop('checked', element.is(':checked'));
                });
            });

            $('.enabler').each(function () {
                if (!$(this).is(':checked')) {
                    $('#content_' + $(this).attr('id')).hide();
                }
            });

            $('.enabler').on('change', function () {
                if ($(this).is(':checked')) {
                    $('#content_' + $(this).attr('id')).fadeIn('fast', 'linear');
                } else {
                    $('#content_' + $(this).attr('id')).fadeOut('fast', 'linear');
                }
            });
        },
        QualityChooser: {
            setFromPresets(preset) {
                // @FIXME: Sometimes when switching too fast between presets,
                // it stops updating the selection on #anyQualities
                if (Number.parseInt(preset, 10) === 0) {
                    $('#customQuality').show();
                    return;
                }

                $('#customQuality').hide();

                $('#anyQualities').find('option').each(function () {
                    const result = preset & $(this).val();
                    $(this).attr('selected', result > 0 ? 'selected' : false);
                });

                $('#bestQualities').find('option').each(function () {
                    const result = preset & ($(this).val() << 16);
                    $(this).attr('selected', result > 0 ? 'selected' : false);
                });
            },
            init() {
                const qualityPresets = $('#qualityPreset');

                qualityPresets.on('change', () => {
                    this.setFromPresets(qualityPresets.find(':selected').val());
                });

                this.setFromPresets(qualityPresets.find(':selected').val());
            },
        },
        updateBlackWhiteList(showName) {
            $('#white').children().remove();
            $('#black').children().remove();
            $('#pool').children().remove();

            if ($('#anime').is(':checked')) {
                $('#blackwhitelist').show();
                if (showName) {
                    $.getJSON(scRoot + '/home/fetch_releasegroups', {
                        show_name: showName, // eslint-disable-line camelcase
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
        },
    },
    config: {
        init() {
            $('#config-components').tabs();

            $('.viewIf').on('click', function () {
                if ($(this).is(':checked')) {
                    $('.hide_if_' + $(this).attr('id')).css('display', 'none');
                    $('.show_if_' + $(this).attr('id')).fadeIn('fast', 'linear');
                } else {
                    $('.show_if_' + $(this).attr('id')).css('display', 'none');
                    $('.hide_if_' + $(this).attr('id')).fadeIn('fast', 'linear');
                }
            });

            $('.datePresets').on('click', function () {
                let def = $('#date_presets').val();
                if ($(this).is(':checked') && def === '%x') {
                    def = '%a, %b %d, %Y';
                    $('#date_use_system_default').html('1');
                } else if (!$(this).is(':checked') && $('#date_use_system_default').html() === '1') {
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
                    $('.config_submitter .config_submitter_refresh').each(function () {
                        $(this).attr('disabled', 'disabled');
                        $(this).after('<span><img src="' + scRoot + '/images/loading16' + themeSpinner + '.gif"> Saving...</span>');
                        $(this).hide();
                    });
                },
                success() {
                    setTimeout(configSuccess, 2000);
                },
            });

            $('#api_key').on('click', () => {
                $('#api_key').select();
            });

            $('#generate_new_apikey').on('click', () => {
                $.get(scRoot + '/config/general/generateApiKey', data => {
                    if (data.error !== undefined) {
                        notifyModal(data.error);
                        return;
                    }

                    $('#api_key').val(data);
                });
            });

            $('#branchCheckout').on('click', () => {
                const url = scRoot + '/home/branchCheckout?branch=' + $('#branchVersion').val();
                const checkDBversion = scRoot + '/home/compare_db_version';
                $.getJSON(checkDBversion, data => {
                    if (data.status === 'success') {
                        if (data.message === 'downgrade') {
                            notifyModal('Can\'t switch branch as this will result in a database downgrade.');
                        } else {
                            let doUpgrade = true;
                            if (data.message === 'upgrade') {
                                doUpgrade = confirm('Changing branch will upgrade your database.\nYou won\'t be able to downgrade afterward.\nDo you want to continue?'); // eslint-disable-line no-alert
                            }

                            if (doUpgrade) {
                                window.location.href = url;
                            }
                        }
                    }
                });
            });

            $('#git_token').on('click', $('#git_token').select());

            $('#create_access_token').on('click', () => {
                notifyModal(
                    '<p>Copy the generated token and paste it in the token input box.</p>'
                    + '<p>Provide permissions for repo:status, public_repo, write:discussion, read:discussion, user, gist, and notifications</p>'
                    + '<p><a href="' + anonURL + 'https://github.com/settings/tokens/new?description=SickChill&scopes=user,gist,public_repo" target="_blank">'
                    + '<input class="btn" type="button" value="Continue to Github..."></a></p>');
                $('#git_token').select();
            });

            $('#manage_tokens').on('click', () => {
                window.open(anonURL + 'https://github.com/settings/tokens', '_blank');
            });
        },
        index() {
            // $('#log_dir').fileBrowser({title: _('Select log file folder location')});
            $('#sickchill_background_path').fileBrowser({title: _('Select Background Image'), key: 'sickchill_background_path', includeFiles: 1, fileTypes: ['images']});
            $('#custom_css_path').fileBrowser({title: _('Select CSS file'), key: 'custom_css_path', includeFiles: 1, fileTypes: ['css']});

            // List remote branches available for checkout
            const branchVersion = $('#branchVersion');
            const branchVersionLabel = $('#branchVersionLabel');
            const branchCheckout = $('#branchCheckout');
            $.getJSON(scRoot + '/home/fetchRemoteBranches', branches => {
                if (branches.length > 0) {
                    const baseOptionElement = $('<option></option>');
                    let optionElement = null;
                    for (const element of branches) {
                        optionElement = baseOptionElement.clone().text(element.name).attr('value', element.name);
                        optionElement.prop('selected', Boolean(element.current));
                        optionElement.appendTo(branchVersion);
                    }

                    branchCheckout.prop('disabled', false);
                    branchVersionLabel.html(_('select branch to use (restart required)'));
                } else {
                    branchCheckout.prop('disabled', true);
                    branchVersionLabel.html(_('error: No branches found.')).css({color: '#FF0000'});
                }
            });
        },
        backupRestore() {
            $('#Backup').on('click', () => {
                $('#Backup').attr('disabled', true);
                $('#Backup-result').html(loading);
                const backupDir = $('#backupDir').val();
                $.get(scRoot + '/config/backuprestore/backup', {backupDir})
                    .done(data => {
                        $('#Backup-result').html(data);
                        $('#Backup').attr('disabled', false);
                    });
            });
            $('#Restore').on('click', () => {
                $('#Restore').attr('disabled', true);
                $('#Restore-result').html(loading);
                const backupFile = $('#backupFile').val();
                $.post(scRoot + '/config/backuprestore/restore', {backupFile})
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
            $('#testGrowl').on('click', function () {
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
                $.get(scRoot + '/home/testGrowl', {
                    host: growl.host,
                    password: growl.password,
                }).done(data => {
                    $('#testGrowl-result').html(data);
                    $('#testGrowl').prop('disabled', false);
                });
            });

            $('#testProwl').on('click', function () {
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
                $.get(scRoot + '/home/testProwl', {
                    prowl_api: prowl.api, // eslint-disable-line camelcase
                    prowl_priority: prowl.priority, // eslint-disable-line camelcase
                }).done(data => {
                    $('#testProwl-result').html(data);
                    $('#testProwl').prop('disabled', false);
                });
            });

            $('#testKODI').on('click', function () {
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
                $.get(scRoot + '/home/testKODI', {
                    host: kodi.host,
                    username: kodi.username,
                    password: kodi.password,
                }).done(data => {
                    $('#testKODI-result').html(data);
                    $('#testKODI').prop('disabled', false);
                });
            });

            $('#testPHT').on('click', function () {
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
                $.get(scRoot + '/home/testPHT', {
                    host: plex.client.host,
                    username: plex.client.username,
                    password: plex.client.password,
                }).done(data => {
                    $('#testPHT-result').html(data);
                    $('#testPHT').prop('disabled', false);
                });
            });

            $('#testPMS').on('click', function () {
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
                $.get(scRoot + '/home/testPMS', {
                    host: plex.server.host,
                    username: plex.server.username,
                    password: plex.server.password,
                    plex_server_token: plex.server.token, // eslint-disable-line camelcase
                }).done(data => {
                    $('#testPMS-result').html(data);
                    $('#testPMS').prop('disabled', false);
                });
            });

            $('#testEMBY').on('click', function () {
                const emby = {};
                emby.host = $('#emby_host').val();
                emby.apikey = $('#emby_apikey').val();
                if (!emby.host || !emby.apikey) {
                    $('#testEMBY-result').html(_('Please fill out the necessary fields above.'));
                    if (emby.host) {
                        $('#emby_host').removeClass('warning');
                    } else {
                        $('#emby_host').addClass('warning');
                    }

                    if (emby.apikey) {
                        $('#emby_apikey').removeClass('warning');
                    } else {
                        $('#emby_apikey').addClass('warning');
                    }

                    return;
                }

                $('#emby_host,#emby_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testEMBY-result').html(loading);
                $.get(scRoot + '/home/testEMBY', {
                    host: emby.host,
                    emby_apikey: emby.apikey, // eslint-disable-line camelcase
                }).done(data => {
                    $('#testEMBY-result').html(data);
                    $('#testEMBY').prop('disabled', false);
                });
            });

            $('#testBoxcar2').on('click', function () {
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
                $.get(scRoot + '/home/testBoxcar2', {
                    accesstoken: boxcar2.accesstoken,
                }).done(data => {
                    $('#testBoxcar2-result').html(data);
                    $('#testBoxcar2').prop('disabled', false);
                });
            });

            $('#testPushover').on('click', function () {
                const pushover = {};
                pushover.userkey = $('#pushover_userkey').val();
                pushover.apikey = $('#pushover_apikey').val();
                if (!pushover.userkey || !pushover.apikey) {
                    $('#testPushover-result').html(_('Please fill out the necessary fields above.'));
                    if (pushover.userkey) {
                        $('#pushover_userkey').removeClass('warning');
                    } else {
                        $('#pushover_userkey').addClass('warning');
                    }

                    if (pushover.apikey) {
                        $('#pushover_apikey').removeClass('warning');
                    } else {
                        $('#pushover_apikey').addClass('warning');
                    }

                    return;
                }

                $('#pushover_userkey,#pushover_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testPushover-result').html(loading);
                $.get(scRoot + '/home/testPushover', {
                    userKey: pushover.userkey,
                    apiKey: pushover.apikey,
                }).done(data => {
                    $('#testPushover-result').html(data);
                    $('#testPushover').prop('disabled', false);
                });
            });

            $('#testLibnotify').on('click', () => {
                $('#testLibnotify-result').html(loading);
                $.get(scRoot + '/home/testLibnotify', data => {
                    $('#testLibnotify-result').html(data);
                });
            });

            $('#twitterStep1').on('click', () => {
                $('#testTwitter-result').html(loading);
                $.get(scRoot + '/home/twitterStep1', data => {
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
                $.get(scRoot + '/home/twitterStep2', {
                    key: twitter.key,
                }, data => {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#testTwitter').on('click', () => {
                $.post(scRoot + '/home/testTwitter', data => {
                    $('#testTwitter-result').html(data);
                });
            });

            $('#testTwilio').on('click', () => {
                $('#testTwilio').addClass('disabled');
                $.post(scRoot + '/home/testTwilio', data => {
                    $('#testTwilio-result').html(data);
                }).always(() => {
                    $('#testTwilio').removeClass('disabled');
                });
            });

            $('#testSlack').on('click', () => {
                $.post(scRoot + '/home/testSlack', data => {
                    $('#testSlack-result').html(data);
                });
            });

            $('#testRocketChat').on('click', () => {
                $.post(scRoot + '/home/testRocketChat', data => {
                    $('#testRocketChat-result').html(data);
                });
            });

            $('#testMatrix').on('click', () => {
                $.post(scRoot + '/home/testMatrix', data => {
                    $('#testMatrix-result').html(data);
                });
            });

            $('#testDiscord').on('click', () => {
                const discord = {};
                const discordWebhook = $('#discord_webhook');
                discord.webhook = discordWebhook.val();
                if (!discord.webhook) {
                    discordWebhook.focus();
                    notifyModal('Please fill in the webhook address');
                    return;
                }

                discord.name = $('#discord_name').val();
                discord.avatar = $('#discord_avatar_url').val();
                discord.tts = $('#discord_tts').val();

                $('#testDiscord').prop('disabled', true);
                $('#testDiscord-result').html(loading);
                $.get(scRoot + '/home/testDiscord', {
                    webhook: discord.webhook,
                    name: discord.name,
                    avatar: discord.avatar,
                    tts: discord.tts,
                }).done(data => {
                    $('#testDiscord-result').html(data);
                    $('#testDiscord').prop('disabled', false);
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

                $.post(scRoot + '/home/settingsNMJ', {host: nmj.host}, data => {
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

            $('#testNMJ').on('click', function () {
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
                $.post(scRoot + '/home/testNMJ', {
                    host: nmj.host,
                    database: nmj.database,
                    mount: nmj.mount,
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
                for (const element of radios) {
                    if (element.checked) {
                        nmjv2.dbloc = element.value;
                        break;
                    }
                }

                nmjv2.dbinstance = $('#NMJv2db_instance').val();
                $.post(scRoot + '/home/settingsNMJv2', {
                    host: nmjv2.host,
                    dbloc: nmjv2.dbloc,
                    instance: nmjv2.dbinstance,
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

            $('#testNMJv2').on('click', function () {
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
                $.post(scRoot + '/home/testNMJv2', {
                    host: nmjv2.host,
                }).done(data => {
                    $('#testNMJv2-result').html(data);
                    $('#testNMJv2').prop('disabled', false);
                });
            });

            $('#testFreeMobile').on('click', function () {
                const freemobile = {};
                freemobile.id = $.trim($('#freemobile_id').val());
                freemobile.apikey = $.trim($('#freemobile_apikey').val());
                if (!freemobile.id || !freemobile.apikey) {
                    $('#testFreeMobile-result').html(_('Please fill out the necessary fields above.'));
                    if (freemobile.id) {
                        $('#freemobile_id').removeClass('warning');
                    } else {
                        $('#freemobile_id').addClass('warning');
                    }

                    if (freemobile.apikey) {
                        $('#freemobile_apikey').removeClass('warning');
                    } else {
                        $('#freemobile_apikey').addClass('warning');
                    }

                    return;
                }

                $('#freemobile_id,#freemobile_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testFreeMobile-result').html(loading);
                $.post(scRoot + '/home/testFreeMobile', {
                    freemobile_id: freemobile.id, // eslint-disable-line camelcase
                    freemobile_apikey: freemobile.apikey, // eslint-disable-line camelcase
                }).done(data => {
                    $('#testFreeMobile-result').html(data);
                    $('#testFreeMobile').prop('disabled', false);
                });
            });

            $('#testTelegram').on('click', function () {
                const telegram = {};
                telegram.id = $.trim($('#telegram_id').val());
                telegram.apikey = $.trim($('#telegram_apikey').val());
                if (!telegram.id || !telegram.apikey) {
                    $('#testTelegram-result').html(_('Please fill out the necessary fields above.'));
                    if (telegram.id) {
                        $('#telegram_id').removeClass('warning');
                    } else {
                        $('#telegram_id').addClass('warning');
                    }

                    if (telegram.apikey) {
                        $('#telegram_apikey').removeClass('warning');
                    } else {
                        $('#telegram_apikey').addClass('warning');
                    }

                    return;
                }

                $('#telegram_id,#telegram_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testTelegram-result').html(loading);
                $.post(scRoot + '/home/testTelegram', {
                    telegram_id: telegram.id, // eslint-disable-line camelcase
                    telegram_apikey: telegram.apikey, // eslint-disable-line camelcase
                }).done(data => {
                    $('#testTelegram-result').html(data);
                    $('#testTelegram').prop('disabled', false);
                });
            });

            $('#testJoin').on('click', function () {
                const join = {};
                join.id = $.trim($('#join_id').val());
                join.apikey = $.trim($('#join_apikey').val());
                if (!join.id || !join.apikey) {
                    $('#testJoin-result').html(_('Please fill out the necessary fields above.'));
                    if (join.id) {
                        $('#join_id').removeClass('warning');
                    } else {
                        $('#join_id').addClass('warning');
                    }

                    if (join.apikey) {
                        $('#join_apikey').removeClass('warning');
                    } else {
                        $('#join_apikey').addClass('warning');
                    }

                    return;
                }

                $('#join_id,#join_apikey').removeClass('warning');
                $(this).prop('disabled', true);
                $('#testJoin-result').html(loading);
                $.post(scRoot + '/home/testJoin', {
                    join_id: join.id, // eslint-disable-line camelcase
                    join_apikey: join.apikey, // eslint-disable-line camelcase
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
                if ($('#trakt_pin').val().length === 0) {
                    $('#TraktGetPin').removeClass('hide');
                    $('#authTrakt').addClass('hide');
                } else {
                    $('#TraktGetPin').addClass('hide');
                    $('#authTrakt').removeClass('hide');
                }
            });

            $('#authTrakt').on('click', () => {
                const trakt = {};
                trakt.pin = $('#trakt_pin').val();
                if (trakt.pin.length > 0) {
                    $.post(scRoot + '/home/getTraktToken', {
                        trakt_pin: trakt.pin, // eslint-disable-line camelcase
                    }).done(data => {
                        $('#testTrakt-result').html(data);
                        $('#authTrakt').addClass('hide');
                        $('#trakt_pin').addClass('hide');
                        $('#TraktGetPin').addClass('hide');
                    });
                }
            });

            $('#testTrakt').on('click', function () {
                const trakt = {};
                trakt.username = $.trim($('#trakt_username').val());
                trakt.trendingBlacklist = $.trim($('#trakt_blacklist_name').val());
                if (!trakt.username) {
                    $('#testTrakt-result').html(_('Please fill out the necessary fields above.'));
                    if (trakt.username) {
                        $('#trakt_username').removeClass('warning');
                    } else {
                        $('#trakt_username').addClass('warning');
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
                $.post(scRoot + '/home/testTrakt', {
                    username: trakt.username,
                    blacklist_name: trakt.trendingBlacklist, // eslint-disable-line camelcase
                }).done(data => {
                    $('#testTrakt-result').html(data);
                    $('#testTrakt').prop('disabled', false);
                });
            });

            $('#testEmail').on('click', () => {
                const status = $('#testEmail-result');
                status.html(loading);
                const host = $('#email_host').val().length > 0 ? $('#email_host').val() : null;
                const port = $('#email_port').val().length > 0 ? $('#email_port').val() : null;
                const tls = $('#email_tls').is(':checked') ? 1 : 0;
                const from = $('#email_from').val().length > 0 ? $('#email_from').val() : 'root@localhost';
                const user = $('#email_user').val().trim();
                const pwd = $('#email_password').val();
                let error = '';
                let to = '';
                if (host === null) {
                    error += '<li style="color: red;">You must specify an SMTP hostname!</li>';
                }

                if (port === null) {
                    error += '<li style="color: red;">You must specify an SMTP port!</li>';
                } else if (port.match(/^\d+$/) === null || Number.parseInt(port, 10) > 65535) {
                    error += '<li style="color: red;">SMTP port must be between 0 and 65535!</li>';
                }

                if (error.length > 0) {
                    error = '<ol>' + error + '</ol>';
                    status.html(error);
                } else {
                    to = prompt('Enter an email address to send the test to:', null); // eslint-disable-line no-alert
                    if (to === null || to.length === 0 || to.match(/.*@.*/) === null) {
                        status.html('<p style="color: red;">' + _('You must provide a recipient email address!') + '</p>');
                    } else {
                        $.post(scRoot + '/home/testEmail', {
                            host,
                            port,
                            smtp_from: from, // eslint-disable-line camelcase
                            use_tls: tls, // eslint-disable-line camelcase
                            user,
                            pwd,
                            to,
                        }, message => {
                            $('#testEmail-result').html(message);
                        });
                    }
                }
            });

            $('#testPushalot').on('click', function () {
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
                $.post(scRoot + '/home/testPushalot', {
                    authorizationToken: pushalot.authToken,
                }).done(data => {
                    $('#testPushalot-result').html(data);
                    $('#testPushalot').prop('disabled', false);
                });
            });

            $('#testPushbullet').on('click', function () {
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
                $.post(scRoot + '/home/testPushbullet', {
                    api: pushbullet.api,
                }).done(data => {
                    $('#testPushbullet-result').html(data);
                    $('#testPushbullet').prop('disabled', false);
                });
            });

            function getPushbulletDevices(message) {
                const pushbullet = {};
                pushbullet.api = $('#pushbullet_api').val();

                if (message) {
                    $('#testPushbullet-result').html(loading);
                }

                if (!pushbullet.api) {
                    $('#testPushbullet-result').html(_('You didn\'t supply a Pushbullet api key'));
                    $('#pushbullet_api').focus();
                    return false;
                }

                $.post(scRoot + '/home/getPushbulletDevices', {
                    api: pushbullet.api,
                }, data => {
                    pushbullet.devices = $.parseJSON(data).devices;
                    pushbullet.currentDevice = $('#pushbullet_device').val();
                    $('#pushbullet_device_list').html('');
                    for (let i = 0; i < pushbullet.devices.length; i++) {
                        if (pushbullet.devices[i].active === true) {
                            if (pushbullet.currentDevice === pushbullet.devices[i].iden) {
                                $('#pushbullet_device_list').append('<option value="' + pushbullet.devices[i].iden + '" selected>' + pushbullet.devices[i].nickname + '</option>');
                            } else {
                                $('#pushbullet_device_list').append('<option value="' + pushbullet.devices[i].iden + '">' + pushbullet.devices[i].nickname + '</option>');
                            }
                        }
                    }

                    $('#pushbullet_device_list').prepend('<option value="" ' + (pushbullet.currentDevice === '' ? 'selected' : '') + '>All devices</option>');
                    if (message) {
                        $('#testPushbullet-result').html(message);
                    }
                });

                $('#pushbullet_device_list').on('change', () => {
                    $('#pushbullet_device').val($('#pushbullet_device_list').val());
                    $('#testPushbullet-result').html(_('Don\'t forget to save your new pushbullet settings.'));
                });

                $.post(scRoot + '/home/getPushbulletChannels', {
                    api: pushbullet.api,
                }, data => {
                    pushbullet.channels = $.parseJSON(data).channels;
                    pushbullet.currentChannel = $('#pushbullet_channel').val();
                    $('#pushbullet_channel_list').html('');
                    if (pushbullet.channels.length > 0) {
                        for (let i = 0; i < pushbullet.channels.length; i++) {
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

                    if (message) {
                        $('#testPushbullet-result').html(message);
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
                const key = Number.parseInt($('#email_show').val(), 10);
                $.getJSON(scRoot + '/home/loadShowNotifyLists', notifyData => {
                    if (notifyData._size > 0) {
                        $('#email_show_list').val(key >= 0 ? notifyData[key.toString()].list : '');
                    }
                });
            });
            $('#prowl_show').on('change', () => {
                const key = Number.parseInt($('#prowl_show').val(), 10);
                $.getJSON(scRoot + '/home/loadShowNotifyLists', notifyData => {
                    if (notifyData._size > 0) {
                        $('#prowl_show_list').val(key >= 0 ? notifyData[key.toString()].prowl_notify_list : '');
                    }
                });
            });

            function loadShowNotifyLists() {
                $.getJSON(scRoot + '/home/loadShowNotifyLists', list => {
                    if (list._size === 0) {
                        return;
                    }

                    // Convert the 'list' object to a js array of objects so that we can sort it
                    const _list = [];
                    for (const _show in list) {
                        if ({}.hasOwnProperty.call(list, _show) && _show.charAt(0) !== '_') {
                            _list.push(list[_show]);
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
                    let html = '<option value="-1">-- Select --</option>';
                    for (const _show in sortedList) {
                        if ({}.hasOwnProperty.call(sortedList, _show) && sortedList[_show].id && sortedList[_show].name) {
                            html += '<option value="' + sortedList[_show].id + '">' + $('<div>').text(sortedList[_show].name).html() + '</option>';
                        }
                    }

                    $('#email_show').html(html);
                    $('#email_show_list').val('');

                    $('#prowl_show').html(html);
                    $('#prowl_show_list').val('');
                });
            }

            // Load the per show notify lists every time this page is loaded
            loadShowNotifyLists();

            // Update the internal data struct anytime settings are saved to the server
            $('#email_show').on('notify', () => {
                loadShowNotifyLists();
            });
            $('#prowl_show').on('notify', () => {
                loadShowNotifyLists();
            });

            $('#email_show_save').on('click', () => {
                $.post(scRoot + '/home/saveShowNotifyList', {
                    show: $('#email_show').val(),
                    emails: $('#email_show_list').val(),
                }, () => {
                    // Reload the per show notify lists to reflect changes
                    loadShowNotifyLists();
                });
            });
            $('#prowl_show_save').on('click', () => {
                $.post(scRoot + '/home/saveShowNotifyList', {
                    show: $('#prowl_show').val(),
                    prowlAPIs: $('#prowl_show_list').val(),
                }, () => {
                    // Reload the per show notify lists to reflect changes
                    loadShowNotifyLists();
                });
            });

            // Show instructions for plex when enabled
            $('#use_plex_server').on('click', function () {
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
            const typewatch = (function () {
                let timer = 0;
                return function (callback, ms) {
                    clearTimeout(timer);
                    timer = setTimeout(callback, ms);
                };
            })();

            function isRarSupported() {
                $.post(scRoot + '/config/postProcessing/isRarSupported', data => {
                    if (data !== 'supported') {
                        $('#unpack').qtip('option', {
                            'content.text': 'Unrar Executable not found.',
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red',
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

                $.post(scRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                }, data => {
                    if (data) {
                        $('#naming_example').text(data + '.ext');
                        $('#naming_example_div').show();
                    } else {
                        $('#naming_example_div').hide();
                    }
                });

                $.post(scRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                    multi: example.multi,
                }, data => {
                    if (data) {
                        $('#naming_example_multi').text(data + '.ext');
                        $('#naming_example_multi_div').show();
                    } else {
                        $('#naming_example_multi_div').hide();
                    }
                });

                $.post(scRoot + '/config/postProcessing/isNamingValid', {
                    pattern: example.pattern,
                    multi: example.multi,
                }, data => {
                    let info;
                    if (data === 'invalid') {
                        info = _('This pattern is invalid.');
                        $('#naming_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFDDDD');
                    } else if (data === 'seasonfolders') {
                        info = _('This pattern would be invalid without the folders, using it will force "Season Folders" on for all shows.');
                        $('#naming_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                        });
                        $('#naming_pattern').qtip('toggle', true);
                        $('#naming_pattern').css('background-color', '#FFFFDD');
                    } else {
                        info = _('This pattern is valid.');
                        $('#naming_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green',
                        });
                        $('#naming_pattern').qtip('toggle', false);
                        $('#naming_pattern').css('background-color', '#FFFFFF');
                    }

                    $('#naming_pattern').attr('title', info);
                });
            }

            function fillAbdExamples() {
                const pattern = $('#naming_abd_pattern').val();

                $.post(scRoot + '/config/postProcessing/testNaming', {
                    pattern,
                    abd: 'True',
                }, data => {
                    if (data) {
                        $('#naming_abd_example').text(data + '.ext');
                        $('#naming_abd_example_div').show();
                    } else {
                        $('#naming_abd_example_div').hide();
                    }
                });

                $.post(scRoot + '/config/postProcessing/isNamingValid', {
                    pattern,
                    abd: 'True',
                }, data => {
                    let info;
                    if (data === 'invalid') {
                        info = _('This pattern is invalid.');
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                        });
                        $('#naming_abd_pattern').qtip('toggle', true);
                        $('#naming_abd_pattern').css('background-color', '#FFDDDD');
                    } else if (data === 'seasonfolders') {
                        info = _('This pattern would be invalid without the folders, using it will force "Season Folders" on for all shows.');
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                        });
                        $('#naming_abd_pattern').qtip('toggle', true);
                        $('#naming_abd_pattern').css('background-color', '#FFFFDD');
                    } else {
                        info = _('This pattern is valid.');
                        $('#naming_abd_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green',
                        });
                        $('#naming_abd_pattern').qtip('toggle', false);
                        $('#naming_abd_pattern').css('background-color', '#FFFFFF');
                    }

                    $('#naming_abd_pattern').attr('title', info);
                });
            }

            function fillSportsExamples() {
                const pattern = $('#naming_sports_pattern').val();

                $.post(scRoot + '/config/postProcessing/testNaming', {
                    pattern,
                    sports: 'True', // @TODO does this actually need to be a string or can it be a boolean?
                }, data => {
                    if (data) {
                        $('#naming_sports_example').text(data + '.ext');
                        $('#naming_sports_example_div').show();
                    } else {
                        $('#naming_sports_example_div').hide();
                    }
                });

                $.post(scRoot + '/config/postProcessing/isNamingValid', {
                    pattern,
                    sports: 'True', // @TODO does this actually need to be a string or can it be a boolean?
                }, data => {
                    let info;
                    if (data === 'invalid') {
                        info = _('This pattern is invalid.');
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                        });
                        $('#naming_sports_pattern').qtip('toggle', true);
                        $('#naming_sports_pattern').css('background-color', '#FFDDDD');
                    } else if (data === 'seasonfolders') {
                        info = _('This pattern would be invalid without the folders, using it will force "Season Folders" on for all shows.');
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                        });
                        $('#naming_sports_pattern').qtip('toggle', true);
                        $('#naming_sports_pattern').css('background-color', '#FFFFDD');
                    } else {
                        info = _('This pattern is valid.');
                        $('#naming_sports_pattern').qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green',
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

                $.post(scRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                    anime_type: example.animeType, // eslint-disable-line camelcase
                }, data => {
                    if (data) {
                        $('#naming_example_anime').text(data + '.ext');
                        $('#naming_example_anime_div').show();
                    } else {
                        $('#naming_example_anime_div').hide();
                    }
                });

                $.post(scRoot + '/config/postProcessing/testNaming', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: example.animeType, // eslint-disable-line camelcase
                }, data => {
                    if (data) {
                        $('#naming_example_multi_anime').text(data + '.ext');
                        $('#naming_example_multi_anime_div').show();
                    } else {
                        $('#naming_example_multi_anime_div').hide();
                    }
                });

                $.post(scRoot + '/config/postProcessing/isNamingValid', {
                    pattern: example.pattern,
                    multi: example.multi,
                    anime_type: example.animeType, // eslint-disable-line camelcase
                }, data => {
                    let info;
                    const $namingAnimePatternInput = $('#naming_anime_pattern');
                    if (data === 'invalid') {
                        info = _('This pattern is invalid.');
                        $namingAnimePatternInput.qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                        });
                        $namingAnimePatternInput.qtip('toggle', true);
                        $namingAnimePatternInput.css('background-color', '#FFDDDD');
                    } else if (data === 'seasonfolders') {
                        info = _('This pattern would be invalid without the folders, using it will force "Season Folders" on for all shows.');
                        $namingAnimePatternInput.qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                        });
                        $namingAnimePatternInput.qtip('toggle', true);
                        $namingAnimePatternInput.css('background-color', '#FFFFDD');
                    } else {
                        info = _('This pattern is valid.');
                        $namingAnimePatternInput.qtip('option', {
                            'content.text': info,
                            'style.classes': 'qtip-rounded qtip-shadow qtip-green',
                        });
                        $namingAnimePatternInput.qtip('toggle', false);
                        $namingAnimePatternInput.css('background-color', '#FFFFFF');
                    }

                    $namingAnimePatternInput.attr('title', info);
                });
            }

            // @TODO all of these setup functions should be able to be rolled into a generic jQuery function

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

            if (Number.parseInt($('#unpack').val(), 10) !== 1) {
                $('#content_unpack').hide();
            }

            $('#unpack').on('change', function () {
                const value = Number.parseInt(this.value, 10);

                // 'Treat as video' or 'Ignore'
                if (value === 2 || value === 0) {
                    $('#content_unpack').fadeOut('fast', 'linear');
                    $('#unpack').qtip('toggle', false);
                }

                // 'Unpack'
                if (value === 1) {
                    $('#content_unpack').fadeIn('fast', 'linear');
                    isRarSupported();
                }
            });

            // @TODO all of these on change functions should be able to be rolled into a generic jQuery function or maybe we could
            //       move all of the setup functions into these handlers?

            $('#name_presets').on('change', setupNaming);
            $('#name_abd_presets').on('change', setupAbdNaming);
            $('#naming_custom_abd').on('change', setupAbdNaming);
            $('#name_sports_presets').on('change', setupSportsNaming);
            $('#naming_custom_sports').on('change', setupSportsNaming);
            $('#name_anime_presets').on('change', setupAnimeNaming);
            $('#naming_custom_anime').on('change', setupAnimeNaming);
            $('input[name="naming_anime"]').on('click', setupAnimeNaming);

            // @TODO We might be able to change these from typewatch to __.debounce like we've done on the log page
            //       The main reason for doing this would be to use only open source stuff that's still being maintained

            $('#naming_multi_ep').on('change', fillExamples);
            $('#naming_pattern').on('focusout', fillExamples);
            $('#naming_pattern').on('keyup', () => {
                typewatch(fillExamples, 500);
            });

            $('#naming_anime_multi_ep').on('change', fillAnimeExamples);
            $('#naming_anime_pattern').on('focusout', fillAnimeExamples);
            $('#naming_anime_pattern').on('keyup', () => {
                typewatch(fillAnimeExamples, 500);
            });

            $('#naming_abd_pattern').on('focusout', fillExamples);
            $('#naming_abd_pattern').on('keyup', () => {
                typewatch(fillAbdExamples, 500);
            });

            $('#naming_sports_pattern').on('focusout', fillExamples);
            $('#naming_sports_pattern').on('keyup', () => {
                typewatch(fillSportsExamples, 500);
            });

            $('#naming_anime_pattern').on('focusout', fillExamples);
            $('#naming_anime_pattern').on('keyup', () => {
                typewatch(fillAnimeExamples, 500);
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
            $('#metadataType').on('change keyup', function () {
                $(this).showHideMetadata();
            });

            $.fn.showHideMetadata = function () {
                $('.metadataDiv').each(function () {
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

            $('.metadata_checkbox').on('click', function () {
                $(this).refreshMetadataConfig(false);
            });

            $.fn.refreshMetadataConfig = function (first) {
                let curMost = 0;
                let curMostProvider = '';

                $('.metadataDiv').each(function () { // eslint-disable-line complexity
                    const generatorName = $(this).attr('id');

                    const configArray = [];
                    const showMetadata = $('#' + generatorName + '_show_metadata').is(':checked');
                    const episodeMetadata = $('#' + generatorName + '_episode_metadata').is(':checked');
                    const fanart = $('#' + generatorName + '_fanart').is(':checked');
                    const poster = $('#' + generatorName + '_poster').is(':checked');
                    const banner = $('#' + generatorName + '_banner').is(':checked');
                    const episodeThumbnails = $('#' + generatorName + '_episode_thumbnails').is(':checked');
                    const seasonPosters = $('#' + generatorName + '_season_posters').is(':checked');
                    const seasonBanners = $('#' + generatorName + '_season_banners').is(':checked');
                    const seasonAllPoster = $('#' + generatorName + '_season_all_poster').is(':checked');
                    const seasonAllBanner = $('#' + generatorName + '_season_all_banner').is(':checked');

                    configArray.push(showMetadata ? '1' : '0', episodeMetadata ? '1' : '0', fanart ? '1' : '0', poster ? '1' : '0', banner ? '1' : '0', episodeThumbnails ? '1' : '0', seasonPosters ? '1' : '0', seasonBanners ? '1' : '0', seasonAllPoster ? '1' : '0', seasonAllBanner ? '1' : '0');

                    let curNumber = 0;
                    for (const element of configArray) {
                        curNumber += Number.parseInt(element, 10);
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
                    my: 'top right',
                },
                style: {
                    tip: {
                        corner: true,
                        method: 'polygon',
                    },
                    classes: 'qtip-shadow qtip-dark',
                },
            });
            $('i[title]').qtip({
                position: {
                    viewport: $(window),
                    at: 'top center',
                    my: 'bottom center',
                },
                style: {
                    tip: {
                        corner: true,
                        method: 'polygon',
                    },
                    classes: 'qtip-rounded qtip-shadow ui-tooltip-sb',
                },
            });
            $('.custom-pattern,#unpack').qtip({
                content: 'validating...',
                show: {
                    event: false,
                    ready: false,
                },
                hide: false,
                position: {
                    viewport: $(window),
                    at: 'center left',
                    my: 'center right',
                },
                style: {
                    tip: {
                        corner: true,
                        method: 'polygon',
                    },
                    classes: 'qtip-rounded qtip-shadow qtip-red',
                },
            });
        },
        search() {
            $('#config-components').tabs();
            $('#nzb_dir').fileBrowser({title: _('Select .nzb black hole/watch location')});
            $('#torrent_dir').fileBrowser({title: _('Select torrent black hole/watch location')});
            $('#torrent_path').fileBrowser({title: _('Select torrent download location')});
            $('#torrent_path_incomplete').fileBrowser({title: _('Select torrent incomplete download location')});

            $.fn.nzbMethodHandler = function () {
                const selectedProvider = $('#nzb_method :selected').val();
                const blackholeSettings = '#blackhole_settings';
                const sabnzbdSettings = '#sabnzbd_settings';
                const testSABnzbd = '#testSABnzbd';
                const testSABnzbdResult = '#testSABnzbd_result';
                const nzbgetSettings = '#nzbget_settings';
                const downloadStationSettings = '#download_station_settings';
                const testDSM = '#testDSM';
                const testDSMResult = '#testDSM_result';

                $('#nzb_method_icon').removeClass((index, css) => (css.match(/(^|\s)add-client-icon-\S+/g) || []).join(' '));
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
                    $('#host_title').text('Synology host:port');
                    $('#username_title').text('Synology Username');
                    $('#password_title').text('Synology Password');

                    $(downloadStationSettings).show();
                    $(testDSM).show();
                    $(testDSMResult).show();
                } else {
                    $(sabnzbdSettings).show();
                    $(testSABnzbd).show();
                    $(testSABnzbdResult).show();
                }
            };

            $.torrentMethodHandler = () => {
                $('#options_torrent_clients').hide();
                $('#options_torrent_blackhole').hide();

                const selectedProvider = $('#torrent_method :selected').val();

                let optionPanel = '#options_torrent_blackhole';
                let client = '';

                $('#torrent_method_icon').removeClass((index, css) => (css.match(/(^|\s)add-client-icon-\S+/g) || []).join(' '));
                $('#torrent_method_icon').addClass('add-client-icon-' + selectedProvider.replace('_', '-'));

                if (selectedProvider.toLowerCase() !== 'blackhole') {
                    $('#torrent_host_option').show();
                    $('#host_desc_torrent').show();

                    $('#torrent_rpcurl_option').hide();
                    $('#torrent_auth_type_option').hide();

                    $('#torrent_verify_cert_option').hide();
                    $('label[for="torrent_verify_cert"]').text(_('verify SSL certificates for HTTPS requests'));

                    $('#username_title.component-title').text(_('Client username'));
                    $('#torrent_username_option').show();

                    $('#password_title.component-title').text(_('Client password'));
                    $('#torrent_password_option').show();
                    $('label[for="torrent_password"]').text(_('(blank for none)'));

                    $('#torrent_path_option').show();
                    $('#torrent_path_option').find('.fileBrowser').show();
                    $('#torrent_path_incomplete_option').hide();
                    $('#path_synology').hide();

                    $('#torrent_seed_time_option').hide();
                    $('#torrent_high_bandwidth_option').hide();
                    $('#torrent_paused_option').show();

                    $('#torrent_label_option').show();
                    $('#label_warning_deluge').hide();
                    $('#label_anime_warning_deluge').hide();
                    $('#test_torrent_result').text(_('Click below to test'));

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
                        $('#torrent_path_incomplete_option').show();
                        $('#torrent_label_option').hide();
                        $('#torrent_rpcurl_option').show();
                        $('#host_desc_torrent').text(_('URL to your Transmission client (e.g. http://localhost:9091)'));
                    } else if (selectedProvider.toLowerCase().startsWith('deluge')) {
                        $('#torrent_verify_cert_option').show();
                        $('#label_warning_deluge').show();
                        $('#label_anime_warning_deluge').show();
                        $('#torrent_path_incomplete_option').show();
                        if (selectedProvider.toLowerCase() === 'deluged') {
                            client = 'Deluge Daemon';
                            $('#torrent_username_option').show();
                            $('#host_desc_torrent').text(_('IP or Hostname of your Deluge Daemon (e.g. http://localhost:58846)'));
                        } else {
                            client = 'Deluge';
                            $('#torrent_username').prop('value', '');
                            $('#torrent_username_option').hide();
                            $('#host_desc_torrent').text(_('URL to your Deluge client (e.g. http://localhost:8112)'));
                        }

                        $('label[for="torrent_verify_cert"]').text(_('disable if you get "Deluge: Authentication Error" in your log'));
                    } else if (selectedProvider.toLowerCase() === 'download_station') {
                        client = 'Synology DS';
                        $('#torrent_label_option').hide();
                        $('#torrent_paused_option').hide();
                        $('#torrent_path_option').find('.fileBrowser').hide();
                        $('#host_desc_torrent').text(_('URL to your Synology DS client (e.g. http://localhost:5000)'));
                        $('#path_synology').show();
                    } else if (selectedProvider.toLowerCase() === 'rtorrent') {
                        client = 'rTorrent';
                        $('#host_desc_torrent').html(_('URL to your rTorrent client (e.g. scgi://localhost:5000 <br> '
                                                        + 'or https://localhost/rutorrent/plugins/httprpc/action.php)'));
                        $('#torrent_verify_cert_option').show();
                        $('#torrent_auth_type_option').show();
                    } else if (selectedProvider.toLowerCase() === 'qbittorrent') {
                        client = 'qBittorrent';
                        $('#torrent_path_option').hide();
                        $('#label_warning_qbittorrent').show();
                        $('#label_anime_warning_qbittorrent').show();
                        $('#torrent_verify_cert_option').show();
                        $('#host_desc_torrent').text(_('URL to your qBittorrent client (e.g. http://localhost:8080)'));
                    } else if (selectedProvider.toLowerCase() === 'mlnet') {
                        client = 'mlnet';
                        $('#torrent_path_option').hide();
                        $('#torrent_label_option').hide();
                        $('#torrent_paused_option').hide();
                        $('#host_desc_torrent').text(_('URL to your MLDonkey (e.g. http://localhost:4080)'));
                    } else if (selectedProvider.toLowerCase() === 'putio') {
                        client = 'putio';
                        $('#torrent_path_option').hide();
                        $('#torrent_label_option').hide();
                        $('#torrent_paused_option').hide();
                        $('#torrent_host_option').hide();
                        $('#host_desc_torrent').text(_('URL to your putio client (e.g. http://localhost:8080)'));
                        $('label[for="torrent_password"]').html(
                            '<a href="' + anonURL + 'https://app.put.io/oauth/apps/new" target="_blank">'
                            + _('Create a new OAuth app for put.io') + '</a>');
                        $('#username_title.component-title').text(_('Put.io Parent Folder'));
                        $('#password_title.component-title').text(_('Put.io OAuth Token'));
                    }

                    $('#host_title').text(client + ' host:port');
                    $('#username_title').text(client + ' Username');
                    $('#password_title').text(client + ' Password');
                    $('#torrent_client').text(client);
                    $('#rpcurl_title').text(client + ' RPC URL');
                    optionPanel = '#options_torrent_clients';
                }

                $(optionPanel).show();
            };

            $('#torrent_host').on('input', () => {
                if ($('#torrent_method :selected').val().toLowerCase().startsWith('rtorrent')) {
                    const hostname = $('#torrent_host').val();
                    const isMatch = hostname.slice(0, 7) === 'scgi://';

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

                $.post(scRoot + '/home/testSABnzbd', {
                    host: sab.host,
                    username: sab.username,
                    password: sab.password,
                    apikey: sab.apiKey,
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

                $.post(scRoot + '/home/testDSM', {
                    host: dsm.host,
                    username: dsm.username,
                    password: dsm.password,
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
                $.post(scRoot + '/home/testTorrent', {
                    torrent_method: torrent.method, // eslint-disable-line camelcase
                    host: torrent.host,
                    username: torrent.username,
                    password: torrent.password,
                }, data => {
                    $('#test_torrent_result').html(data);
                });
            });
        },
        subtitles() {
            $.fn.showHideServices = function () {
                $('.serviceDiv').each(function () {
                    const serviceName = $(this).attr('id');
                    const selectedService = $('#editAService :selected').val();

                    if (selectedService + 'Div' === serviceName) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            };

            $.fn.addService = function (id, name, url, key, isDefault, showService) { // eslint-disable-line max-params
                if (url.match('/$') === null) {
                    url += '/';
                }

                if ($('#service_order_list > #' + id).length === 0 && showService !== false) {
                    let toAdd = '';
                    toAdd += '<li class="ui-state-default" id="' + id + '"> ';
                    toAdd += '<input type="checkbox" id="enable_' + id + '" class="service_enabler" CHECKED> ';
                    toAdd += '<a href="' + anonURL + url + '" class="imgLink" target="_new">';
                    toAdd += '<img src="' + scRoot + '/images/services/newznab.gif" alt="' + name + '" width="16" height="16"></a> ';
                    toAdd += name + '</li>';

                    $('#service_order_list').append(toAdd);
                    $('#service_order_list').sortable('refresh');
                }
            };

            $.fn.deleteService = function (id) {
                $('#service_order_list > #' + id).remove();
            };

            $.fn.refreshServiceList = function () {
                const idArray = $('#service_order_list').sortable('toArray');
                const finalArray = [];
                $.each(idArray, (key, value) => {
                    const checked = $('#enable_' + value).is(':checked') ? '1' : '0';
                    finalArray.push(value + ':' + checked);
                });
                $('#service_order').val(finalArray.join(' '));
            };

            $('#editAService').on('change', function () {
                $(this).showHideServices();
            });

            $('.service_enabler').on('click', function () {
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
                },
            });

            $('#service_order_list').disableSelection();
        },
        providers() {
            // @TODO This function need to be filled with ConfigProviders.js but can't be as we've got scope issues currently.
            console.log('This function need to be filled with ConfigProviders.js but can\'t be as we\'ve got scope issues currently.');
        },
    },
    home: {
        init() {
            // Reset the layout for the activated tab (when using ui tabs)
            $('#showTabs').tabs({
                activate() {
                    $('.show-grid').isotope('layout');
                },
            });
        },
        index() {
            // Resets the tables sorting, needed as we only use a single call for both tables in tablesorter
            $('.resetsorting').on('click', () => {
                $('table').trigger('filterReset');
            });

            // Handle filtering in the poster layout
            $('#filterShowName').on('input', __.debounce(() => {
                $('.show-grid').isotope({
                    filter() {
                        const name = $(this).find('.show-title').html().trim().toLowerCase();
                        return name.includes($('#filterShowName').val().toLowerCase());
                    },
                });
            }, 500));

            function resizePosters(newSize) {
                let fontSize = 0;
                let logoWidth = 0;
                let borderRadius = 0;
                let borderWidth = 0;

                if (newSize < 125) { // Small
                    borderRadius = 3;
                    borderWidth = 4;
                } else if (newSize < 175) { // Medium
                    fontSize = 9;
                    logoWidth = 40;
                    borderRadius = 4;
                    borderWidth = 5;
                } else { // Large
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
                    borderWidth,
                    borderRadius,
                });
            }

            let posterSize;
            if (typeof (Storage) !== 'undefined') {
                posterSize = Number.parseInt(localStorage.getItem('posterSize'), 10);
            }

            if (typeof (posterSize) !== 'number' || Number.isNaN(posterSize)) {
                posterSize = 188;
            }

            resizePosters(posterSize);

            $('#posterSizeSlider').slider({
                min: 75,
                max: 250,
                value: posterSize,
                change(event, ui) {
                    if (typeof (Storage) !== 'undefined') {
                        localStorage.setItem('posterSize', ui.value);
                    }

                    resizePosters(ui.value);
                    $('.show-grid').isotope('layout');
                },
            });

            $('#rootDirSelect').on('change', () => {
                $('#rootDirForm').submit();
            });

            // This needs to be refined to work a little faster.
            $('.progressbar').each(function () {
                const percentage = $(this).data('progress-percentage');
                const classToAdd = Math.max(20, percentage - (percentage % 20));
                $(this).progressbar({value: percentage});
                if ($(this).data('progress-text')) {
                    $(this).append('<div class="progressbarText" title="' + $(this).data('progress-tip') + '">' + $(this).data('progress-text') + '</div>');
                }

                $(this).find('.ui-progressbar-value').addClass('progress-' + classToAdd);
            });

            $('img#network').on('error', function () {
                $(this).parent().text($(this).attr('alt'));
                $(this).remove();
            });

            $('#showListTableShows:has(tbody tr), #showListTableAnime:has(tbody tr)').tablesorter({
                sortList: [[7, 1], [2, 0]],
                textExtraction: {
                    0(node) {
                        return $(node).find('time').attr('datetime');
                    },
                    1(node) {
                        return $(node).find('time').attr('datetime');
                    },
                    2(node) {
                        return latinize($(node).text().normalize('NFC'));
                    },
                    3(node) {
                        return ($(node).find('span').prop('title') || 'zunknown').toLowerCase();
                    },
                    4(node) {
                        return $(node).find('span').text().toLowerCase();
                    },
                    5(node) {
                        const progress = $(node).find('div').attr('data-progress-sort');
                        return progress === undefined ? Number.NEGATIVE_INFINITY : (progress.length > 0 && Number.parseFloat(progress)) || Number.NEGATIVE_INFINITY;
                    },
                    6(node) {
                        return $(node).data('show-size');
                    },
                    7(node) {
                        return ($(node).find('span').attr('title') || 'No').toLowerCase();
                    },
                },
                widgets: ['saveSort', 'zebra', 'stickyHeaders', 'filter', 'columnSelector'],
                headers: {
                    0: {sorter: 'realISODate'},
                    1: {sorter: 'realISODate'},
                    2: {sorter: 'loadingNames'},
                    4: {sorter: 'quality'},
                    5: {sorter: 'digit'},
                    6: {sorter: 'digit'},
                    7: {filter: 'parsed'},
                },
                widgetOptions: {
                    filter_columnFilters: true, // eslint-disable-line camelcase
                    filter_hideFilters: true, // eslint-disable-line camelcase
                    stickyHeaders_offset: 50, // eslint-disable-line camelcase
                    filter_saveFilters: false, // eslint-disable-line camelcase
                    filter_functions: { // eslint-disable-line camelcase
                        // HOWTO: https://mottie.github.io/tablesorter/docs/example-widget-filter-custom.html#notes
                        5(exact, normalized, filterInput) {
                            let test = false;
                            const pct = Math.floor((normalized % 1) * 1000);
                            const doCompare = {
                                '<'(a, b) {
                                    return a < b;
                                },
                                '<='(a, b) {
                                    return a <= b;
                                },
                                '>='(a, b) {
                                    return a >= b;
                                },
                                '>'(a, b) {
                                    return a > b;
                                },
                            };

                            if (filterInput === '') {
                                test = true;
                            } else {
                                let result = filterInput.match(/(<|<=|>=|>)\s?(\d+)/i);
                                if (result) {
                                    // Compare using the matched operator
                                    const comp = doCompare[result[1]];
                                    if (comp(pct, Number.parseInt(result[2], 10))) {
                                        test = true;
                                    }
                                }

                                result = filterInput.match(/(\d+)\s(-|to)\s+(\d+)/i);
                                if (result && ((result[2] === '-') || (result[2] === 'to')) && (pct >= Number.parseInt(result[1], 10)) && (pct <= Number.parseInt(result[3], 10))) {
                                    test = true;
                                }

                                result = filterInput.match(/(=)?\s?(\d+)\s?(=)?/i);
                                if (result && ((result[1] === '=') || (result[3] === '=')) && Number.parseInt(result[2], 10) === pct) {
                                    test = true;
                                }

                                if (!Number.isNaN(Number.parseFloat(filterInput)) && Number.isFinite(filterInput) && Number.parseInt(filterInput, 10) === pct) {
                                    test = true;
                                }
                            }

                            return test;
                        },
                    },
                    columnSelector_mediaquery: false, // eslint-disable-line camelcase
                },
                sortStable: true,
                sortAppend: [[2, 0]],
            });

            $('.show-grid').imagesLoaded(() => {
                const sort = getMeta('settings.POSTER_SORTBY') === 'date' ? ['status', 'date', 'name'] : getMeta('settings.POSTER_SORTBY');
                $('.loading-spinner').hide();
                $('.show-grid').show().isotope({
                    itemSelector: '.show-container',
                    sortBy: sort,
                    sortAscending: getMeta('settings.POSTER_SORTDIR'),
                    layoutMode: 'masonry',
                    masonry: {
                        isFitWidth: true,
                    },
                    getSortData: {
                        name(itemElement) {
                            const name = $(itemElement).attr('data-name') || '';
                            return latinize((metaToBool('settings.SORT_ARTICLE') ? name : name.replace(/^((?:the|a|an)\s)/i, '')).toLowerCase().normalize('NFC'));
                        },
                        network: '[data-network]',
                        date(itemElement) {
                            const date = $(itemElement).attr('data-date');
                            return (date.length > 0 && Number.parseInt(date, 10)) || Number.POSITIVE_INFINITY;
                        },
                        progress(itemElement) {
                            const progress = $(itemElement).attr('data-progress-sort');
                            return (progress.length > 0 && Number.parseFloat(progress)) || Number.NEGATIVE_INFINITY;
                        },
                        status: '[data-status]',
                    },
                });

                // When posters are small enough to not display the .show-details
                // table, display a larger poster when hovering.
                let posterHoverTimer = null;
                $('.show-container').on('mouseenter', function () {
                    const poster = $(this);
                    if (poster.find('.show-details').css('display') !== 'none') {
                        return;
                    }

                    posterHoverTimer = setTimeout(() => {
                        posterHoverTimer = null;
                        $('#posterPopup').remove();
                        const popup = poster.clone().attr({
                            id: 'posterPopup',
                        });
                        const origLeft = poster.offset().left;
                        const origTop = poster.offset().top;
                        popup.css({
                            position: 'absolute',
                            margin: 0,
                            top: origTop,
                            left: origLeft,
                            zIndex: 9999,
                        });

                        popup.find('.show-details').show();
                        popup.on('mouseleave', function () {
                            $(this).remove();
                        });
                        popup.appendTo('body');

                        const height = 438;
                        const width = 250;
                        let newTop = ((origTop + poster.height()) / 2) - (height / 2);
                        let newLeft = ((origLeft + poster.width()) / 2) - (width / 2);

                        // Make sure the popup isn't outside the viewport
                        const margin = 5;
                        const scrollTop = $(window).scrollTop();
                        const scrollLeft = $(window).scrollLeft();
                        const scrollBottom = scrollTop + $(window).innerHeight();
                        const scrollRight = scrollLeft + $(window).innerWidth();
                        if (newTop < scrollTop + margin) {
                            newTop = scrollTop + margin;
                        }

                        if (newLeft < scrollLeft + margin) {
                            newLeft = scrollLeft + margin;
                        }

                        if (newTop + height + margin > scrollBottom) {
                            newTop = scrollBottom - height - margin;
                        }

                        if (newLeft + width + margin > scrollRight) {
                            newLeft = scrollRight - width - margin;
                        }

                        popup.animate({
                            top: newTop,
                            left: newLeft,
                            width: 250,
                            height: 438,
                        });
                    }, 300);
                }).on('mouseleave', () => {
                    if (posterHoverTimer !== null) {
                        clearTimeout(posterHoverTimer);
                    }
                });
            });

            $('#layout').on('change', function () {
                window.location.href = $(this).find('option:selected').val();
            });

            $('#postersort').on('change', function () {
                $('.show-grid').isotope({sortBy: $(this).val() === 'date' ? ['status', 'date', 'name'] : $(this).val()});
                $.post($(this).find('option:selected').data('sort'));
            });

            $('#postersortdirection').on('change', function () {
                $('.show-grid').isotope({sortAscending: ($(this).val() === 'true')});
                $.post($(this).find('option:selected').data('sort'));
            });

            $('#popover').popover({
                placement: 'bottom',
                html: true, // Required if content has HTML
                content: '<div id="popover-target"></div>',
            }).on('shown.bs.popover', () => { // Bootstrap popover event triggered when the popover opens
                // call this function to copy the column selection code into the popover
                $.tablesorter.columnSelector.attachTo($('#showListTableShows'), '#popover-target');
                if (metaToBool('settings.ANIME_SPLIT_HOME')) {
                    $.tablesorter.columnSelector.attachTo($('#showListTableAnime'), '#popover-target');
                }
            });
        },
        displayShow() {
            if (metaToBool('settings.FANART_BACKGROUND')) {
                const backgroundPath = getMeta('showBackgroundImage') || scRoot + '/cache/images/' + $('#showID').attr('value') + '.fanart.jpg';
                $.backstretch(backgroundPath);
                $('.backstretch').css('opacity', getMeta('settings.FANART_BACKGROUND_OPACITY')).fadeIn('500');
            }

            $('.displayShowTable').tablesorter({
                widgets: ['saveSort', 'stickyHeaders', 'columnSelector'],
                widgetOptions: {
                    columnSelector_saveColumns: true, // eslint-disable-line camelcase
                    columnSelector_layout: '<label><input type="checkbox"/>{name}</label>', // eslint-disable-line camelcase
                    columnSelector_mediaquery: false, // eslint-disable-line camelcase
                    columnSelector_cssChecked: 'checked', // eslint-disable-line camelcase
                    stickyHeaders_offset: 50, // eslint-disable-line camelcase
                },
            });

            $('.displayShowTable').ajaxEpSearch({colorRow: true});

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

            $('.play-on-kodi').on('click', function () {
                if ($(this).prop('enableClick') === '0') {
                    return false;
                }

                const selectedEpisode = $(this);
                const playModal = $('#playOnKodiModal');

                $('#playOnKodiModal .btn.btn-success').on('click', () => {
                    disableLink(selectedEpisode);
                    playModal.modal('hide');

                    const img = selectedEpisode.children('img');
                    img.hide();

                    selectedEpisode.append($('<span/>').attr({class: 'loading-spinner16', title: 'Playing'}));
                    const icon = selectedEpisode.children('span');

                    const host = $('#kodi-play-host').val();
                    $.getJSON(selectedEpisode.prop('href') + '&host=' + host, data => {
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
                playModal.modal('show');
                return false;
            });

            $('.epSubtitlesSearch').on('click', function () {
                if ($(this).prop('enableClick') === '0') {
                    return false;
                }

                disableLink($(this));

                const parent = $(this).parent();
                const subtitlesTd = parent.siblings('.col-subtitles');

                const icon = $(this).children('span');
                icon.prop('class', 'loading-spinner16');
                icon.prop('title', 'Searching');

                $.getJSON($(this).attr('href'), function (data) {
                    if (data.result.toLowerCase() !== 'failure' && data.result.toLowerCase() !== 'no subtitles downloaded') {
                        // Clear and update the subtitles column with new information
                        const subtitles = data.subtitles.split(',');
                        subtitlesTd.empty();
                        $.each(subtitles, (index, language) => {
                            if (language !== '') {
                                subtitlesTd.append($('<img/>', {src: scRoot + '/images/subtitles/flags/' + language + '.png', alt: language, width: 16, height: 11}));
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

            $('.epRetrySubtitlesSearch').on('click', function () {
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

            $('#seasonJump').on('change', () => {
                const $seasonJumpOpt = $('#seasonJump option:selected');
                const id = $seasonJumpOpt.val();
                if (id && id !== 'jump') {
                    const season = $seasonJumpOpt.data('season');
                    $('html,body').animate({scrollTop: $('#' + id.slice(1)).offset().top - 50}, 'slow');
                    $('#collapseSeason-' + season).collapse('show');
                    location.hash = id;
                }

                $(this).val('jump');
            });

            $('#seasonJumpLinks a').on('click', ev => {
                const season = $(ev.target).data('season');
                $('html,body').animate({scrollTop: $('#' + season).offset().top - 50}, 'slow');
                $('#collapseSeason-' + season).collapse('show');
                location.hash = season;
                return false;
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
                const epArray = [];

                $('.epCheck').each(function () {
                    if (this.checked === true) {
                        epArray.push($(this).attr('id'));
                    }
                });

                if (epArray.length === 0) {
                    return false;
                }

                const url = scRoot + '/home/setStatus';
                const parameters = 'show=' + $('#showID').attr('value') + '&eps=' + epArray.join('|') + '&status=' + $('#statusSelect').val();
                $.post(url, parameters, () => {
                    location.reload(true);
                });
            });

            $('.seasonCheck').on('click', function () {
                const seasCheck = this.checked;
                const seasNo = $(this).attr('id');
                $('#collapseSeason-' + seasNo).collapse('show');
                $('.epCheck:visible[id^="' + seasNo + 'x"]').each(function () {
                    this.checked = seasCheck;
                });
            });

            let lastCheck = null;
            $('.epCheck').on('click', function (event) {
                if (!lastCheck || !event.shiftKey) {
                    lastCheck = this; // eslint-disable-line unicorn/no-this-assignment
                    return;
                }

                const check = this; // eslint-disable-line unicorn/no-this-assignment
                let found = 0;

                $('.epCheck').each(function () {
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
                $('.epCheck:visible').each(function () {
                    this.checked = true;
                });
                $('.seasonCheck:visible').each(function () {
                    this.checked = true;
                });
            });

            // Clears all visible episode checkboxes and the season selectors
            $('.clearAll').on('click', () => {
                $('.epCheck:visible').each(function () {
                    this.checked = false;
                });
                $('.seasonCheck:visible').each(function () {
                    this.checked = false;
                });
            });

            // Handle the show selection dropbox
            $('#pickShow').on('change', function () {
                const value = $(this).val();
                if (value === 0) {
                    return;
                }

                window.location.href = scRoot + '/home/displayShow?show=' + value;
            });

            // Show/hide different types of rows when the checkboxes are changed
            $('#checkboxControls input').on('change', function () {
                const whichClass = $(this).attr('id');
                $(this).showHideRows(whichClass);
            });

            // Initially show/hide all the rows according to the checkboxes
            $('#checkboxControls input').each(function () {
                const status = $(this).is(':checked');
                $('tr.' + $(this).attr('id')).each(function () {
                    if (status) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            });

            $.fn.showHideRows = function (whichClass) {
                const status = $('#checkboxControls > input, #' + whichClass).is(':checked');
                $('tr.' + whichClass).each(function () {
                    if (status) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });

                // Hide season headers with no episodes under them
                $('div.seasonheader').each(function () {
                    let numberRows = 0;
                    const seasonNo = $(this).attr('data-season-id');
                    $('tr.season-' + seasonNo + ' :visible').each(() => {
                        numberRows++;
                    });
                    if (numberRows === 0) {
                        $(this).hide();
                        $('#' + seasonNo + '-cols').hide();
                    } else {
                        $(this).show();
                        $('#' + seasonNo + '-cols').show();
                    }
                });
            };

            function setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode) {
                const showId = $('#showID').val();
                const indexer = $('#indexer').val();

                if (sceneSeason === '') {
                    sceneSeason = null;
                }

                if (sceneEpisode === '') {
                    sceneEpisode = null;
                }

                $.getJSON(scRoot + '/home/setSceneNumbering', {
                    show: showId,
                    indexer,
                    forSeason,
                    forEpisode,
                    sceneSeason,
                    sceneEpisode,
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
                const showId = $('#showID').val();
                const indexer = $('#indexer').val();

                if (sceneAbsolute === '') {
                    sceneAbsolute = null;
                }

                $.getJSON(scRoot + '/home/setSceneNumbering', {
                    show: showId,
                    indexer,
                    forAbsolute,
                    sceneAbsolute,
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

            function setInputValidInvalid(valid, element) {
                if (valid) {
                    $(element).css({'background-color': '#90EE90', color: '#FFF', 'font-weight': 'bold'}); // Green
                    return true;
                }

                $(element).css({'background-color': '#FF0000', color: '#FFF!important', 'font-weight': 'bold'}); // Red
                return false;
            }

            $('.sceneSeasonXEpisode').on('change', function () {
                // Strip non-numeric characters
                $(this).val($(this).val().replace(/[^\dxX]*/g, ''));
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

            $('.sceneAbsolute').on('change', function () {
                // Strip non-numeric characters
                $(this).val($(this).val().replace(/[^\dxX]*/g, ''));
                const forAbsolute = $(this).attr('data-for-absolute');

                const m = $(this).val().match(/^(\d{1,3})$/i);
                let sceneAbsolute = null;
                if (m) {
                    sceneAbsolute = m[1];
                }

                setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute);
            });

            $('.addQTip').each(function () {
                $(this).css({cursor: 'help', 'text-shadow': '0px 0px 0.5px #666'});
                $(this).qtip({
                    show: {solo: true},
                    position: {viewport: $(window), my: 'left center', adjust: {y: -10, x: 2}},
                    style: {tip: {corner: true, method: 'polygon'}, classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'},
                });
            });
            $.fn.generateStars = function () {
                return this.each((i, element) => {
                    $(element).html($('<span/>').width($(element).text() * 12));
                });
            };

            $('.imdbstars').generateStars();

            $('#popover').popover({
                placement: 'bottom',
                html: true, // Required if content has HTML
                content: '<div id="popover-target"></div>',
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
                $('.collapse.toggle').on('hide.bs.collapse', function () {
                    const reg = /collapseSeason-(\d+)/g;
                    const result = reg.exec(this.id);
                    $('#showseason-' + result[1]).text(_('Show Episodes'));
                });
                $('.collapse.toggle').on('show.bs.collapse', function () {
                    const reg = /collapseSeason-(\d+)/g;
                    const result = reg.exec(this.id);
                    $('#showseason-' + result[1]).text(_('Hide Episodes'));
                });
            });
        },
        editShow() {
            $('#location').fileBrowser({title: _('Select Show Location')});

            SICKCHILL.common.QualityChooser.init();

            // @TODO: Make anime button work like in addShow (opens the groups list without a refresh)
            /* $('#anime').change (function() {
                SICKCHILL.common.updateBlackWhiteList(getMeta('show.name'));
            }); */

            $('#submit').on('click', () => {
                const allExceptions = $('#exceptions_list').find('optgroup').get().map(group => {
                    const season = $(group).data('season');
                    const exceptions = $(group).find('option:enabled').get().map(option => {
                        const exception = $(option).val();

                        return encodeURIComponent(exception);
                    }).join('|');

                    if (exceptions.length === 0) {
                        return null;
                    }

                    return [season, exceptions].join(':');
                }).filter(item => item);

                $('#exceptions').val(allExceptions);

                if (metaToBool('show.is_anime')) {
                    generateBlackWhiteList(); // eslint-disable-line no-undef
                }
            });

            $('#addSceneName').on('click', () => {
                const season = $('#SceneSeason').find(':selected').data('season');
                const sceneEx = $('#SceneName').val();

                const group = $('.exceptions_list optgroup[data-season="' + season + '"]').get()[0];
                const placeholder = $(group).find('option.empty');

                const exceptions = new Set($(group).find('option:not(.empty)').get().map(element => $(element).val()));

                // If we already have the exception or the field is empty return
                if (exceptions.has(sceneEx) || sceneEx.trim() === '') {
                    $('#SceneName').val('');
                    return;
                }

                const newException = $('<option data-season=' + season + '>').text(sceneEx).val(sceneEx);

                $(group).append(newException);
                placeholder.remove();

                $('#SceneName').val('');
            });

            $('#removeSceneName').on('click', () => {
                const option = $('#exceptions_list').find('option:selected');
                const group = option.closest('optgroup');

                if (group.find('option').length < 2) {
                    const newOption = $('<option disabled class="empty">');
                    newOption.text(_('None'));

                    group.append(newOption);
                }

                option.remove();
            });

            $('.custom-image').imageSelector();
        },
        manual_search_show_releases() { // eslint-disable-line camelcase
            $('#manualSearchShowTable:has(tbody tr)').tablesorter({
                widgets: ['zebra', 'filter'],
                textExtraction: (function () {
                    return {
                        0(node) { // Provider
                            return $(node).attr('title');
                        },
                    };
                })(),
                headers: (function () {
                    return {
                        3: {sorter: 'quality'},
                        4: {sorter: 'metric'},
                        7: {sorter: false, filter: false},
                    };
                })(),
                widgetOptions: {
                    filter_hideFilters: true, // eslint-disable-line camelcase
                },
            });
        },
        postProcess() {
            $('#episodeDir').fileBrowser({
                title: _('Select Unprocessed Episode Folder'),
                key: 'postprocessPath',
            });
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
                    },
                },
                headers: {
                    5: {sorter: 'digit'},
                    6: {sorter: 'digit'},
                },
            });
            $('#queueStatusTable').tablesorter({
                widgets: ['saveSort', 'zebra'],
                sortList: [[3, 0], [4, 0], [2, 1]],
            });
        },
        restart() {
            let currentPid = srPID;
            let checkIsAlive = setTimeout(() => {
                setInterval(() => {
                    $.post(scRoot + '/home/is-alive/', data => {
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
                            srPID = data.msg;
                            currentPid = data.msg;
                            checkIsAlive = setInterval(() => {
                                $.post(scRoot + '/home/is-alive/', () => { // eslint-disable-line max-nested-callbacks
                                    clearInterval(checkIsAlive);
                                    setTimeout(() => { // eslint-disable-line max-nested-callbacks
                                        window.location = scRoot + '/' + srDefaultPage + '/';
                                    }, 3000);
                                }, 'jsonp');
                            }, 1000);
                        }
                    }, 'jsonp').fail(() => {
                        $('#restart_message').show();
                        $('#shut_down_loading').hide();
                        $('#shut_down_success').show();
                    });
                }, 1000);
            }, 5000);
        },
    },
    manage: {
        init() {
            $.makeEpisodeRow = function (indexerId, season, episode, name, checked) { // eslint-disable-line max-params
                let row = '';
                row += ' <tr class="' + $('#row_class').val() + ' show-' + indexerId + '">';
                row += '  <td class="tableleft" align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
                row += '  <td>' + season + 'x' + episode + '</td>';
                row += '  <td class="tableright" style="width: 100%">' + name + '</td>';
                row += ' </tr>';

                return row;
            };

            $.makeSubtitleRow = function (indexerId, season, episode, name, subtitles, checked) { // eslint-disable-line max-params
                let row = '';
                row += '<tr class="good show-' + indexerId + '">';
                row += '<td align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
                row += '<td style="width: 2%;">' + season + 'x' + episode + '</td>';
                if (subtitles.length > 0) {
                    row += '<td style="width: 8%;">';
                    subtitles = subtitles.split(',');
                    for (const i in subtitles) {
                        if ({}.hasOwnProperty.call(subtitles, i)) {
                            row += '<img src="' + scRoot + '/images/subtitles/flags/' + subtitles[i] + '.png" width="16" height="11" alt="' + subtitles[i] + '" />&nbsp;';
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
                    2(node) { // Network
                        return ($(node).find('img').attr('alt') || 'unknown').toLowerCase();
                    },
                    3(node) { // Quality
                        return $(node).find('span').attr('title').toLowerCase();
                    },
                    4(node) { // Sports
                        return $(node).find('span').attr('title').toLowerCase();
                    },
                    5(node) { // Scene
                        return $(node).find('span').attr('title').toLowerCase();
                    },
                    6(node) { // Anime
                        return $(node).find('span').attr('title').toLowerCase();
                    },
                    7(node) { // Season Folders
                        return $(node).find('span').attr('title').toLowerCase();
                    },
                    8(node) { // Paused
                        return $(node).find('span').attr('title').toLowerCase();
                    },
                    9(node) { // Subtitle
                        return $(node).find('span').attr('title').toLowerCase();
                    },
                    10(node) { // Default Episode Status
                        return $(node).text().toLowerCase();
                    },
                    11(node) { // Show Status
                        return $(node).text().toLowerCase();
                    },
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
                    17: {sorter: false},
                },
                widgetOptions: {
                    columnSelector_mediaquery: false, // eslint-disable-line camelcase
                },
            });
            $('#popover').popover({
                placement: 'bottom',
                html: true, // Required if content has HTML
                content: '<div id="popover-target"></div>',
            }).on('shown.bs.popover', () => { // Bootstrap popover event triggered when the popover opens
                // call this function to copy the column selection code into the popover
                $.tablesorter.columnSelector.attachTo($('#massUpdateTable'), '#popover-target');
            });

            $('.submitMassEdit').on('click', () => {
                const editArray = [];

                $('.editCheck').each(function () {
                    if (this.checked === true) {
                        editArray.push($(this).attr('id').split('-')[1]);
                    }
                });

                if (editArray.length === 0) {
                    return;
                }

                const submitForm = $(
                    '<form method=\'post\' action=\'' + scRoot + '/manage/massEdit\'>'
                        + '<input type=\'hidden\' name=\'toEdit\' value=\'' + editArray.join('|') + '\'/>'
                    + '</form>',
                );
                submitForm.appendTo('body');

                submitForm.submit();
            });

            $('.submitMassUpdate').on('click', () => {
                const updateArray = [];
                const refreshArray = [];
                const renameArray = [];
                const subtitleArray = [];
                const deleteArray = [];
                const removeArray = [];
                const metadataArray = [];

                $('.updateCheck').each(function () {
                    if (this.checked === true) {
                        updateArray.push($(this).attr('id').split('-')[1]);
                    }
                });

                $('.refreshCheck').each(function () {
                    if (this.checked === true) {
                        refreshArray.push($(this).attr('id').split('-')[1]);
                    }
                });

                $('.renameCheck').each(function () {
                    if (this.checked === true) {
                        renameArray.push($(this).attr('id').split('-')[1]);
                    }
                });

                $('.subtitleCheck').each(function () {
                    if (this.checked === true) {
                        subtitleArray.push($(this).attr('id').split('-')[1]);
                    }
                });

                $('.removeCheck').each(function () {
                    if (this.checked === true) {
                        removeArray.push($(this).attr('id').split('-')[1]);
                    }
                });

                let deleteCount = 0;

                $('.deleteCheck').each(function () {
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
                            $('.deleteCheck').each(function () {
                                if (this.checked === true) {
                                    deleteArray.push($(this).attr('id').split('-')[1]);
                                }
                            });
                            if (updateArray.length + refreshArray.length + renameArray.length + subtitleArray.length + deleteArray.length + removeArray.length + metadataArray.length === 0) {
                                return false;
                            }

                            const url = scRoot + '/manage/massUpdate';
                            const parameters = 'toUpdate=' + updateArray.join('|') + '&toRefresh=' + refreshArray.join('|') + '&toRename=' + renameArray.join('|') + '&toSubtitle=' + subtitleArray.join('|') + '&toDelete=' + deleteArray.join('|') + '&toRemove=' + removeArray.join('|') + '&toMetadata=' + metadataArray.join('|');
                            $.post(url, parameters, () => {
                                location.reload(true);
                            });
                        },
                    });
                }

                if (updateArray.length + refreshArray.length + renameArray.length + subtitleArray.length + deleteArray.length + removeArray.length + metadataArray.length === 0) {
                    return false;
                }

                const url = scRoot + '/manage/massUpdate';
                const parameters = 'toUpdate=' + updateArray.join('|') + '&toRefresh=' + refreshArray.join('|') + '&toRename=' + renameArray.join('|') + '&toSubtitle=' + subtitleArray.join('|') + '&toDelete=' + deleteArray.join('|') + '&toRemove=' + removeArray.join('|') + '&toMetadata=' + metadataArray.join('|');
                $.post(url, parameters, () => {
                    location.reload(true);
                });
            });

            for (const name of ['.editCheck', '.updateCheck', '.refreshCheck', '.renameCheck', '.deleteCheck', '.removeCheck']) {
                let lastCheck = null;

                $(name).on('click', function (event) {
                    if (!lastCheck || !event.shiftKey) {
                        lastCheck = this; // eslint-disable-line unicorn/no-this-assignment
                        return;
                    }

                    const check = this; // eslint-disable-line unicorn/no-this-assignment
                    let found = 0;

                    $(name).each(function () {
                        if (found === 2) {
                            return false;
                        }

                        if (found === 1 && !this.disabled) {
                            this.checked = lastCheck.checked;
                        }

                        if (this === check || this === lastCheck) {
                            found++;
                        }
                    });
                });
            }
        },
        backlogOverview() {
            $('#pickShow').on('change', event => {
                const id = $(event.currentTarget).val();
                if (id) {
                    $('html,body').animate({scrollTop: $('#show-' + id).offset().top - 25}, 'slow');
                }
            });
        },
        failedDownloads() {
            $('#failedTable:has(tbody tr)').tablesorter({
                widgets: ['zebra'],
                sortList: [[1, 0]],
                headers: {3: {sorter: false}},
            });
            $('#limit').on('change', event => {
                window.location.href = scRoot + '/manage/failedDownloads/?limit=' + $(event.currentTarget).val();
            });

            $('#submitMassRemove').on('click', () => {
                const removeArray = [];

                $('.removeCheck').each(function () {
                    if (this.checked === true) {
                        removeArray.push($(this).attr('id').split('-')[1]);
                    }
                });

                if (removeArray.length === 0) {
                    return false;
                }

                $.post(scRoot + '/manage/failedDownloads', 'toRemove=' + removeArray.join('|'), () => {
                    location.reload(true);
                });
            });

            if ($('.removeCheck').length > 0) {
                $('.removeCheck').each(name => {
                    let lastCheck = null;
                    $(name).on('click', function (event) {
                        if (!lastCheck || !event.shiftKey) {
                            lastCheck = this; // eslint-disable-line unicorn/no-this-assignment
                            return;
                        }

                        const check = this; // eslint-disable-line unicorn/no-this-assignment
                        let found = 0;

                        $(name + ':visible').each(function () {
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

            $('.new_root_dir').on('change', function () {
                const curIndex = findDirIndex($(this).attr('id'));
                $('#display_new_root_dir_' + curIndex).html('<b>' + $(this).val() + '</b>');
            });

            $('.edit_root_dir').on('click', function () {
                const curIndex = findDirIndex($(this).attr('id'));
                const initialDir = $('#new_root_dir_' + curIndex).val();
                $(this).nFileBrowser(editRootDir, {initialDir, whichId: curIndex});
            });

            $('.delete_root_dir').on('click', function () {
                const curIndex = findDirIndex($(this).attr('id'));
                $('#new_root_dir_' + curIndex).val(null);
                $('#display_new_root_dir_' + curIndex).html('<b>' + _('DELETED') + '</b>');
            });

            SICKCHILL.common.QualityChooser.init();
        },
        episodeStatuses() {
            $('.allCheck').on('click', function () {
                const indexerId = $(this).attr('id').split('-')[1];
                $('.' + indexerId + '-epcheck').prop('checked', $(this).is(':checked'));
            });

            $('.get_more_eps').on('click', function () {
                const curIndexerId = $(this).attr('id');
                const checked = $('#allCheck-' + curIndexerId).is(':checked');
                const lastRow = $('tr#' + curIndexerId);
                const clicked = $(this).attr('data-clicked');
                const action = $(this).attr('value');

                if (!clicked) {
                    $.getJSON(scRoot + '/manage/showEpisodeStatuses', {
                        indexer_id: curIndexerId, // eslint-disable-line camelcase
                        whichStatus: $('#oldStatus').val(),
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
                    $('.show-' + curIndexerId).hide();
                    $(this).prop('value', 'Expand');
                } else if (action.toLowerCase() === 'expand') {
                    $('.show-' + curIndexerId).show();
                    $(this).prop('value', 'Collapse');
                }
            });

            // Selects all visible episode checkboxes.
            $('.selectAllShows').on('click', () => {
                $('.allCheck').each(function () {
                    this.checked = true;
                });
                $('input[class*="-epcheck"]').each(function () {
                    this.checked = true;
                });
            });

            // Clears all visible episode checkboxes and the season selectors
            $('.deselectAllShows').on('click', () => {
                $('.allCheck').each(function () {
                    this.checked = false;
                });
                $('input[class*="-epcheck"]').each(function () {
                    this.checked = false;
                });
            });
        },
        subtitleMissed() {
            $('.allCheck').on('click', function () {
                const indexerId = $(this).attr('id').split('-')[1];
                $('.' + indexerId + '-epcheck').prop('checked', $(this).is(':checked'));
            });

            $('.get_more_eps').on('click', function () {
                const indexerId = $(this).attr('id');
                const checked = $('#allCheck-' + indexerId).is(':checked');
                const lastRow = $('tr#' + indexerId);
                const clicked = $(this).attr('data-clicked');
                const action = $(this).attr('value');

                if (!clicked) {
                    $.getJSON(scRoot + '/manage/showSubtitleMissed', {
                        indexer_id: indexerId, // eslint-disable-line camelcase
                        whichSubs: $('#selectSubLang').val(),
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
                    $('.show-' + indexerId).hide();
                    $(this).prop('value', 'Expand');
                } else if (action === 'Expand') {
                    $('.show-' + indexerId).show();
                    $(this).prop('value', 'Collapse');
                }
            });

            // @TODO these two should be able to be merged by using a generic class for the selector

            // selects all visible episode checkboxes.
            $('.selectAllShows').on('click', () => {
                $('.allCheck').each(function () {
                    this.checked = true;
                });
                $('input[class*="-epcheck"]').each(function () {
                    this.checked = true;
                });
            });

            // Clears all visible episode checkboxes and the season selectors
            $('.deselectAllShows').on('click', () => {
                $('.allCheck').each(function () {
                    this.checked = false;
                });
                $('input[class*="-epcheck"]').each(function () {
                    this.checked = false;
                });
            });
        },
    },
    history: {
        init() {},
        index() {
            $('#historyTable:has(tbody tr)').tablesorter({
                widgets: ['zebra', 'filter'],
                sortList: [[0, 1]],
                textExtraction: (function () {
                    if (isMeta('settings.HISTORY_LAYOUT', ['detailed'])) {
                        return {
                            0(node) { // Time
                                return $(node).find('time').attr('datetime');
                            },
                            4(node) { // Quality
                                return $(node).find('span').text().toLowerCase();
                            },
                        };
                    }

                    const compactExtract = {
                        0(node) { // Time
                            return $(node).find('time').attr('datetime');
                        },
                        2(node) { // Provider
                            return $(node).attr('provider').toLowerCase();
                        },
                    };

                    if (isMeta('settings.USE_SUBTITLES', ['True'])) {
                        compactExtract[4] = function (node) { // Subtitles
                            return $(node).find('img').attr('title');
                        };

                        compactExtract[5] = function (node) { // Quality
                            return $(node).find('span').text().toLowerCase();
                        };
                    } else {
                        compactExtract[4] = function (node) { // Quality
                            return $(node).find('span').text().toLowerCase();
                        };
                    }

                    return compactExtract;
                })(),
                headers: (function () {
                    if (isMeta('settings.HISTORY_LAYOUT', ['detailed'])) {
                        return {
                            0: {sorter: 'realISODate'},
                            1: {sorter: 'loadingNames'},
                            4: {sorter: 'quality'},
                            5: {sorter: false, filter: false},
                        };
                    }

                    if (isMeta('settings.USE_SUBTITLES', ['True'])) {
                        return {
                            0: {sorter: 'realISODate'},
                            1: {sorter: 'loadingNames'},
                            4: {sorter: false},
                            5: {sorter: 'quality'},
                            6: {sorter: false, filter: false},
                        };
                    }

                    return {
                        0: {sorter: 'realISODate'},
                        1: {sorter: 'loadingNames'},
                        4: {sorter: 'quality'},
                        5: {sorter: false, filter: false},
                    };
                })(),
            });

            $('#layout').on('change', function () {
                window.location.href = $(this).find('option:selected').val();
            });

            $('#history_limit').on('change', function () {
                window.location.href = scRoot + '/history/?limit=' + $(this).val();
            });

            $('a.removehistory').on('click', () => {
                const removeArray = [];
                let removeCount = 0;

                $('.removeCheck').each(function () {
                    if (this.checked === true) {
                        removeArray.push(shiftReturn($(this).attr('id').split('-')));
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
                        const url = scRoot + '/history/removeHistory';
                        const parameters = 'toRemove=' + removeArray.join('|');
                        $.post(url, parameters, () => {
                            location.reload(true);
                        });
                    },
                });

                return false;
            });

            for (const name of ['.removeCheck']) {
                let lastCheck = null;

                $(name).on('click', function (event) {
                    if (!lastCheck || !event.shiftKey) {
                        lastCheck = this; // eslint-disable-line unicorn/no-this-assignment
                        return;
                    }

                    const check = this; // eslint-disable-line unicorn/no-this-assignment
                    let found = 0;

                    $(name).each(function () {
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
            }
        },
    },
    errorlogs: {
        init() {},
        index() {},
        viewlogs() {
            $('#min_level,#log_filter,#log_search').on('keyup change', __.debounce(() => {
                if ($('#log_search').val().length > 0) {
                    $('#log_filter option[value="<NONE>"]').prop('selected', true);
                    $('#min_level option[value=5]').prop('selected', true);
                }

                $('#min_level').prop('disabled', true);
                $('#log_filter').prop('disabled', true);
                document.body.style.cursor = 'wait';
                const url = scRoot + '/errorlogs/viewlog/';
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
                    const url = scRoot + '/errorlogs/viewlog/';
                    $.post(url, postData, data => {
                        $('pre').html($(data).find('pre').html());
                    });
                }

                setTimeout(updateLogData, 500);
            }

            updateLogData();

            $('#log_update_toggle').on('click', function () {
                const wasActive = $(this).data('state') === 'active'; // State before clicking
                $(this).data('state', wasActive ? 'paused' : 'active');
                $(this).find('i').toggleClass('fa-pause fa-play');
                $(this).find('span').text(wasActive ? _('Resume') : _('Pause'));
                $(this).attr('title', wasActive ? _('Resume updating the log on this page.') : _('Pause updating the log on this page.'));
                return false;
            });
        },
    },
    schedule: {
        init() {
            // Set webcal link for calendar subscription
            $('.btn-cal-subscribe').attr('href', document.location.href.replace(/https?/, 'webcal').replace(/schedule.*/, 'calendar'));
        },
        index() {
            if (isMeta('settings.COMING_EPS_LAYOUT', ['list'])) {
                const sortCodes = {date: 0, show: 2, network: 5};
                const sort = getMeta('settings.COMING_EPS_SORT');
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
                        2(node) {
                            return latinize($(node).text().normalize('NFC'));
                        },
                        7(node) {
                            return $(node).find('span').text().toLowerCase();
                        },
                    },
                    headers: {
                        0: {sorter: 'realISODate'},
                        1: {sorter: 'realISODate'},
                        2: {sorter: 'loadingNames'},
                        4: {sorter: 'loadingNames'},
                        7: {sorter: 'quality'},
                        8: {sorter: false},
                        9: {sorter: false},
                    },
                    widgetOptions: {
                        filter_columnFilters: true, // eslint-disable-line camelcase
                        filter_hideFilters: true, // eslint-disable-line camelcase
                        filter_saveFilters: false, // eslint-disable-line camelcase
                        columnSelector_mediaquery: false, // eslint-disable-line camelcase
                        stickyHeaders_offset: 50, // eslint-disable-line camelcase
                    },
                });

                $(document).ajaxEpSearch();
            }

            if (isMeta('settings.COMING_EPS_LAYOUT', ['banner', 'poster'])) {
                $(document).ajaxEpSearch();
                $('.ep_summary').hide();
                $('.ep_summaryTrigger').on('click', function () {
                    $(this).next('.ep_summary').slideToggle('normal', function () {
                        $(this).prev('.ep_summaryTrigger').attr('src', function (i, src) {
                            return $(this).next('.ep_summary').is(':visible') ? src.replace('plus', 'minus') : src.replace('minus', 'plus');
                        });
                    });
                });
            }

            $('#popover').popover({
                placement: 'bottom',
                html: true, // Required if content has HTML
                content: '<div id="popover-target"></div>',
            }).on('shown.bs.popover', () => { // Bootstrap popover event triggered when the popover opens
                // call this function to copy the column selection code into the popover
                $.tablesorter.columnSelector.attachTo($('#showListTable'), '#popover-target');
            });

            $('#sort, #viewpaused, #viewsnatched, #layout').on('change', function () {
                window.location.href = $(this).find('option:selected').val();
            });
        },
    },
    addShows: {
        init() {
            $('#tabs').tabs({
                collapsible: true,
                selected: (metaToBool('settings.SORT_ARTICLE') ? -1 : 0),
            });

            $.initRemoteShowGrid = function () {
                // Set defaults on page load
                $('#showsort').val('original');
                $('#showsortdirection').val('asc');

                $('#showsort').on('change', function () {
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
                        case 'rank':
                            sortCriteria = 'rank';
                            break;
                        default:
                            sortCriteria = 'name';
                            break;
                    }

                    $('#container').isotope({
                        sortBy: sortCriteria,
                    });
                });

                $('#showsortdirection').on('change', function () {
                    $('#container').isotope({
                        sortAscending: (this.value === 'asc'),
                    });
                });

                $('#container').isotope({
                    sortBy: 'original-order',
                    layoutMode: 'fitRows',
                    getSortData: {
                        name(itemElement) {
                            const name = $(itemElement).attr('data-name') || '';
                            return (metaToBool('settings.SORT_ARTICLE') ? name : name.replace(/^((?:the|a|an)\s)/i, '')).toLowerCase();
                        },
                        rating: '[data-rating] parseInt',
                        votes: '[data-votes] parseInt',
                        rank: '[data-rank] parseInt',
                    },
                });
            };

            $.loadTraktImages = function () {
                const url = scRoot + '/addShows/getTrendingShowImage';
                let ajaxCount = 0;
                $('img.trakt-image').each(function () {
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

            $.fn.loadRemoteShows = function (path, loadingTxt, errorTxt) {
                $(this).html('<img id="searchingAnim" src="' + scRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" />&nbsp;' + loadingTxt);
                $(this).load(scRoot + path + ' #container', function (response, status) {
                    if (status === 'error') {
                        $(this).empty().html(errorTxt);
                    } else {
                        $.initRemoteShowGrid();
                        $.loadTraktImages();
                    }
                });
            };

            $('#saveDefaultsButton').on('click', function () {
                const anyQualArray = [];
                const bestQualArray = [];
                $('#anyQualities option:selected').each((i, d) => {
                    anyQualArray.push($(d).val());
                });
                $('#bestQualities option:selected').each((i, d) => {
                    bestQualArray.push($(d).val());
                });

                $.post(scRoot + '/config/general/saveAddShowDefaults', {
                    defaultStatus: $('#statusSelect').val(),
                    anyQualities: anyQualArray.join(','),
                    bestQualities: bestQualArray.join(','),
                    defaultSeasonFolders: $('#season_folders').is(':checked'),
                    subtitles: $('#subtitles').is(':checked'),
                    anime: $('#anime').is(':checked'),
                    scene: $('#scene').is(':checked'),
                    defaultStatusAfter: $('#statusSelectAfter').val(),
                });

                $(this).attr('disabled', true);
            });

            $('#statusSelect, #qualityPreset, #season_folders, #anyQualities, #bestQualities, #subtitles, #scene, #anime, #statusSelectAfter').on('change', () => {
                $('#saveDefaultsButton').attr('disabled', false);
            });

            SICKCHILL.common.QualityChooser.init();
        },
        index() {},
        newShow() {
            const updateSampleText = function () {
                // If something's selected then we have some behavior to figure out
                const object = {
                    showName: '',
                    dir: 'unknown dir.',
                    sepChar: '',
                };

                // If they've picked a radio button then use that
                if ($('input:radio[name=whichSeries]:checked').length > 0) {
                    object.showName = $('input:radio[name=whichSeries]:checked').val().split('|')[4];
                } else if ($('input:hidden[name=whichSeries]').length > 0 && $('input:hidden[name=whichSeries]').val().length > 0) {
                    // If we provided a show in the hidden field, use that
                    object.showName = $('#providedName').val();
                }

                SICKCHILL.common.updateBlackWhiteList(object.showName);

                // If we have a root dir selected, figure out the path
                if ($('#rootDirs option:selected').length > 0) {
                    object.dir = $('#rootDirs option:selected').val();

                    if (object.dir.includes('/')) {
                        object.sepChar = '/';
                    } else if (object.dir.includes('\\')) {
                        object.sepChar = '\\';
                    }

                    object.dir.trim(object.sepChar);
                    object.dir += object.sepChar;
                } else if ($('#fullShowPath').val()) {
                    object.dir = $('#fullShowPath').val();
                }

                // If we have a show name then sanitize and use it for the dir name
                if (object.showName.length > 0) {
                    $.post(scRoot + '/addShows/sanitizeFileName', {name: object.showName}, data => {
                        $('#desc-show-name').text(object.showName);
                        if (object.dir === $('#fullShowPath').val()) {
                            $('#desc-directory-name').html(object.dir);
                        } else {
                            $('#desc-directory-name').html(object.dir + data + object.sepChar);
                        }
                    });
                } else { // If not then it's unknown
                    $('#desc-show-name').text(object.showName);
                    $('#desc-directory-name').html(object.dir);
                }

                $('#desc-quality-name').text($('#qualityPreset option:selected').text());

                // If show has been selected
                if (!($('input:radio[name=whichSeries]:checked').val() || $('input:hidden[name=whichSeries]').val())) {
                    return $('#addShowButton').attr('disabled', true);
                }

                // If root dir has been set properly
                if (!($('#rootDirs option:selected').val() || $('#fullShowPath').val())) {
                    return $('#addShowButton').attr('disabled', true);
                }

                $('#addShowButton').attr('disabled', false);
            };

            const showGroupPicker = function () {
                $('#blackwhitelist').toggle($('#anime').prop('checked'));
            };

            const buildTable = function (shows) {
                let table
                    = '<div class="row">'
                    + '<div class="col-lg-6 col-md-12">'
                    + '<table class="sickchillTable new-show-table tablesorter">'
                    + '<thead>'
                    + '<tr>'
                    + '<th></th>'
                    + '<th>Show Name</th>'
                    + '<th>Premiere</th>'
                    + '<th>Indexer</th>'
                    + '</tr>'
                    + '</thead>'
                    + '<tbody>';

                const selectedIndex = shows.indexOf(show => !show.inShowList);

                for (const [index, show] of shows.entries()) {
                    table
                        += '<tr class="' + (show.inShowList ? 'in-list' : '') + '">'
                        + '<td>'
                        + '<input type="radio" class="whichSeries" name="whichSeries" value="' + show.obj + '" '
                        + (selectedIndex === index ? 'checked ' : '') + (show.inShowList ? 'disabled' : '') + '/>'
                        + '</td>'
                        + '<td>'
                        + (function () {
                            let string = '<a href=';
                            string += show.inShowList ? '"/home/displayShow?show=' + show.id + '"' : '"' + show.url + '" target="_blank"';

                            string += '>' + show.title + '</a>';

                            return string;
                        })()
                        + '</td>'
                        + '<td>' + show.debut + '</td>'
                        + '<td>' + show.indexer + '</td>'
                        + '</tr>';
                }

                table
                    += '</tbody>'
                    + '</table>'
                    + '</div>'
                    + '</div>';

                return table;
            };

            let searchRequestXhr = null;
            const searchIndexers = function () {
                if (searchRequestXhr) {
                    searchRequestXhr.abort();
                }

                if (!$('#show-name').val()) {
                    return;
                }

                const searchingFor = _($('#show-name').val().trim() + ' on ' + $('#providedIndexer option:selected').text() + ' in ' + $('#indexerLangSelect option:selected').text());
                $('#searchResults').empty().html(
                    '<img id="searchingAnim" src="' + scRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" /> '
                    + _('searching {searchingFor}...').replace(/{searchingFor}/, searchingFor),
                );

                searchRequestXhr = $.ajax({
                    url: scRoot + '/addShows/searchIndexersForShowName',
                    data: {
                        search_term: $('#show-name').val().trim(), // eslint-disable-line camelcase
                        exact: $('#exact-match').is(':checked') ? 1 : 0,
                        lang: $('#indexerLangSelect').val(),
                        indexer: $('#providedIndexer').val(),
                    },
                    timeout: Number.parseInt($('#indexer_timeout').val(), 10) * 1000,
                    dataType: 'json',
                    error() {
                        $('#searchResults').empty().html(_('search timed out, try again or try another indexer'));
                        $('.next-steps').hide();
                    },
                    success(data) {
                        let resultString = '<legend class="legendStep">#2 Pick a Show</legend>';
                        if (data.results.length === 0) {
                            resultString += '<b>No results found, try a different search.</b>';
                            $('.next-steps').hide();
                        } else {
                            const shows = [];

                            $.each(data.results, (index, object) => {
                                const whichSeries = object.join('|').replace(/"/g, '');

                                const show = {
                                    obj: whichSeries,
                                    indexer: object[0],
                                    id: object[3],
                                    title: object[4],
                                    debut: object[5],
                                    inShowList: object[6],
                                    url: anonURL + object[2] + object[3],
                                };

                                if (data.langid) {
                                    show.url += '&lid=' + data.langid;
                                }

                                shows.push(show);
                            });

                            resultString += buildTable(shows);

                            $('.next-steps').show();
                        }

                        $('#searchResults').html(resultString);
                        updateSampleText();
                        $('.new-show-table').tablesorter(
                            {
                                widgets: ['stickyHeaders', 'zebra', 'saveSort'],
                                headers: {0: {sorter: false}},
                            });
                    },
                });
            };

            $('#search-button').on('click', searchIndexers);

            $('#addShowButton').on('click', () => {
                // If they haven't picked a show don't let them submit
                if (!$('input:radio[name="whichSeries"]:checked').val()) {
                    notifyModal('You must choose a show to continue');
                    return false;
                }

                generateBlackWhiteList(); // eslint-disable-line no-undef
                $('#addShowForm').submit();
            });

            $('#anime').on('click', () => {
                showGroupPicker();
                updateSampleText();
            });

            $('#skipShowButton').on('click', () => {
                $('#skipShow').val('1');
                $('#addShowForm').submit();
            });

            $('#rootDirText').change(updateSampleText);
            $('#qualityPreset').change(updateSampleText);
            $('#searchResults').on('change', '.whichSeries', updateSampleText);

            $('#show-name').on('focus keyup', event => {
                if (event.keyCode === 13) { // Enter
                    $('#search-button').click();
                }
            });

            if ($('#show-name').val()) {
                $('#search-button').click();
            }

            updateSampleText();
            showGroupPicker();
        },
        addExistingShow() {
            $('#tableDiv').on('click', '#checkAll', function () {
                const seasCheck = this.checked;
                $('.dirCheck').each(function () {
                    this.checked = seasCheck;
                });
            });

            $('#submitShowDirs').on('click', () => {
                const submitForm = $('#addShowForm');
                let selectedShows = false;
                $('.dirCheck').each(function () {
                    if (this.checked === true) {
                        const show = $(this).attr('id');
                        const indexer = $(this).closest('tr').find('select').val();
                        $('<input>', {
                            type: 'hidden',
                            name: 'shows_to_add',
                            value: indexer + '|' + show,
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
                    value: $('#promptForSettings').is(':checked') ? 'on' : 'off',
                }).appendTo(submitForm);

                submitForm.submit();
            });

            function loadContent() {
                let url = '';
                $('.dir_check').each((i, w) => {
                    if ($(w).is(':checked')) {
                        if (url.length > 0) {
                            url += '&';
                        }

                        url += 'rootDir=' + encodeURIComponent($(w).attr('id'));
                    }
                });

                $('#tableDiv').html('<img id="searchingAnim" src="' + scRoot + '/images/loading32.gif" height="32" width="32" /> ' + _('loading folders...'));
                $.post(scRoot + '/addShows/massAddTable/', url, data => {
                    $('#tableDiv').html(data);
                    $('#addRootDirTable').tablesorter({
                        // SortList: [[1,0]],
                        widgets: ['zebra'],
                        headers: {
                            0: {sorter: false},
                        },
                    });
                });
            }

            let lastTxt = '';
            // @TODO This fixes the issue of the page not loading at all,
            //       before I added this I couldn't get the directories to show in the table.
            const rootDirsWorkaround = function () {
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

            rootDirsWorkaround();

            $('#rootDirText').on('change', rootDirsWorkaround);

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
                'Trakt timed out, refresh page to try again',
            );
        },
        trendingShows() {
            $('#trendingShows').loadRemoteShows(
                '/addShows/getTrendingShows/?traktList=' + $('#traktList').val(),
                'Loading trending shows...',
                'Trakt timed out, refresh page to try again',
            );

            $('#traktlistselection').on('change', event => {
                const traktList = event.target.value;
                window.history.replaceState({}, document.title, '?traktList=' + traktList);
                $('#trendingShows').loadRemoteShows(
                    '/addShows/getTrendingShows/?traktList=' + traktList,
                    'Loading trending shows...',
                    'Trakt timed out, refresh page to try again',
                );
            });
        },
        popularShows() {
            $.initRemoteShowGrid();
        },
    },
    movies: {
        init() {
            // Reset the layout for the activated tab (when using ui tabs)
            $('#movieTabs').tabs({
                activate() {
                    $('.movie-grid').isotope('layout');
                },
            });
        },
        index() {
            // Resets the tables sorting, needed as we only use a single call for both tables in tablesorter
            $('.resetsorting').on('click', () => {
                $('table').trigger('filterReset');
            });

            // Handle filtering in the poster layout
            $('#filterMovieName').on('input', __.debounce(() => {
                $('.movie-grid').isotope({
                    filter() {
                        const name = $(this).find('.movie-title').html().trim().toLowerCase();
                        return name.includes($('#filterShowName').val().toLowerCase());
                    },
                });
            }, 500));

            function resizePosters(newSize) {
                let fontSize = 0;
                let logoWidth = 0;
                let borderRadius = 0;
                let borderWidth = 0;

                if (newSize < 125) { // Small
                    borderRadius = 3;
                    borderWidth = 4;
                } else if (newSize < 175) { // Medium
                    fontSize = 9;
                    logoWidth = 40;
                    borderRadius = 4;
                    borderWidth = 5;
                } else { // Large
                    fontSize = 11;
                    logoWidth = 50;
                    borderRadius = 6;
                    borderWidth = 6;
                }

                // If there's a poster popup, remove it before resizing
                $('#posterPopup').remove();

                if (fontSize === undefined) {
                    $('.movie-details').hide();
                } else {
                    $('.movie-details').show();
                    $('.movie-dlstats, .movie-quality').css('fontSize', fontSize);
                    $('.movie-network-image').css('width', logoWidth);
                }

                $('.movie-container').css({
                    width: newSize,
                    borderWidth,
                    borderRadius,
                });
            }

            let posterSize;
            if (typeof (Storage) !== 'undefined') {
                posterSize = Number.parseInt(localStorage.getItem('posterSize'), 10);
            }

            if (typeof (posterSize) !== 'number' || Number.isNaN(posterSize)) {
                posterSize = 188;
            }

            resizePosters(posterSize);

            $('#posterSizeSlider').slider({
                min: 75,
                max: 250,
                value: posterSize,
                change(event, ui) {
                    if (typeof (Storage) !== 'undefined') {
                        localStorage.setItem('posterSize', ui.value);
                    }

                    resizePosters(ui.value);
                    $('.movie-grid').isotope('layout');
                },
            });

            $('#rootDirSelect').on('change', () => {
                $('#rootDirForm').submit();
            });

            // This needs to be refined to work a little faster.
            $('.progressbar').each(function () {
                const percentage = $(this).data('progress-percentage');
                const classToAdd = Math.max(20, percentage - (percentage % 20));
                $(this).progressbar({value: percentage});
                if ($(this).data('progress-text')) {
                    $(this).append('<div class="progressbarText" title="' + $(this).data('progress-tip') + '">' + $(this).data('progress-text') + '</div>');
                }

                $(this).find('.ui-progressbar-value').addClass('progress-' + classToAdd);
            });

            $('img#network').on('error', function () {
                $(this).parent().text($(this).attr('alt'));
                $(this).remove();
            });
        },
        details() {
            $('.addQTip').each(function () {
                $(this).css({cursor: 'help', 'text-shadow': '0px 0px 0.5px #666'});
                $(this).qtip({
                    show: {solo: true},
                    position: {viewport: $(window), my: 'left center', adjust: {y: -10, x: 2}},
                    style: {tip: {corner: true, method: 'polygon'}, classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'},
                });
            });

            $.fn.generateStars = function () {
                return this.each((i, element) => {
                    $(element).html($('<span/>').width($(element).text() * 12));
                });
            };

            $('.imdbstars').generateStars();

            $('#popover').popover({
                placement: 'bottom',
                html: true, // Required if content has HTML
                content: '<div id="popover-target"></div>',
            })
                // Bootstrap popover event triggered when the popover opens
                .on('shown.bs.popover', () => {
                    $('.displayShowTable').each((index, item) => {
                        $.tablesorter.columnSelector.attachTo(item, '#popover-target');
                    });
                });
        },
    },
};

const UTIL = {
    exec(controller, action) {
        const ns = SICKCHILL;
        action = (action === undefined) ? 'init' : action;

        if (controller !== '' && ns[controller] && typeof ns[controller][action] === 'function') {
            ns[controller][action]();
        }
    },
    init() {
        const body = document.body;
        const controller = body.getAttribute('data-controller');
        const action = body.getAttribute('data-action');

        UTIL.exec('common');
        UTIL.exec(controller);
        UTIL.exec(controller, action);
    },
};

// Handle js-gettext + load javascript functions
$.getJSON(scRoot + '/ui/locale.json', {lang: getMeta('settings.GUI_LANG')}, data => {
    window.gt = data === undefined ? new Gettext() : new Gettext(data.messages);

    // Shortcut for normal gettext
    window._ = function (string) {
        return gt.gettext(string);
    };

    // Shortcut for plural gettext
    window._n = function (string, pluralString, number) {
        return gt.ngettext(string, pluralString, number);
    };

    if (!navigator.userAgent.includes('PhantomJS')) {
        $(document).ready(UTIL.init);
    }
});
