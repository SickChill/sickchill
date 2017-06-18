// $('#testPMS').on('click', function() {
//     const plex = {};
//     plex.server = {};
//     plex.server.host = $.trim($('#plex_server_host').val());
//     plex.server.username = $.trim($('#plex_server_username').val());
//     plex.server.password = $.trim($('#plex_server_password').val());
//     plex.server.token = $.trim($('#plex_server_token').val());
//     if (!plex.server.host) {
//         $('#testPMS-result').html(_('Please fill out the necessary fields above.'));
//         $('#plex_server_host').addClass('warning');
//         return;
//     }
//     $('#plex_server_host').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testPMS-result').html(loading);
//     $.get(config.srRoot + '/home/testPMS', {
//         host: plex.server.host,
//         username: plex.server.username,
//         password: plex.server.password,
//         plex_server_token: plex.server.token // eslint-disable-line camelcase
//     }).done(data => {
//         $('#testPMS-result').html(data);
//         $('#testPMS').prop('disabled', false);
//     });
// });


// // Show instructions for plex when enabled
// $('#use_plex_server').on('click', function() {
//     if ($(this).is(':checked')) {
//         $('.plexinfo').removeClass('hide');
//     } else {
//         $('.plexinfo').addClass('hide');
//     }
// });
