$(document).ready(function() {
    window.console_debug = false; // jshint ignore:line
    window.console_prefix = 'Restart: '; // jshint ignore:line
    window.current_pid = ''; // jshint ignore:line

    var isAliveUrl = srRoot + '/home/is_alive/';

    var checkIsAlive = setInterval(isAlive, 1000);

    function isAlive() {  // jshint ignore:line
        // Setup error detection
        $.ajaxSetup({
            error: ajaxError
        });

        var jqxhr = $.get(isAliveUrl, function(data) {
            if (data.msg.toLowerCase() === 'nope') {
                // if it's still initializing then just wait and try again
                if (console_debug) { // jshint ignore:line
                    console.log(console_prefix + 'isAlive: Sickrage is starting.'); // jshint ignore:line
                }
                $('#shut_down_loading').hide();
                $('#shut_down_success').show();
                $('#restart_message').show();
            } else {
                // if this is before we've even shut down then just try again later
                if (console_debug) { // jshint ignore:line
                    console.log(console_prefix + 'isAlive: Sickrage is shutdowning.'); // jshint ignore:line
                }
                if (current_pid === '' || data.msg == current_pid) { // jshint ignore:line
                    current_pid = data.msg; // jshint ignore:line
                // if we're ready to go then redirect to new url
                } else {
                    clearInterval(checkIsAlive);
                    if (console_debug) { // jshint ignore:line
                        console.log(console_prefix + 'isAlive: Setting redirect.'); // jshint ignore:line
                    }
                    $('#restart_loading').hide();
                    $('#restart_success').show();
                    $('#refresh_message').show();
                    setTimeout(function(){window.location = srRoot + '/' + sbDefaultPage + '/';}, 5000);
                }
            }

        }, 'jsonp');

        jqxhr.fail(function() {
            ajaxError();
        });
    }

    function ajaxError(x, e) {
        if (console_debug) { // jshint ignore:line
            if (x.status === 0) {
                console.log(console_prefix + 'isAlive: Sickrage is not responding.');
            } else if (x.status == 404) {
                console.log(console_prefix + 'isAlive: Requested URL not found.');
            } else if (x.status == 500) {
                console.log(console_prefix + 'isAlive: Internel Server Error.');
            }  else {
                console.log(console_prefix + 'isAlive: Unknow Error.\n' + x.responseText);
            }
        }
    }
});
