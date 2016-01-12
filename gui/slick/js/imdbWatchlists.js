// Avoid `console` errors in browsers that lack a console.

function n(n){
    return n > 9 ? "" + n: "0" + n;
}

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

	
    function checkImdbWlEnabled() {
    	var kvgroups = $('.key-value-group [type="checkbox"]')
    	wl_enabled = false;
    	$(kvgroups).each(function(index, kvgroup){
    		if ( $(kvgroup).prop('checked') ) { wl_enabled = true;}
    	});
    	
    	if (wl_enabled) { $('#watchlist-warning').removeClass('hidden') }
    	else { $('#watchlist-warning').addClass('hidden') }
    }
    
	function regHandlers() {
		$('.key-value-group input').on("input", function() {
	    	fn.checkLastInput();
	    	fn.updateWatchlists();
	    });
		$('.key-value-group input').on("blur", function() {
	    	fn.updateWatchlists();
	    	fn.saveWatchlists();
	    	return false;
	    });
		$('.key-value-group input').on("click", function() {
	    	fn.updateWatchlists();
	    });
		$('.key-value-group [type="checkbox"]').on("click", function() {
	    	checkImdbWlEnabled();
	    });
	}
	
    ManageWatchlists = function  () {
    	var self = this;
    	this.rrWatchlists = [];
    	
    	/*
    	 * Class for describing a Watchlist object.
    	 */
    	function Watchlist (url, enabled, el_url) {
    	    this.url = url;
    	    if (enabled === 'on' || enabled === '1' || enabled === true) { this.enabled = 1 }
    	    else { this.enabled = 0 }
    	    
    	    if (typeof el_url === 'undefined') { el_url = false; }
    	    else {this.el_url = el_url}
    	    
    	    this.getInfo = function() {
    	        return this.url + '|' + this.enabled;
    	    };
    	    
    	    /*
        	 * Function for validating the imdb wl url.
        	 * If the url is invalid the input field will turn red
        	 * If valid the input field will turn green
        	 */
        	this.validateWatchlistUrl = function() {
        			if (this.url) {
	        			var rex_ls = /list_id=(ls\d+)/;
	            		var rex_ur = /ur\d+/;
	            		
	            		if ( rex_ur.exec(this.url) ) {
	            			//Color green
	            			$(this.el_url).css({'background-color' : '#90EE90'});
	            			return true;
	            		}
	            		else {
	            			//Color red
	            			$(this.el_url).css({'background-color' : '#FF0000'});
	            			return false;
	            		}
        			}
        			else {
        				$(this.el_url).css({'background-color' : '#FFFFFF'});
        				return false;
        			}

        	}
        	
        	this.validateWatchlistUrl();
    	}
    	
    	this.createWlInputs = function () {
    		$.each( this.ids, function( index, value ){
    			addWatchlistInput(self.ids_enabled[index], value)
    	    });
    	}
    	
    	/*
    	 * Function for retrieving data from the hidden inputs, and translating those to 
    	 * an array with Watchlist Objects
    	 * Function should only be run once, initializing!.
    	 */
    	this.initWatchlists = function() {
    		this.ids_enabled = $('#imdb_wl_ids_enabled').val().split('|');
    	    this.ids = $('#imdb_wl_ids').val().split('|');

    	    $.each( this.ids, function( index, value){
    	        wl = new Watchlist(value, self.ids_enabled[index]);
    	        self.rrWatchlists.push(wl);
    	    });
    	    
    	    this.createWlInputs();
    	    //Add an empty input
    		addWatchlistInput();
    	}
    	
    	this.updateWatchlists = function() {
    		el_ids_enabled = $('.key-value-group input[type=checkbox]');
    	    el_ids = $('.key-value-group input[type=text]');
    	    self.rrWatchlists = [];
    	    
    	    if (el_ids_enabled.length == el_ids.length) {
    	    	$.each( el_ids, function( index, el ){
        	        wl = new Watchlist($(el).val(), $(el_ids_enabled[index]).prop('checked'), el);
        	        wl.validateWatchlistUrl();
        	        self.rrWatchlists.push(wl);
        	    });
    	    }
    	    
    	    console.log('Watchlists array upated with ' + el_ids.length + ' rows');
    	    
    	}
    	
    	
    	
    	/*
    	 * This function retrieves all watchlists from the rrWatchlist array, 
    	 * and saves it into the hidden input fields. Separated with pipes (|)
    	 */
    	this.saveWatchlists = function() {
    		ids_enabled = [];
    		ids = [];
    		$.each( self.rrWatchlists, function( index, watchlist ){
    			if ( watchlist.validateWatchlistUrl() ) {
    				ids_enabled.push(watchlist.enabled);
        			ids.push(watchlist.url);
    			}
    	    });
    		
    		$('#imdb_wl_ids_enabled').val(ids_enabled.join('|'));
    		$('#imdb_wl_ids').val(ids.join('|'));
    	}
    	
    	this.checkLastInput = function() {
//    		key_value_groups = ;
//    		last_input = key_value_groups.last();
    		if ($('.key-value-group input[type="text"]').last().val()) {
    			console.log('Last input field is used.. lets generate a new one!');
    			addWatchlistInput();
    		}
    	}
    	
    	function addWatchlistInput(enabled, url) {
    		
    		if (typeof enabled === 'undefined') { enabled = ''; }
    		else if (enabled === '1') { enabled = 'checked="checked"'}
    		
    		if (typeof url === 'undefined') { url = ''; }
    		
    		key_value_groups = $('.key-value-group input[type="text"]');
        	
    		if (!key_value_groups.length) { 
    			// Create first empty input box
    			next_id = '00'
    				}
    		else {
	    		last_input = key_value_groups.last();
	    		
	    		var rex = /imdb_wl_ids-(\d+)/;
	    		var last_input_id = rex.exec(last_input.attr('id'))[1];
	    		
	    		next_id = n(parseInt(last_input_id) + 1);
    		}
    		
    		/* Let's add the html to the end of the div: <div  id="imdb-watchlist-placeholder">
    		* the resulting html shoul look as follows:
    		* <div id="kv-xx" class="key-value-group clearfix">
				<input type="checkbox"class="enabler" name="IMDB_WL_IDS_ENABLED-xx" id="imdb_wl_ids_enabled-xx" checked="checked" value="0" size="100" />
				<input type="text" name="IMDB_WL_USE_IDS-xx" id="imdb_wl_ids-xx" value="" size="40" />
			  </div>
			  x should be replaced with the next_id
    		*/
    		
    		parent = $('#imdb-watchlist-placeholder');
    		el = parent.append('<div id="kv-' + next_id + '" class="key-value-group clearfix"> <input type="checkbox" class="enabler" id="imdb_wl_ids_enabled-' + next_id + '" '+ enabled +' /><input class="form-control input200" style="margin-top: 0px" type="text" id="imdb_wl_ids-' + next_id + '" value="' + url + '" size="40" /></div>')
    		el.append('<input class="btn" type="submit" class="" value="Test Watchlist" />');
    		regHandlers();
    	}
    	
    	regHandlers();
    	self.initWatchlists();
    	self.updateWatchlists();
    }
    
    fn = new ManageWatchlists();
    fn.saveWatchlists();
    
    //Check if the disclaimer should be shown
    checkImdbWlEnabled();
    
});


