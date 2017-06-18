// $('#testPHT').on('click', function() {
//     const plex = {};
//     plex.client = {};
//     plex.client.host = $.trim($('#plex_client_host').val());
//     plex.client.username = $.trim($('#plex_client_username').val());
//     plex.client.password = $.trim($('#plex_client_password').val());
//     if (!plex.client.host) {
//         $('#testPHT-result').html(_('Please fill out the necessary fields above.'));
//         $('#plex_client_host').addClass('warning');
//         return;
//     }
//     $('#plex_client_host').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testPHT-result').html(loading);
//     $.get(config.srRoot + '/home/testPHT', {
//         host: plex.client.host,
//         username: plex.client.username,
//         password: plex.client.password
//     }).done(data => {
//         $('#testPHT-result').html(data);
//         $('#testPHT').prop('disabled', false);
//     });
// });
