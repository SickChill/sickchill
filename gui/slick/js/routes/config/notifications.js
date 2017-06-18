import {GrowlNotifier, KodiNotifier, ProwlNotifier} from '../../notifiers';

export default () => {
    const growl = new GrowlNotifier();
    const kodi = new KodiNotifier();
    const prowl = new ProwlNotifier();

    growl.init();
    kodi.init();
    prowl.init();

    // $('#settingsNMJ').on('click', () => {
    //     const nmj = {};
    //     if (!$('#nmj_host').val()) {
    //         $('#nmj_host').focus();
    //         notifyModal('Please fill in the Popcorn IP address');
    //         return;
    //     }
    //     $('#testNMJ-result').html(loading);
    //     nmj.host = $('#nmj_host').val();
    //
    //     $.post(config.srRoot + '/home/settingsNMJ', {host: nmj.host}, data => {
    //         if (data === null) {
    //             $('#nmj_database').removeAttr('readonly');
    //             $('#nmj_mount').removeAttr('readonly');
    //         }
    //         const JSONData = $.parseJSON(data);
    //         $('#testNMJ-result').html(JSONData.message);
    //         $('#nmj_database').val(JSONData.database);
    //         $('#nmj_mount').val(JSONData.mount);
    //
    //         if (JSONData.database) {
    //             $('#nmj_database').attr('readonly', true);
    //         } else {
    //             $('#nmj_database').removeAttr('readonly');
    //         }
    //         if (JSONData.mount) {
    //             $('#nmj_mount').attr('readonly', true);
    //         } else {
    //             $('#nmj_mount').removeAttr('readonly');
    //         }
    //     });
    // });
    //
    // $('#testNMJ').on('click', function() {
    //     const nmj = {};
    //     nmj.host = $.trim($('#nmj_host').val());
    //     nmj.database = $('#nmj_database').val();
    //     nmj.mount = $('#nmj_mount').val();
    //     if (!nmj.host) {
    //         $('#testNMJ-result').html(_('Please fill out the necessary fields above.'));
    //         $('#nmj_host').addClass('warning');
    //         return;
    //     }
    //     $('#nmj_host').removeClass('warning');
    //     $(this).prop('disabled', true);
    //     $('#testNMJ-result').html(loading);
    //     $.post(config.srRoot + '/home/testNMJ', {
    //         host: nmj.host,
    //         database: nmj.database,
    //         mount: nmj.mount
    //     }).done(data => {
    //         $('#testNMJ-result').html(data);
    //         $('#testNMJ').prop('disabled', false);
    //     });
    // });
    //
    // $('#settingsNMJv2').on('click', () => {
    //     const nmjv2 = {};
    //     if (!$('#nmjv2_host').val()) {
    //         $('#nmjv2_host').focus();
    //         notifyModal('Please fill in the Popcorn IP address', 'modal');
    //         return;
    //     }
    //     $('#testNMJv2-result').html(loading);
    //     nmjv2.host = $('#nmjv2_host').val();
    //     nmjv2.dbloc = '';
    //     const radios = document.getElementsByName('nmjv2_dbloc');
    //     for (let i = 0, len = radios.length; i < len; i++) {
    //         if (radios[i].checked) {
    //             nmjv2.dbloc = radios[i].value;
    //             break;
    //         }
    //     }
    //
    //     nmjv2.dbinstance = $('#NMJv2db_instance').val();
    //     $.post(config.srRoot + '/home/settingsNMJv2', {
    //         host: nmjv2.host,
    //         dbloc: nmjv2.dbloc,
    //         instance: nmjv2.dbinstance
    //     }, data => {
    //         if (data === null) {
    //             $('#nmjv2_database').removeAttr('readonly');
    //         }
    //         const JSONData = $.parseJSON(data);
    //         $('#testNMJv2-result').html(JSONData.message);
    //         $('#nmjv2_database').val(JSONData.database);
    //
    //         if (JSONData.database) {
    //             $('#nmjv2_database').attr('readonly', true);
    //         } else {
    //             $('#nmjv2_database').removeAttr('readonly');
    //         }
    //     });
    // });
    //
    // $('#testNMJv2').on('click', function() {
    //     const nmjv2 = {};
    //     nmjv2.host = $.trim($('#nmjv2_host').val());
    //     if (!nmjv2.host) {
    //         $('#testNMJv2-result').html(_('Please fill out the necessary fields above.'));
    //         $('#nmjv2_host').addClass('warning');
    //         return;
    //     }
    //     $('#nmjv2_host').removeClass('warning');
    //     $(this).prop('disabled', true);
    //     $('#testNMJv2-result').html(loading);
    //     $.post(config.srRoot + '/home/testNMJv2', {
    //         host: nmjv2.host
    //     }).done(data => {
    //         $('#testNMJv2-result').html(data);
    //         $('#testNMJv2').prop('disabled', false);
    //     });
    // });
    //
    //
    // $('#testNMA').on('click', function() {
    //     const nma = {};
    //     nma.api = $.trim($('#nma_api').val());
    //     nma.priority = $('#nma_priority').val();
    //     if (!nma.api) {
    //         $('#testNMA-result').html(_('Please fill out the necessary fields above.'));
    //         $('#nma_api').addClass('warning');
    //         return;
    //     }
    //     $('#nma_api').removeClass('warning');
    //     $(this).prop('disabled', true);
    //     $('#testNMA-result').html(loading);
    //     $.post(config.srRoot + '/home/testNMA', {
    //         nma_api: nma.api, // eslint-disable-line camelcase
    //         nma_priority: nma.priority // eslint-disable-line camelcase
    //     }).done(data => {
    //         $('#testNMA-result').html(data);
    //         $('#testNMA').prop('disabled', false);
    //     });
    // });
    //
    //
    // $('#email_show').on('change', () => {
    //     const key = parseInt($('#email_show').val(), 10);
    //     $.getJSON(config.srRoot + '/home/loadShowNotifyLists', notifyData => {
    //         if (notifyData._size > 0) {
    //             $('#email_show_list').val(key >= 0 ? notifyData[key.toString()].list : '');
    //         }
    //     });
    // });
    // $('#prowl_show').on('change', () => {
    //     const key = parseInt($('#prowl_show').val(), 10);
    //     $.getJSON(config.srRoot + '/home/loadShowNotifyLists', notifyData => {
    //         if (notifyData._size > 0) {
    //             $('#prowl_show_list').val(key >= 0 ? notifyData[key.toString()].prowl_notify_list : '');
    //         }
    //     });
    // });
    //
    // function loadShowNotifyLists() {
    //     $.getJSON(config.srRoot + '/home/loadShowNotifyLists', list => {
    //         let html, s;
    //         if (list._size === 0) {
    //             return;
    //         }
    //
    //         // Convert the 'list' object to a js array of objects so that we can sort it
    //         const _list = [];
    //         for (s in list) {
    //             if (s.charAt(0) !== '_') {
    //                 _list.push(list[s]);
    //             }
    //         }
    //         const sortedList = _list.sort((a, b) => {
    //             if (a.name < b.name) {
    //                 return -1;
    //             }
    //             if (a.name > b.name) {
    //                 return 1;
    //             }
    //             return 0;
    //         });
    //         html = '<option value="-1">-- Select --</option>';
    //         for (s in sortedList) {
    //             if (sortedList[s].id && sortedList[s].name) {
    //                 html += '<option value="' + sortedList[s].id + '">' + $('<div/>').text(sortedList[s].name).html() + '</option>';
    //             }
    //         }
    //         $('#email_show').html(html);
    //         $('#email_show_list').val('');
    //
    //         $('#prowl_show').html(html);
    //         $('#prowl_show_list').val('');
    //     });
    // }
    // // Load the per show notify lists everytime this page is loaded
    // loadShowNotifyLists();
    //
    // // Update the internal data struct anytime settings are saved to the server
    // $('#email_show').on('notify', () => {
    //     loadShowNotifyLists();
    // });
    // $('#prowl_show').on('notify', () => {
    //     loadShowNotifyLists();
    // });
    //
    // $('#email_show_save').on('click', () => {
    //     $.post(config.srRoot + '/home/saveShowNotifyList', {
    //         show: $('#email_show').val(),
    //         emails: $('#email_show_list').val()
    //     }, () => {
    //         // Reload the per show notify lists to reflect changes
    //         loadShowNotifyLists();
    //     });
    // });
    // $('#prowl_show_save').on('click', () => {
    //     $.post(config.srRoot + '/home/saveShowNotifyList', {
    //         show: $('#prowl_show').val(),
    //         prowlAPIs: $('#prowl_show_list').val()
    //     }, () => {
    //         // Reload the per show notify lists to reflect changes
    //         loadShowNotifyLists();
    //     });
    // });
    //
};
