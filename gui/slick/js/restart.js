$(document).ready(function() {
    window.console_debug = false;
    window.console_prefix = 'Restart: ';
    window.current_pid = '';

    var is_alive_url = srRoot + '/home/is_alive/';

    var check_isAlive = setInterval(is_alive, 1000);

    function is_alive() {
        // Setup error detection
        $.ajaxSetup({
            error: ajax_error
        });

        var jqxhr = $.get(is_alive_url, function(data) {
            if (data.msg == 'nope') {
                // if it's still initializing then just wait and try again
                if (console_debug) {
                    console.log(console_prefix + 'is_alive: Sickrage is starting.');
                }
                $('#shut_down_loading').hide();
                $('#shut_down_success').show();
                $('#restart_message').show();
            } else {
                // if this is before we've even shut down then just try again later
                if (console_debug) {
                    console.log(console_prefix + 'is_alive: Sickrage is shutdowning.');
                }
                if (current_pid === '' || data.msg == current_pid) {
                    current_pid = data.msg;
                // if we're ready to go then redirect to new url
                } else {
                    clearInterval(check_isAlive);
                    if (console_debug) {
                        console.log(console_prefix + 'is_alive: Setting redirect.');
                    }
                    $('#restart_loading').hide();
                    $('#restart_success').show();
                    $('#refresh_message').show();
                    setTimeout(function(){window.location = srRoot + '/' + sbDefaultPage + '/';}, 5000);
                }
            }

        }, 'jsonp');

        jqxhr.fail(function() {
            ajax_error();
        });
    }

    function ajax_error(x, e) {
        if (console_debug) {
            if (x.status === 0) {
                console.log(console_prefix + 'is_alive: Sickrage is not responding.');
            } else if (x.status == 404) {
                console.log(console_prefix + 'is_alive: Requested URL not found.');
            } else if (x.status == 500) {
                console.log(console_prefix + 'is_alive: Internel Server Error.');
            }  else {
                console.log(console_prefix + 'is_alive: Unknow Error.\n' + x.responseText);
            }
        }
    }
});
