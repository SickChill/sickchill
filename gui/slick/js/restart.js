if (sbHttpsEnabled != "False" && sbHttpsEnabled != 0) {
    var sb_base_url = 'https://' + sbHost + ':' + sbHttpPort + sbRoot;
} else {
    var sb_base_url = 'http://' + sbHost + ':' + sbHttpPort + sbRoot;
}

var base_url = window.location.protocol + '//' + window.location.host + sbRoot;
var is_alive_url = sbRoot + '/home/is_alive/';
var timeout_id;
var current_pid = '';
var num_restart_waits = 0;
var console_debug = false
var console_prefix = 'Restart: '

function is_alive() {
	// Setup error detection
	$.ajaxSetup({
        error: ajax_error
    });
	var redirect = false
	
    timeout_id = 0;
    
	var jqxhr = $.get(is_alive_url, function(data) {

        // if it's still initializing then just wait and try again
        if (data.msg == 'nope') {
        	if (console_debug) {
        		console.log(console_prefix + 'is_alive: Sickrage is starting.')
        	}
            $('#shut_down_loading').hide();
            $('#shut_down_success').show();
            $('#restart_message').show();
        } else {
            // if this is before we've even shut down then just try again later
        	if (console_debug) {
        		console.log(console_prefix + 'is_alive: Sickrage is shutdowning.')
        	}
            if (current_pid == '' || data.msg == current_pid) {
                current_pid = data.msg;
            // if we're ready to go then redirect to new url
            } else {
            	redirect = true
            	if (console_debug) {
            		console.log(console_prefix + 'is_alive: Setting redirect.')
            	}
                $('#restart_loading').hide();
                $('#restart_success').show();
                $('#refresh_message').show();
                window.location = sbRoot + '/home/';
            }
        }
    }, 'jsonp');
	
	if (!(redirect)) {
		setTimeout(is_alive, 1000);
	}
    
    jqxhr.fail(function() {
    	ajax_error
    	})
    
    function ajax_error(x, e) {
    	if (console_debug) {
    		if (x.status == 0) {
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
}

$(document).ready(function() {

	if (console_debug) {
		console.log(console_prefix + 'Document ready.')
	}
    is_alive();

    $('#shut_down_message').ajaxError(function(e, jqxhr, settings, exception) {
    	if (console_debug) {
    		console.log(console_prefix + 'ajaxError callback: Start')
    	}
        num_restart_waits += 1;

        $('#shut_down_loading').hide();
        $('#shut_down_success').show();
        $('#restart_message').show();
        is_alive_url = sb_base_url + '/home/is_alive/';

        // if https is enabled or you are currently on https and the port or protocol changed just wait 5 seconds then redirect. 
        // This is because the ajax will fail if the cert is untrusted or the the http ajax requst from https will fail because of mixed content error.
        if ((sbHttpsEnabled != "False" && sbHttpsEnabled != 0) || window.location.protocol == "https:") {
            if (base_url != sb_base_url) {
            	if (console_debug) {
            		console.log(console_prefix + 'ajaxError callback: redirect.')
            	}
                timeout_id = 1;
                setTimeout(function(){
                    $('#restart_loading').hide();
                    $('#restart_success').show();
                    $('#refresh_message').show();
                }, 3000);
                setTimeout("window.location = sbRoot + '/home/'", 5000);
            }
        }

        // if it is taking forever just give up
        if (num_restart_waits > 90) {
        	if (console_debug) {
        		console.log(console_prefix + 'ajaxError callback: Taking to long, give up.')
        	}
            $('#restart_loading').hide();
            $('#restart_failure').show();
            $('#restart_fail_message').show();
            return;
        }

        if (timeout_id == 0) {
        	if (console_debug) {
        		console.log(console_prefix + 'ajaxError callback: call is_alive.')
        	}
            timeout_id = setTimeout('is_alive()', 1000);
        }
    });

});