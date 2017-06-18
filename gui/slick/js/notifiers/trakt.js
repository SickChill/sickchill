// $('#TraktGetPin').on('click', () => {
//     window.open($('#trakt_pin_url').val(), 'popUp', 'toolbar=no, scrollbars=no, resizable=no, top=200, left=200, width=650, height=550');
//     $('#trakt_pin').removeClass('hide');
// });
//
// $('#trakt_pin').on('keyup change', () => {
//     if ($('#trakt_pin').val().length !== 0) {
//         $('#TraktGetPin').addClass('hide');
//         $('#authTrakt').removeClass('hide');
//     } else {
//         $('#TraktGetPin').removeClass('hide');
//         $('#authTrakt').addClass('hide');
//     }
// });
//
// $('#authTrakt').on('click', () => {
//     const trakt = {};
//     trakt.pin = $('#trakt_pin').val();
//     if (trakt.pin.length !== 0) {
//         $.post(config.srRoot + '/home/getTraktToken', {
//             trakt_pin: trakt.pin // eslint-disable-line camelcase
//         }).done(data => {
//             $('#testTrakt-result').html(data);
//             $('#authTrakt').addClass('hide');
//             $('#trakt_pin').addClass('hide');
//             $('#TraktGetPin').addClass('hide');
//         });
//     }
// });
//
// $('#testTrakt').on('click', function() {
//     const trakt = {};
//     trakt.username = $.trim($('#trakt_username').val());
//     trakt.trendingBlacklist = $.trim($('#trakt_blacklist_name').val());
//     if (!trakt.username) {
//         $('#testTrakt-result').html(_('Please fill out the necessary fields above.'));
//         if (!trakt.username) {
//             $('#trakt_username').addClass('warning');
//         } else {
//             $('#trakt_username').removeClass('warning');
//         }
//         return;
//     }
//
//     if (/\s/g.test(trakt.trendingBlacklist)) {
//         $('#testTrakt-result').html(_('Check blacklist name; the value needs to be a trakt slug'));
//         $('#trakt_blacklist_name').addClass('warning');
//         return;
//     }
//     $('#trakt_username').removeClass('warning');
//     $('#trakt_blacklist_name').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testTrakt-result').html(loading);
//     $.post(config.srRoot + '/home/testTrakt', {
//         username: trakt.username,
//         blacklist_name: trakt.trendingBlacklist // eslint-disable-line camelcase
//     }).done(data => {
//         $('#testTrakt-result').html(data);
//         $('#testTrakt').prop('disabled', false);
//     });
// });
//
