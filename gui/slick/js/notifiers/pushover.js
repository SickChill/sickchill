// $('#testPushover').on('click', function() {
//     const pushover = {};
//     pushover.userkey = $('#pushover_userkey').val();
//     pushover.apikey = $('#pushover_apikey').val();
//     if (!pushover.userkey || !pushover.apikey) {
//         $('#testPushover-result').html(_('Please fill out the necessary fields above.'));
//         if (!pushover.userkey) {
//             $('#pushover_userkey').addClass('warning');
//         } else {
//             $('#pushover_userkey').removeClass('warning');
//         }
//         if (!pushover.apikey) {
//             $('#pushover_apikey').addClass('warning');
//         } else {
//             $('#pushover_apikey').removeClass('warning');
//         }
//         return;
//     }
//     $('#pushover_userkey,#pushover_apikey').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testPushover-result').html(loading);
//     $.get(config.srRoot + '/home/testPushover', {
//         userKey: pushover.userkey,
//         apiKey: pushover.apikey
//     }).done(data => {
//         $('#testPushover-result').html(data);
//         $('#testPushover').prop('disabled', false);
//     });
// });
