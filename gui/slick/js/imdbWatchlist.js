// Avoid `console` errors in browsers that lack a console.
(function() {
    var method;
    var noop = function noop() {};
    var methods = [
        'assert', 'clear', 'count', 'debug', 'dir', 'dirxml', 'error',
        'exception', 'group', 'groupCollapsed', 'groupEnd', 'info', 'log',
        'markTimeline', 'profile', 'profileEnd', 'table', 'time', 'timeEnd',
        'timeStamp', 'trace', 'warn'
    ];
    var length = methods.length;
    var console = (window.console = window.console || {});

    while (length--) {
        method = methods[length];

        // Only stub undefined methods.
        if (!console[method]) {
            console[method] = noop;
        }
    }
}());

$(document).ready(function() {

    function addImdbWl(path) {

        if (!path.length)
            return;

        $('#imdbWl').append('<option value="'+path+'">'+path+'</option>');
        refreshImdbUrls();
        $.get(sbRoot+'/config/general/saveImdbWatchlists', { imdbWatchlistString: $('#ImdbWlText').val() });
    }

    function editImdbWl(path) {

        if (!path.length)
            return;

        // as long as something is selected
        if ($("#imdbWl option:selected").length) {

        	$("#imdbWl option:selected").text(path);
            $("#imdbWl option:selected").val(path);
        }

        refreshImdbUrls();
        $.get(sbRoot+'/config/general/saveRootDirs', {rootDirString: $('#ImdbWlText').val()});
    }
    
    $('#addImdbWl').click(function(){editText()});
    $('#editImdbWl').click(function(){editText({selectedWl: $("#imdbWl option:selected").val()})});

    $('#deleteImdbWl').click(function() {
        if ($("#imdbWl option:selected").length) {

            var toDelete = $("#imdbWl option:selected");

            toDelete.remove();
            syncOptionIDs();

        };
        
        refreshImdbUrls();
        $.get(sbRoot+'/config/general/saveImdbWatchlists', {imdbWatchlistString: $('#ImdbWlText').val()});
    });

    function syncOptionIDs() {
        // re-sync option ids
        var i = 0;
        $('#imdbWl option').each(function() {
            $(this).attr('id', 'wl-'+(i++));
        });
    }

    function refreshImdbUrls() {
    	// Rebuild the string in #ImdbWlText as url|url|url

        if (!$("#imdbWl").length)
            return;

        var do_disable = 'true';

        // if something's selected then we have some behavior to figure out
        if ($("#imdbWl option:selected").length) {
            do_disable = '';
        }

        // update the elements
        $('#deleteImdbWl').prop('disabled', do_disable);
        $('#editImdbWl').prop('disabled', do_disable);

        var log_str = '';
        var dir_text = '';

        $('#imdbWl option').each(function() {
            log_str += $(this).val();
            //Check if this is a valid IMDB link before adding it

            if (checkIMDBUrl(log_str)) {
            	if (dir_text == '') {
            		dir_text = $(this).val()
            	}
            	else {
            		dir_text += '|' + $(this).val();
            	}
            }
        });

        //console.log(log_str);
        
        $('#ImdbWlText').val(dir_text);
        $('#ImdbWlText').change();
        //console.log('ImdbWlText: '+$('#ImdbWlText').val());
    }

    function checkIMDBUrl(url) {
        if (url.match(/http.*:\/\/www\.imdb\.com\/.*/gi) &&
        		url.match(/ls[0-9]+/gi) &&
        		url.match(/ur[0-9]+/gi)) {
        	return true;
        }
        else {
        	alert(url + ' is not a valid IMDB csv export!');
        	return false;
        };
    };
    
    $('#imdbWl').click(refreshImdbUrls);

    // set up buttons on page load
    refreshImdbUrls();
    
    function editText(optionid) {
    	var updateVal = "";
    	if (optionid) {
    		updateVal = 'update-' + optionid.selectedWl;
    		$('#editImdbWlText').val(optionid.selectedWl);
    	}
    	else {
    		updateVal = 'add';
    		$('#editImdbWlText').val("");
    	}
    	$('#updateImdbWl').attr('action', updateVal);
    	$('#editImdbWlText').attr('style','display: block; width: 583px; margin-top: 4px; margin-bottom: 4px;');
    	$('#imdbWl').prop('disabled', 'true');
    	$('#updateImdbWl').attr('style','display: block;');
    	$('#editImdbWlText').select();
    }
    
    $('#updateImdbWl').click(function(){
    	// Update the Multiselect after clicking on the Update button
    	var updateText = $('#editImdbWlText').val();
    	if (checkIMDBUrl(updateText)) {
	    	if ($('#updateImdbWl').attr('action') == 'add') {
	    		addImdbWl(updateText);
	    	}
	    	else {
	    		editImdbWl(updateText);
	    	};
    	};

    	
    	$('#editImdbWlText').attr('style','display: none; width: 100%');
    	$('#imdbWl').prop('disabled', '');
    	$('#updateImdbWl').attr('style','display: none;');
    });
    
});