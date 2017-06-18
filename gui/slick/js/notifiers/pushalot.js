// $('#testPushalot').on('click', function() {
//     const pushalot = {};
//     pushalot.authToken = $.trim($('#pushalot_authorizationtoken').val());
//     if (!pushalot.authToken) {
//         $('#testPushalot-result').html(_('Please fill out the necessary fields above.'));
//         $('#pushalot_authorizationtoken').addClass('warning');
//         return;
//     }
//     $('#pushalot_authorizationtoken').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testPushalot-result').html(loading);
//     $.post(config.srRoot + '/home/testPushalot', {
//         authorizationToken: pushalot.authToken
//     }).done(data => {
//         $('#testPushalot-result').html(data);
//         $('#testPushalot').prop('disabled', false);
//     });
// });
//
