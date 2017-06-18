// $('#testEMBY').on('click', function() {
//     const emby = {};
//     emby.host = $('#emby_host').val();
//     emby.apikey = $('#emby_apikey').val();
//     if (!emby.host || !emby.apikey) {
//         $('#testEMBY-result').html(_('Please fill out the necessary fields above.'));
//         if (emby.host) {
//             $('#emby_host').removeClass('warning');
//         } else {
//             $('#emby_host').addClass('warning');
//         }
//         if (emby.apikey) {
//             $('#emby_apikey').removeClass('warning');
//         } else {
//             $('#emby_apikey').addClass('warning');
//         }
//         return;
//     }
//     $('#emby_host,#emby_apikey').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testEMBY-result').html(loading);
//     $.get(config.srRoot + '/home/testEMBY', {
//         host: emby.host,
//         emby_apikey: emby.apikey // eslint-disable-line camelcase
//     }).done(data => {
//         $('#testEMBY-result').html(data);
//         $('#testEMBY').prop('disabled', false);
//     });
// });
