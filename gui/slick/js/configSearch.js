$(document).ready(function(){
    var loading = '<img src="' + srRoot + '/images/loading16' + themeSpinner + '.gif" height="16" width="16" />';

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

        $.get(srRoot + '/home/testSABnzbd', {'host': sab_host, 'username': sab_username, 'password': sab_password, 'apikey': sab_apiKey},
        function(data){
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

        $.get(srRoot + '/home/testTorrent', {'torrent_method': torrent_method, 'host': torrent_host, 'username': torrent_username, 'password': torrent_password},
        function(data){ $('#test_torrent_result').html(data); });
    });

    $('#torrent_host').change($(this).rtorrentScgi);
});
