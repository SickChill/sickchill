// $('#testPushbullet').on('click', function() {
//     const pushbullet = {};
//     pushbullet.api = $.trim($('#pushbullet_api').val());
//     if (!pushbullet.api) {
//         $('#testPushbullet-result').html(_('Please fill out the necessary fields above.'));
//         $('#pushbullet_api').addClass('warning');
//         return;
//     }
//     $('#pushbullet_api').removeClass('warning');
//     $(this).prop('disabled', true);
//     $('#testPushbullet-result').html(loading);
//     $.post(config.srRoot + '/home/testPushbullet', {
//         api: pushbullet.api
//     }).done(data => {
//         $('#testPushbullet-result').html(data);
//         $('#testPushbullet').prop('disabled', false);
//     });
// });
//
// function getPushbulletDevices(msg) {
//     const pushbullet = {};
//     pushbullet.api = $('#pushbullet_api').val();
//
//     if (msg) {
//         $('#testPushbullet-result').html(loading);
//     }
//
//     if (!pushbullet.api) {
//         $('#testPushbullet-result').html(_('You didn\'t supply a Pushbullet api key'));
//         $('#pushbullet_api').focus();
//         return false;
//     }
//
//     $.post(config.srRoot + '/home/getPushbulletDevices', {
//         api: pushbullet.api
//     }, data => {
//         pushbullet.devices = $.parseJSON(data).devices;
//         pushbullet.currentDevice = $('#pushbullet_device').val();
//         $('#pushbullet_device_list').html('');
//         for (let i = 0, len = pushbullet.devices.length; i < len; i++) {
//             if (pushbullet.devices[i].active === true) {
//                 if (pushbullet.currentDevice === pushbullet.devices[i].iden) {
//                     $('#pushbullet_device_list').append('<option value="' + pushbullet.devices[i].iden + '" selected>' + pushbullet.devices[i].nickname + '</option>');
//                 } else {
//                     $('#pushbullet_device_list').append('<option value="' + pushbullet.devices[i].iden + '">' + pushbullet.devices[i].nickname + '</option>');
//                 }
//             }
//         }
//         $('#pushbullet_device_list').prepend('<option value="" ' + (pushbullet.currentDevice === '' ? 'selected' : '') + '>All devices</option>');
//         if (msg) {
//             $('#testPushbullet-result').html(msg);
//         }
//     });
//
//     $('#pushbullet_device_list').on('change', () => {
//         $('#pushbullet_device').val($('#pushbullet_device_list').val());
//         $('#testPushbullet-result').html(_('Don\'t forget to save your new pushbullet settings.'));
//     });
//
//     $.post(config.srRoot + '/home/getPushbulletChannels', {
//         api: pushbullet.api
//     }, data => {
//         pushbullet.channels = $.parseJSON(data).channels;
//         pushbullet.currentChannel = $('#pushbullet_channel').val();
//         $('#pushbullet_channel_list').html('');
//         if (pushbullet.channels.length > 0) {
//             for (let i = 0, len = pushbullet.channels.length; i < len; i++) {
//                 if (pushbullet.channels[i].active === true) {
//                     $('#pushbullet_channel_list').append('<option value="' + pushbullet.channels[i].tag + '" selected>' + pushbullet.channels[i].name + '</option>');
//                 } else {
//                     $('#pushbullet_channel_list').append('<option value="' + pushbullet.channels[i].tag + '">' + pushbullet.channels[i].name + '</option>');
//                 }
//             }
//             $('#pushbullet_channel_list').prepend('<option value="" ' + (pushbullet.currentChannel ? 'selected' : '') + '>No Channel</option>');
//             $('#pushbullet_channel_list').prop('disabled', false);
//         } else {
//             $('#pushbullet_channel_list').prepend('<option value>No Channels</option>');
//             $('#pushbullet_channel_list').prop('disabled', true);
//         }
//         if (msg) {
//             $('#testPushbullet-result').html(msg);
//         }
//
//         $('#pushbullet_channel_list').on('change', () => {
//             $('#pushbullet_channel').val($('#pushbullet_channel_list').val());
//             $('#testPushbullet-result').html(_('Don\'t forget to save your new pushbullet settings.'));
//         });
//     });
// }
//
// $('#getPushbulletDevices').on('click', () => {
//     getPushbulletDevices('Device list updated. Please choose a device to push to.');
// });
//
// // We have to call this function on dom ready to create the devices select
// getPushbulletDevices();
