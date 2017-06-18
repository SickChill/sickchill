// $('#twitterStep1').on('click', () => {
//     $('#testTwitter-result').html(loading);
//     $.get(config.srRoot + '/home/twitterStep1', data => {
//         window.open(data);
//     }).done(() => {
//         $('#testTwitter-result').html(_('<b>Step 1:</b> Confirm Authorization'));
//     });
// });
//
// $('#twitterStep2').on('click', () => {
//     const twitter = {};
//     twitter.key = $.trim($('#twitter_key').val());
//     if (!twitter.key) {
//         $('#testTwitter-result').html(_('Please fill out the necessary fields above.'));
//         $('#twitter_key').addClass('warning');
//         return;
//     }
//     $('#twitter_key').removeClass('warning');
//     $('#testTwitter-result').html(loading);
//     $.get(config.srRoot + '/home/twitterStep2', {
//         key: twitter.key
//     }, data => {
//         $('#testTwitter-result').html(data);
//     });
// });
//
// $('#testTwitter').on('click', () => {
//     $.post(config.srRoot + '/home/testTwitter', data => {
//         $('#testTwitter-result').html(data);
//     });
// });
