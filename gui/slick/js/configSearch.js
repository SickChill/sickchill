$(document).ready(function(){
    var loading = '<img src="' + srRoot + '/images/loading16' + themeSpinner + '.gif" height="16" width="16" />';

    function toggle_torrent_title(){
        if ($('#use_torrents').prop('checked')){
            $('#no_torrents').show();
        } else {
            $('#no_torrents').hide();
        }
    }

    $.fn.nzb_method_handler = function() {
        var selectedProvider = $('#nzb_method :selected').val(),
            blackhole_settings = '#blackhole_settings',
            sabnzbd_settings = '#sabnzbd_settings',
            testSABnzbd = '#testSABnzbd',
            testSABnzbd_result = '#testSABnzbd_result',
            nzbget_settings = '#nzbget_settings';

        $(blackhole_settings).hide();
        $(sabnzbd_settings).hide();
        $(testSABnzbd).hide();
        $(testSABnzbd_result).hide();
        $(nzbget_settings).hide();

        if ('blackhole' == selectedProvider) {
            $(blackhole_settings).show();
        } else if ('nzbget' == selectedProvider) {
            $(nzbget_settings).show();
        } else {
            $(sabnzbd_settings).show();
            $(testSABnzbd).show();
            $(testSABnzbd_result).show();
        }
    };

    $.fn.rtorrent_scgi = function(){
        var selectedProvider = $('#torrent_method :selected').val();

        if ('rtorrent' == selectedProvider) {
            var hostname = $('#torrent_host').prop('value');
            var isMatch = hostname.substr(0, 7) == "scgi://";

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

    $.fn.torrent_method_handler = function() {

        $('#options_torrent_clients').hide();
        $('#options_torrent_blackhole').hide();

        var selectedProvider = $('#torrent_method :selected').val(),
            host = ' host:port',
            username = ' username',
            password = ' password',
            label = ' label',
            directory = ' directory',
            client = '',
            option_panel = '#options_torrent_blackhole';
            rpcurl = ' RPC URL';

        if ('blackhole' != selectedProvider) {
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
            $(this).rtorrent_scgi();

            if ('utorrent' == selectedProvider) {
                client = 'uTorrent';
                $(torrent_path_option).hide();
                $('#torrent_seed_time_label').text('Minimum seeding time is');
                $(torrent_seed_time_option).show();
                $('#host_desc_torrent').text('URL to your uTorrent client (e.g. http://localhost:8000)');
            } else if ('transmission' == selectedProvider){
                client = 'Transmission';
                $('#torrent_seed_time_label').text('Stop seeding when inactive for');
                $(torrent_seed_time_option).show();
                $(torrent_high_bandwidth_option).show();
                $(torrent_label_option).hide();
                $(torrent_label_anime_option).hide();
                $(torrent_rpcurl_option).show();
                $('#host_desc_torrent').text('URL to your Transmission client (e.g. http://localhost:9091)');
                //$('#directory_title').text(client + directory);
            } else if ('deluge' == selectedProvider){
                client = 'Deluge';
                $(torrent_verify_cert_option).show();
                $(torrent_verify_deluge).show();
                $(torrent_verify_rtorrent).hide();
                $(label_warning_deluge).show();
                $(label_anime_warning_deluge).show();
                $('#torrent_username_option').hide();
                $('#torrent_username').prop('value', '');
                $('#host_desc_torrent').text('URL to your Deluge client (e.g. http://localhost:8112)');
                //$('#directory_title').text(client + directory);
            } else if ('deluged' == selectedProvider){
                client = 'Deluge';
                $(torrent_verify_cert_option).hide();
                $(torrent_verify_deluge).hide();
                $(torrent_verify_rtorrent).hide();
                $(label_warning_deluge).show();
                $(label_anime_warning_deluge).show();
                $('#torrent_username_option').show();
                $('#host_desc_torrent').text('IP or Hostname of your Deluge Daemon (e.g. scgi://localhost:58846)');
                //$('#directory_title').text(client + directory);
            } else if ('download_station' == selectedProvider){
                client = 'Synology DS';
                $(torrent_label_option).hide();
                $(torrent_label_anime_option).hide();
                $('#torrent_paused_option').hide();
                $(torrent_path_option).find('.fileBrowser').hide();
                $('#host_desc_torrent').text('URL to your Synology DS client (e.g. http://localhost:5000)');
                //$('#directory_title').text(client + directory);
                $(path_synology).show();
            } else if ('rtorrent' == selectedProvider){
                client = 'rTorrent';
                $(torrent_paused_option).hide();
                $('#host_desc_torrent').text('URL to your rTorrent client (e.g. scgi://localhost:5000 <br/> or https://localhost/rutorrent/plugins/httprpc/action.php)');
                $(torrent_verify_cert_option).show();
                $(torrent_verify_deluge).hide();
                $(torrent_verify_rtorrent).show();
                $(torrent_auth_type_option).show();
                //$('#directory_title').text(client + directory);
            } else if ('qbittorrent' == selectedProvider){
                client = 'qbittorrent';
                $(torrent_path_option).hide();
                $(torrent_label_option).hide();
                $(torrent_label_anime_option).hide();
                $('#host_desc_torrent').text('URL to your qbittorrent client (e.g. http://localhost:8080)');
            }
            $('#host_title').text(client + host);
            $('#username_title').text(client + username);
            $('#password_title').text(client + password);
            $('#torrent_client').text(client);
            $('#rpcurl_title').text(client + rpcurl);
            option_panel = '#options_torrent_clients';
        }
        $(option_panel).show();
    };

    $('#nzb_method').change($(this).nzb_method_handler);

    $(this).nzb_method_handler();

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


    $('#torrent_method').change($(this).torrent_method_handler);

    $(this).torrent_method_handler();

    $('#use_torrents').click(function(){
        toggle_torrent_title();
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

    $('#torrent_host').change($(this).rtorrent_scgi);
});
