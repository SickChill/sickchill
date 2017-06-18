//
// $('#testBoxcar2').on('click', function() {
//     const boxcar2 = {};
//     boxcar2.accesstoken = $.trim($('#boxcar2_accesstoken').val());
//     if (!boxcar2.accesstoken) {
//         $('#testBoxcar2-result').html(_('Please fill out the necessary fields above.'));
//         $('#boxcar2_accesstoken').addClass('warning');
//         return;
//     }
//     $('#boxcar2_accesstoken').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testBoxcar2-result').html(loading);
//     $.get(config.srRoot + '/home/testBoxcar2', {
//         accesstoken: boxcar2.accesstoken
//     }).done(data => {
//         $('#testBoxcar2-result').html(data);
//         $('#testBoxcar2').prop('disabled', false);
//     });
// });
