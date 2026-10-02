window.SICKCHILL ||= {};
window.SICKCHILL.config = {
    init() {
        initConfigComponentTabs();

        // Trakt account auth (Config → General → Indexer / Data)
        $('#TraktGetPin').on('click', () => {
            window.open($('#trakt_pin_url').val(), 'popUp', 'toolbar=no, scrollbars=no, resizable=no, top=200, left=200, width=650, height=550');
            $('#trakt_pin').removeClass('hide');
        });

        let traktDevicePollTimer = null;
        const stopTraktDevicePolling = () => {
            if (!traktDevicePollTimer) {
                return;
            }

            clearTimeout(traktDevicePollTimer);
            traktDevicePollTimer = null;
        };

        const pollTraktDevice = (deviceCode, intervalSeconds, expiresAt) => {
            if (Date.now() > expiresAt) {
                $('#TraktDeviceStatus').text(_('Authorization code expired. Please try again.'));
                $('#TraktDeviceStart').removeClass('hide').prop('disabled', false);
                return;
            }

            $.post(scRoot + '/home/pollTraktDeviceAuth', {device_code: deviceCode}) // eslint-disable-line camelcase
                .done(response => {
                    let data = response;
                    if (typeof data === 'string') {
                        try {
                            data = JSON.parse(data);
                        } catch {
                            data = {};
                        }
                    }

                    if (data.status === 'authorized') {
                        $('#TraktDeviceStatus').text(_('Trakt authorized successfully.'));
                        $('#TraktDevicePanel').addClass('hide');
                        if ($('#testTrakt-result').length > 0) {
                            $('#testTrakt-result').html(_('Trakt Authorized'));
                        } else {
                            notifyModal(_('Trakt Authorized'));
                        }

                        return;
                    }

                    if (data.status === 'pending') {
                        traktDevicePollTimer = setTimeout(
                            () => pollTraktDevice(deviceCode, intervalSeconds, expiresAt),
                            intervalSeconds * 1000,
                        );

                        return;
                    }

                    if (data.status === 'slow_down') {
                        const slowedInterval = Math.max(intervalSeconds * 2, intervalSeconds + 5);
                        $('#TraktDeviceStatus').text(_('Trakt asked us to slow down; retrying...'));
                        traktDevicePollTimer = setTimeout(
                            () => pollTraktDevice(deviceCode, slowedInterval, expiresAt),
                            slowedInterval * 1000,
                        );

                        return;
                    }

                    if (data.status === 'expired') {
                        $('#TraktDeviceStatus').text(_('Code expired. Please try again.'));
                        $('#TraktDeviceStart').removeClass('hide').prop('disabled', false);

                        return;
                    }

                    $('#TraktDeviceStatus').text((data && data.message) || _('Trakt authorization failed.'));
                    $('#TraktDeviceStart').removeClass('hide').prop('disabled', false);
                })
                .fail(() => {
                    traktDevicePollTimer = setTimeout(
                        () => pollTraktDevice(deviceCode, intervalSeconds, expiresAt),
                        intervalSeconds * 1000,
                    );
                });
        };

        $('#TraktDeviceStart').on('click', () => {
            stopTraktDevicePolling();
            $('#TraktDeviceStatus').text(_('Contacting Trakt...'));
            $('#TraktDeviceStart').prop('disabled', true);
            $.post(scRoot + '/home/startTraktDeviceAuth')
                .done(response => {
                    let data = response;
                    if (typeof data === 'string') {
                        try {
                            data = JSON.parse(data);
                        } catch {
                            data = {};
                        }
                    }

                    if (!data || data.error || !data.user_code) {
                        $('#TraktDeviceStatus').text((data && data.error) || _('Failed to start Trakt authorization.'));
                        $('#TraktDeviceStart').prop('disabled', false);

                        return;
                    }

                    $('#TraktDeviceUserCode').text(data.user_code);
                    $('#TraktDeviceVerifyLink').attr('href', data.verification_url).text(data.verification_url);
                    $('#TraktDevicePanel').removeClass('hide');
                    $('#TraktDeviceStatus').text(_('Waiting for approval...'));
                    try {
                        window.open(data.verification_url, '_blank', 'noopener');
                    } catch {
                        // Popup blocked - user can click the link.
                    }

                    const interval = Math.max(1, Number(data.interval) || 5);
                    const expiresAt = Date.now() + (Math.max(60, Number(data.expires_in) || 600) * 1000);
                    pollTraktDevice(data.device_code, interval, expiresAt);
                })
                .fail(() => {
                    $('#TraktDeviceStatus').text(_('Failed to start Trakt authorization.'));
                    $('#TraktDeviceStart').prop('disabled', false);
                });
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
                    if ($('#testTrakt-result').length > 0) {
                        $('#testTrakt-result').html(data);
                    } else {
                        notifyModal(data);
                    }

                    $('#authTrakt').addClass('hide');
                    $('#trakt_pin').addClass('hide');
                    $('#TraktGetPin').addClass('hide');
                    $('#TraktDeviceStart').addClass('hide');
                });
            }
        });

        $('.viewIf').on('click', function () {
            if (this.checked) {
                $('.hide_if_' + $(this).attr('id')).css('display', 'none');
                $('.show_if_' + $(this).attr('id')).fadeIn('fast', 'linear');
            } else {
                $('.show_if_' + $(this).attr('id')).css('display', 'none');
                $('.hide_if_' + $(this).attr('id')).fadeIn('fast', 'linear');
            }
        });

        $('.datePresets').on('click', function () {
            let defaultPreset = $('#date_presets').val();
            if (this.checked && defaultPreset === '%x') {
                defaultPreset = '%a, %b %d, %Y';
                $('#date_use_system_default').html('1');
            } else if (!this.checked && $('#date_use_system_default').html() === '1') {
                defaultPreset = '%x';
            }

            $('#date_presets').attr('name', 'date_preset_old');
            $('#date_presets').attr('id', 'date_presets_old');

            $('#date_presets_na').attr('name', 'date_preset');
            $('#date_presets_na').attr('id', 'date_presets');

            $('#date_presets_old').attr('name', 'date_preset_na');
            $('#date_presets_old').attr('id', 'date_presets_na');

            if (defaultPreset) {
                $('#date_presets').val(defaultPreset);
            }
        });

        // Bind 'configForm' and provide a simple callback function
        let configSaveShouldReload = false;
        $(document).on('click', '#configForm .config_submitter_refresh', () => {
            configSaveShouldReload = true;
        });
        $(document).on('click', '#configForm .config_submitter', () => {
            configSaveShouldReload = false;
        });
        $('#configForm').ajaxForm({
            beforeSubmit() {
                $('.config_submitter, .config_submitter_refresh').each(function () {
                    $(this).attr('disabled', 'disabled');
                    $(this).after('<span>' + loading + ' Saving...</span>');
                    $(this).hide();
                });
            },
            success() {
                setTimeout(() => {
                    configSuccess(configSaveShouldReload);
                }, 2000);
            },
        });

        $('#config_save_button').on('click', () => {
            $('#configForm').submit();
        });

        $('#api_key').on('click', () => {
            $('#api_key').select();
        });

        $('#generate_new_apikey').on('click', () => {
            $.get(scRoot + '/config/general/generateApiKey', data => {
                if (data.error === undefined) {
                    $('#api_key').val(data);
                } else {
                    notifyModal(data.error);
                }
            });
        });
    },
    index() {
        $('#log_dir').fileBrowser({title: _('Select log file folder location')});
        $('#sickchill_background_path').fileBrowser({
            title: _('Select Background Image'), key: 'sickchill_background_path', includeFiles: 1, fileTypes: ['images'],
        });
        $('#custom_css_path').fileBrowser({
            title: _('Select CSS file'), key: 'custom_css_path', includeFiles: 1, fileTypes: ['css'],
        });
    },
    backupRestore() {
        $('#backup-submit').on('click', () => {
            $('#backup-submit').attr('disabled', true);
            $('#backup-result').html(loading);
            $.post(scRoot + '/config/backuprestore/backup', {backupDirectory: $('#backupDirectory').val()}).done(data => {
                $('#backup-result').html(data);
                $('#backup-submit').attr('disabled', false);
            });
        });
        $('#restore-submit').on('click', () => {
            $('#restore-submit').attr('disabled', true);
            $('#restore-result').html(loading);
            $.post(scRoot + '/config/backuprestore/restore', {backupFile: $('#backupFile').val()}).done(data => {
                $('#restore-result').html(data);
                $('#restore-submit').attr('disabled', false);
            });
        });

        $('#backupDirectory').fileBrowser({title: _('Select backup folder to save to'), key: 'backupPath'});
        $('#backupFile').fileBrowser({
            title: _('Select backup files to restore'), key: 'backupFile', includeFiles: 1, fileTypes: ['zip'],
        });
        initConfigComponentTabs();
    },
    notifications() {
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

        $('#testJELLYFIN').on('click', function () {
            const jellyfin = {};
            jellyfin.host = $('#jellyfin_host').val();
            jellyfin.apikey = $('#jellyfin_apikey').val();
            if (!jellyfin.host || !jellyfin.apikey) {
                $('#testJELLYFIN-result').html(_('Please fill out the necessary fields above.'));
                if (jellyfin.host) {
                    $('#jellyfin_host').removeClass('warning');
                } else {
                    $('#jellyfin_host').addClass('warning');
                }

                if (jellyfin.apikey) {
                    $('#jellyfin_apikey').removeClass('warning');
                } else {
                    $('#jellyfin_apikey').addClass('warning');
                }

                return;
            }

            $('#jellyfin_host,#jellyfin_apikey').removeClass('warning');
            $(this).prop('disabled', true);
            $('#testJELLYFIN-result').html(loading);
            $.get(scRoot + '/home/testJELLYFIN', {
                host: jellyfin.host,
                jellyfin_apikey: jellyfin.apikey, // eslint-disable-line camelcase
            }).done(data => {
                $('#testJELLYFIN-result').html(data);
                $('#testJELLYFIN').prop('disabled', false);
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

        $('#testSlack').on('click', () => {
            $.post(scRoot + '/home/testSlack', data => {
                $('#testSlack-result').html(data);
            });
        });

        $('#testMattermost').on('click', () => {
            $.post(scRoot + '/home/testMattermost', data => {
                $('#testMattermost-result').html(data);
            });
        });

        $('#testMattermostBot').on('click', () => {
            $.post(scRoot + '/home/testMattermostBot', data => {
                $('#testMattermostBot-result').html(data);
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
            const discordWebhook = $('#discord_webhook');
            if (!discordWebhook.val()) {
                discordWebhook.focus();
                notifyModal('Please fill in the webhook address');
                return;
            }

            const discord = {
                webhook: discordWebhook.val(),
                name: $('#discord_name').val(),
                avatar: $('#discord_avatar_url').val(),
                tts: $('#discord_tts').is(':checked') ? 1 : 0,
            };
            $('#testDiscord').prop('disabled', true);
            $('#testDiscord-result').html(loading);
            $.post(scRoot + '/home/testDiscord', discord).done(data => {
                $('#testDiscord-result').html(data);
                $('#testDiscord').prop('disabled', false);
            });
        });

        $('#settingsNMJ').on('click', () => {
            if (!$('#nmj_host').val()) {
                $('#nmj_host').focus();
                notifyModal('Please fill in the Popcorn IP address');
                return;
            }

            const nmj = {};
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
            if (!$('#nmjv2_host').val()) {
                $('#nmjv2_host').focus();
                notifyModal('Please fill in the Popcorn IP address', 'modal');
                return;
            }

            const nmjv2 = {};

            $('#testNMJv2-result').html(loading);
            nmjv2.host = $('#nmjv2_host').val();
            nmjv2.dbloc = '';
            const radios = document.querySelectorAll('nmjv2_dbloc');
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

        // Trakt PIN authorize handlers live in config.init (Indexer / Data on General)

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

            if (/\s/.test(trakt.trendingBlacklist)) {
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
            } else if (port.match(/^\d+$/) === null || Number.parseInt(port, 10) > 65535) { // eslint-disable-line unicorn/numeric-separators-style
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

        $('#testGotify').on('click', function () {
            const gotify = {};
            gotify.host = $.trim($('#gotify_host').val());
            gotify.authToken = $.trim($('#gotify_authorizationtoken').val());
            if (!gotify.host || !gotify.authToken) {
                $('#testGotify-result').html(_('Please fill out the necessary fields above.'));
                if (gotify.host) {
                    $('#gotify_host').removeClass('warning');
                } else {
                    $('#gotify_host').addClass('warning');
                }

                if (gotify.authToken) {
                    $('#gotify_authorizationtoken').removeClass('warning');
                } else {
                    $('#gotify_authorizationtoken').addClass('warning');
                }

                return;
            }

            $('#gotify_host,#gotify_authorizationtoken').removeClass('warning');
            $(this).prop('disabled', true);
            $('#testGotify-result').html(loading);
            $.post(scRoot + '/home/testGotify', {
                host: gotify.host,
                authorizationToken: gotify.authToken,
            }).done(data => {
                $('#testGotify-result').html(data);
                $('#testGotify').prop('disabled', false);
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
                for (let device = 0; device < pushbullet.devices.length; device++) {
                    if (pushbullet.devices[device].active === true) {
                        if (pushbullet.currentDevice === pushbullet.devices[device].iden) {
                            $('#pushbullet_device_list').append('<option value="' + pushbullet.devices[device].iden + '" selected>' + pushbullet.devices[device].nickname + '</option>');
                        } else {
                            $('#pushbullet_device_list').append('<option value="' + pushbullet.devices[device].iden + '">' + pushbullet.devices[device].nickname + '</option>');
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
                    $('#pushbullet_channel_list').prepend('<option value="">No Channels</option>');
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
                // future: Why is this not just sent as json to begin with?
                const notifyList = [];
                for (const listKey in list) {
                    if (Object.hasOwn(list, listKey) && listKey.charAt(0) !== '_') {
                        notifyList.push(list[listKey]);
                    }
                }

                const sortedList = notifyList.sort((a, b) => a.name.localeCompare(b.name));
                let html = '<option value="-1">-- Select --</option>';
                for (const sortedListKey in sortedList) {
                    if (Object.hasOwn(sortedList, sortedListKey) && sortedList[sortedListKey].id && sortedList[sortedListKey].name) {
                        html += '<option value="' + sortedList[sortedListKey].id + '">' + $('<div>').text(sortedList[sortedListKey].name).html() + '</option>';
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
            if (this.checked) {
                $('.plexinfo').removeClass('hide');
            } else {
                $('.plexinfo').addClass('hide');
            }
        });
    },
    postProcessing() {
        initConfigComponentTabs();
        $('#tv_download_dir').fileBrowser({title: _('Select TV Download Directory')});
        $('#unpack_dir').fileBrowser({title: _('Select Unpack Directory')});

        function isRarSupported() {
            $.post(scRoot + '/config/postProcessing/isRarSupported', data => {
                if (data === 'supported') {
                    return;
                }

                $('#unpack').qtip('option', {
                    'content.text': 'Unrar Executable not found.',
                    'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                });
                $('#unpack').qtip('toggle', true);
                $('#unpack').css('background-color', '#FFFFDD');
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
                abd: true,
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
                abd: true,
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
                sports: true,
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
                sports: true,
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
                const namingAnimePatternInput = $('#naming_anime_pattern');
                if (data === 'invalid') {
                    info = _('This pattern is invalid.');
                    namingAnimePatternInput.qtip('option', {
                        'content.text': info,
                        'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                    });
                    namingAnimePatternInput.qtip('toggle', true);
                    namingAnimePatternInput.css('background-color', '#FFDDDD');
                } else if (data === 'seasonfolders') {
                    info = _('This pattern would be invalid without the folders, using it will force "Season Folders" on for all shows.');
                    namingAnimePatternInput.qtip('option', {
                        'content.text': info,
                        'style.classes': 'qtip-rounded qtip-shadow qtip-red',
                    });
                    namingAnimePatternInput.qtip('toggle', true);
                    namingAnimePatternInput.css('background-color', '#FFFFDD');
                } else {
                    info = _('This pattern is valid.');
                    namingAnimePatternInput.qtip('option', {
                        'content.text': info,
                        'style.classes': 'qtip-rounded qtip-shadow qtip-green',
                    });
                    namingAnimePatternInput.qtip('toggle', false);
                    namingAnimePatternInput.css('background-color', '#FFFFFF');
                }

                namingAnimePatternInput.attr('title', info);
            });
        }

        function setupNamingPattern(presetSelector, customSelector, patternSelector, fill) {
            if ($(presetSelector + ' :selected').val().toLowerCase() === 'custom...') {
                $(customSelector).show();
            } else {
                $(customSelector).hide();
                $(patternSelector).val($(presetSelector + ' :selected').attr('id'));
            }

            fill();
        }

        function setupNaming() {
            setupNamingPattern('#name_presets', '#naming_custom', '#naming_pattern', fillExamples);
        }

        function setupAbdNaming() {
            setupNamingPattern('#name_abd_presets', '#naming_abd_custom', '#naming_abd_pattern', fillAbdExamples);
        }

        function setupSportsNaming() {
            setupNamingPattern('#name_sports_presets', '#naming_sports_custom', '#naming_sports_pattern', fillSportsExamples);
        }

        function setupAnimeNaming() {
            setupNamingPattern('#name_anime_presets', '#naming_anime_custom', '#naming_anime_pattern', fillAnimeExamples);
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
            if (value !== 1) {
                return;
            }

            $('#content_unpack').fadeIn('fast', 'linear');
            isRarSupported();
        });

        $('#name_presets').on('change', setupNaming);
        $('#name_abd_presets').on('change', setupAbdNaming);
        $('#naming_custom_abd').on('change', setupAbdNaming);
        $('#name_sports_presets').on('change', setupSportsNaming);
        $('#naming_custom_sports').on('change', setupSportsNaming);
        $('#name_anime_presets').on('change', setupAnimeNaming);
        $('#naming_custom_anime').on('change', setupAnimeNaming);
        $('input[name="naming_anime"]').on('click', setupAnimeNaming);

        $('#naming_multi_ep').on('change', fillExamples);
        $('#naming_pattern').on('focusout', fillExamples);
        $('#naming_pattern').on('keyup', __.debounce(fillExamples, 500));

        $('#naming_anime_multi_ep').on('change', fillAnimeExamples);
        $('#naming_anime_pattern').on('focusout', fillAnimeExamples);
        $('#naming_anime_pattern').on('keyup', __.debounce(fillAnimeExamples, 500));

        $('#naming_abd_pattern').on('focusout', fillAbdExamples);
        $('#naming_abd_pattern').on('keyup', __.debounce(fillAbdExamples, 500));

        $('#naming_sports_pattern').on('focusout', fillSportsExamples);
        $('#naming_sports_pattern').on('keyup', __.debounce(fillSportsExamples, 500));

        // Anime pattern already bound to fillAnimeExamples above — do not also call fillExamples

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
            let currentMost = 0;
            let currentMostProvider = '';

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

                configArray.push(
                    showMetadata ? '1' : '0',
                    episodeMetadata ? '1' : '0',
                    fanart ? '1' : '0',
                    poster ? '1' : '0',
                    banner ? '1' : '0',
                    episodeThumbnails ? '1' : '0',
                    seasonPosters ? '1' : '0',
                    seasonBanners ? '1' : '0',
                    seasonAllPoster ? '1' : '0',
                    seasonAllBanner ? '1' : '0',
                );

                let currentNumber = 0;
                for (const element of configArray) {
                    currentNumber += Number.parseInt(element, 10);
                }

                if (currentNumber > currentMost) {
                    currentMost = currentNumber;
                    currentMostProvider = generatorName;
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

            if (currentMostProvider === '' || !first) {
                return;
            }

            $('#metadataType option[value=' + currentMostProvider + ']').attr('selected', 'selected');
            $(this).showHideMetadata();
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
        initConfigComponentTabs();
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
                    $('#torrent_path_option').show();
                    $('#torrent_path_option').find('.fileBrowser').show();
                    $('#torrent_path_incomplete_option').show();
                    $('#torrent_seed_time_label').text(_('Stop seeding after'));
                    $('#torrent_seed_time_option').show();
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
                    $('label[for="torrent_password"]').html('<a href="' + anonURL + 'https://app.put.io/oauth/apps/new" target="_blank">'
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
            if (!$('#torrent_method :selected').val().toLowerCase().startsWith('rtorrent')) {
                return;
            }

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
        });

        const applyNzbBlackholeSettings = data => {
            if (Object.hasOwn(data, 'nzb_dir')) {
                $('#nzb_dir').val(data.nzb_dir || '');
            }
        };

        const applyNzbDownloadStationSettings = data => {
            $('#syno_dsm_host').val(data.host || '');
            $('#syno_dsm_user').val(data.username || '');
            $('#syno_dsm_pass').val(data.password || '');
            $('#syno_dsm_path').val(data.path || '');
        };

        const applySabnzbdSettings = data => {
            $('#sab_host').val(data.host || '');
            $('#sab_username').val(data.username || '');
            $('#sab_password').val(data.password || '');
            $('#sab_apikey').val(data.apikey || '');
            $('#sab_category').val(data.category || 'tv');
            $('#sab_category_backlog').val(data.category_backlog || '');
            $('#sab_category_anime').val(data.category_anime || 'anime');
            $('#sab_category_anime_backlog').val(data.category_anime_backlog || '');
            $('#sab_forced').prop('checked', Boolean(data.forced));
        };

        const applyNzbgetSettings = data => {
            const priority = data.priority ?? 100;
            $('#nzbget_host').val(data.host || '');
            $('#nzbget_username').val(data.username || 'nzbget');
            $('#nzbget_password').val(data.password || '');
            $('#nzbget_category').val(data.category || 'tv');
            $('#nzbget_category_backlog').val(data.category_backlog || '');
            $('#nzbget_category_anime').val(data.category_anime || 'anime');
            $('#nzbget_category_anime_backlog').val(data.category_anime_backlog || '');
            $('#nzbget_use_https').prop('checked', Boolean(data.use_https));
            $('#nzbget_priority').val(priority);
        };

        const nzbClientSettingsAppliers = {
            blackhole: applyNzbBlackholeSettings,
            download_station: applyNzbDownloadStationSettings, // eslint-disable-line camelcase
            sabnzbd: applySabnzbdSettings,
            nzbget: applyNzbgetSettings,
        };

        $.applyNzbClientSettings = (method, data) => {
            const apply = nzbClientSettingsAppliers[method];
            if (apply) {
                apply(data);
            }
        };

        let nzbClientSettingsRequestId = 0;
        let nzbClientSettingsXhr = null;

        $.loadNzbClientSettings = method => {
            method = (method || $('#nzb_method :selected').val() || '').toLowerCase();
            if (!method) {
                return;
            }

            if (nzbClientSettingsXhr) {
                nzbClientSettingsXhr.abort();
            }

            const requestId = ++nzbClientSettingsRequestId;
            nzbClientSettingsXhr = $.getJSON(scRoot + '/config/search/getNzbClientSettings', {
                nzb_method: method, // eslint-disable-line camelcase
            }).done(data => {
                if (requestId !== nzbClientSettingsRequestId) {
                    return;
                }

                const selected = ($('#nzb_method :selected').val() || '').toLowerCase();
                if (!data || method !== selected) {
                    return;
                }

                $.applyNzbClientSettings(method, data);
            });
        };

        $('#nzb_method').on('change', () => {
            const method = $('#nzb_method :selected').val();
            $.loadNzbClientSettings(method);
            $(document).nzbMethodHandler();
        });

        $(document).nzbMethodHandler();

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

        $.applyTorrentClientSettings = (method, data) => {
            if (method === 'blackhole') {
                if (Object.hasOwn(data, 'torrent_dir')) {
                    $('#torrent_dir').val(data.torrent_dir || '');
                }

                return;
            }

            const seedTime = data.seed_time ?? 0;
            $('#torrent_host').val(data.host || '');
            $('#torrent_username').val(data.username || '');
            $('#torrent_password').val(data.password || '');
            $('#torrent_path').val(data.path || '');
            $('#torrent_path_incomplete').val(data.path_incomplete || '');
            $('#torrent_label').val(data.label || '');
            $('#torrent_label_anime').val(data.label_anime || '');
            $('#torrent_seed_time').val(seedTime);
            $('#torrent_rpcurl').val(data.rpcurl || 'transmission');
            $('#torrent_auth_type').val(data.auth_type || 'none');
            $('#torrent_paused').prop('checked', Boolean(data.paused));
            $('#torrent_verify_cert').prop('checked', Boolean(data.verify_cert));
            $('#torrent_high_bandwidth').prop('checked', Boolean(data.high_bandwidth));
        };

        let torrentClientSettingsRequestId = 0;
        let torrentClientSettingsXhr = null;

        $.loadTorrentClientSettings = method => {
            method = (method || $('#torrent_method :selected').val() || '').toLowerCase();
            if (!method) {
                return;
            }

            if (torrentClientSettingsXhr) {
                torrentClientSettingsXhr.abort();
            }

            const requestId = ++torrentClientSettingsRequestId;
            torrentClientSettingsXhr = $.getJSON(scRoot + '/config/search/getTorrentClientSettings', {
                torrent_method: method, // eslint-disable-line camelcase
            }).done(data => {
                if (requestId !== torrentClientSettingsRequestId) {
                    return;
                }

                const selected = ($('#torrent_method :selected').val() || '').toLowerCase();
                if (!data || method !== selected) {
                    return;
                }

                $.applyTorrentClientSettings(method, data);
            });
        };

        $('#torrent_method').on('change', () => {
            const method = $('#torrent_method :selected').val();
            $.loadTorrentClientSettings(method);
            $.torrentMethodHandler();
        });

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
        $('#testFlareSolverr').on('click', function () {
            const flaresolverrUri = $.trim($('#flaresolverr_uri').val());
            if (!flaresolverrUri) {
                $('#testFlaresolverr-result').html(_('Please fill out the necessary fields above.'));
                $('#flaresolverr_uri').addClass('warning');
                return;
            }

            $('#flaresolverr_uri').removeClass('warning');
            $(this).prop('disabled', true);
            $('#testFlaresolverr-result').html(loading);
            $.post(scRoot + '/home/testFlareSolverr', {
                flaresolverr_uri: flaresolverrUri, // eslint-disable-line camelcase
            }).done(data => {
                $('#testFlaresolverr-result').html(data);
                $('#testFlareSolverr').prop('disabled', false);
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

            if ($('#service_order_list > #' + id).length > 0 || showService === false) {
                return;
            }

            let toAdd = '';
            toAdd += '<li class="ui-state-default" id="' + id + '"> ';
            toAdd += '<input type="checkbox" id="enable_' + id + '" class="service_enabler" checked> ';
            toAdd += '<a href="' + anonURL + url + '" class="imgLink" target="_new">';
            toAdd += '<img src="' + scRoot + '/images/services/newznab.gif" alt="' + name + '" width="16" height="16"></a> ';
            toAdd += name + '</li>';

            $('#service_order_list').append(toAdd);
            $('#service_order_list').sortable('refresh');
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
};
