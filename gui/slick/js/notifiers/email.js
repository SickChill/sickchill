// $('#testEmail').on('click', () => {
//     let status, host, port, tls, from, user, pwd, err, to;
//     status = $('#testEmail-result');
//     status.html(loading);
//     host = $('#email_host').val();
//     host = host.length > 0 ? host : null;
//     port = $('#email_port').val();
//     port = port.length > 0 ? port : null;
//     tls = $('#email_tls').attr('checked') !== undefined ? 1 : 0;
//     from = $('#email_from').val();
//     from = from.length > 0 ? from : 'root@localhost';
//     user = $('#email_user').val().trim();
//     pwd = $('#email_password').val();
//     err = '';
//     if (host === null) {
//         err += '<li style="color: red;">You must specify an SMTP hostname!</li>';
//     }
//     if (port === null) {
//         err += '<li style="color: red;">You must specify an SMTP port!</li>';
//     } else if (port.match(/^\d+$/) === null || parseInt(port, 10) > 65535) {
//         err += '<li style="color: red;">SMTP port must be between 0 and 65535!</li>';
//     }
//     if (err.length > 0) {
//         err = '<ol>' + err + '</ol>';
//         status.html(err);
//     } else {
//         to = prompt('Enter an email address to send the test to:', null);
//         if (to === null || to.length === 0 || to.match(/.*@.*/) === null) {
//             status.html('<p style="color: red;">' + _('You must provide a recipient email address!') + '</p>');
//         } else {
//             $.post(config.srRoot + '/home/testEmail', {
//                 host,
//                 port,
//                 smtp_from: from, // @TODO we shouldn't be using any reserved words like "from"
//                 use_tls: tls,
//                 user,
//                 pwd,
//                 to
//             }, msg => {
//                 $('#testEmail-result').html(msg);
//             });
//         }
//     }
// });
