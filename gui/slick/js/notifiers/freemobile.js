// $('#testFreeMobile').on('click', function() {
//     const freemobile = {};
//     freemobile.id = $.trim($('#freemobile_id').val());
//     freemobile.apikey = $.trim($('#freemobile_apikey').val());
//     if (!freemobile.id || !freemobile.apikey) {
//         $('#testFreeMobile-result').html(_('Please fill out the necessary fields above.'));
//         if (!freemobile.id) {
//             $('#freemobile_id').addClass('warning');
//         } else {
//             $('#freemobile_id').removeClass('warning');
//         }
//         if (!freemobile.apikey) {
//             $('#freemobile_apikey').addClass('warning');
//         } else {
//             $('#freemobile_apikey').removeClass('warning');
//         }
//         return;
//     }
//     $('#freemobile_id,#freemobile_apikey').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testFreeMobile-result').html(loading);
//     $.post(config.srRoot + '/home/testFreeMobile', {
//         freemobile_id: freemobile.id, // eslint-disable-line camelcase
//         freemobile_apikey: freemobile.apikey // eslint-disable-line camelcase
//     }).done(data => {
//         $('#testFreeMobile-result').html(data);
//         $('#testFreeMobile').prop('disabled', false);
//     });
// });
//
