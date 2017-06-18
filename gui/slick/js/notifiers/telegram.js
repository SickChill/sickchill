// $('#testTelegram').on('click', function() {
//     const telegram = {};
//     telegram.id = $.trim($('#telegram_id').val());
//     telegram.apikey = $.trim($('#telegram_apikey').val());
//     if (!telegram.id || !telegram.apikey) {
//         $('#testTelegram-result').html(_('Please fill out the necessary fields above.'));
//         if (!telegram.id) {
//             $('#telegram_id').addClass('warning');
//         } else {
//             $('#telegram_id').removeClass('warning');
//         }
//         if (!telegram.apikey) {
//             $('#telegram_apikey').addClass('warning');
//         } else {
//             $('#telegram_apikey').removeClass('warning');
//         }
//         return;
//     }
//     $('#telegram_id,#telegram_apikey').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testTelegram-result').html(loading);
//     $.post(config.srRoot + '/home/testTelegram', {
//         telegram_id: telegram.id,
//         telegram_apikey: telegram.apikey
//     }).done(data => {
//         $('#testTelegram-result').html(data);
//         $('#testTelegram').prop('disabled', false);
//     });
// });
//
