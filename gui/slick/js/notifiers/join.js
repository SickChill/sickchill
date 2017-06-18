// $('#testJoin').on('click', function() {
//     const join = {};
//     join.id = $.trim($('#join_id').val());
//     join.apikey = $.trim($('#join_apikey').val());
//     if (!join.id || !join.apikey) {
//         $('#testJoin-result').html(_('Please fill out the necessary fields above.'));
//         if (!join.id) {
//             $('#join_id').addClass('warning');
//         } else {
//             $('#join_id').removeClass('warning');
//         }
//         if (!join.apikey) {
//             $('#join_apikey').addClass('warning');
//         } else {
//             $('#join_apikey').removeClass('warning');
//         }
//         return;
//     }
//     $('#join_id,#join_apikey').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testJoin-result').html(loading);
//     $.post(config.srRoot + '/home/testJoin', {
//         join_id: join.id,
//         join_apikey: join.apikey
//     }).done(data => {
//         $('#testJoin-result').html(data);
//         $('#testJoin').prop('disabled', false);
//     });
// });
//
