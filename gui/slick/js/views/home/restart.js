$(document).ready(function () {

    var currentPid = srPID;
    var checkIsAlive = setInterval(function () {
        $.get(srRoot + '/home/is_alive/', function (data) {
            if (data.msg.toLowerCase() === 'nope') {
                // if it's still initializing then just wait and try again
                $('#restart_message').show();
            } else {
                // if this is before we've even shut down then just try again later
                if (currentPid === '' || data.msg === currentPid) {
                    $('#shut_down_loading').hide();
                    $('#shut_down_success').show();
                    currentPid = data.msg;
                } else {
                    clearInterval(checkIsAlive);
                    $('#restart_loading').hide();
                    $('#restart_success').show();
                    $('#refresh_message').show();
                    setTimeout(function () {
                        window.location = srRoot + '/' + srDefaultPage + '/';
                    }, 5000);
                }
            }
        }, 'jsonp');
    }, 100);

});
