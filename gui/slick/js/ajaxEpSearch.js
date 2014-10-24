var search_status_url = sbRoot + '/getManualSearchStatus';
$.pnotify.defaults.width = "400px";
$.pnotify.defaults.styling = "jqueryui";
$.pnotify.defaults.history = false;
$.pnotify.defaults.shadow = false;
$.pnotify.defaults.delay = 4000;
$.pnotify.defaults.maxonscreen = 5;

$.fn.manualSearches = [];

function check_manual_searches() {
    var poll_interval = 5000;
    $.ajax({
        url: search_status_url + '?show=' + $('#showID').val(),
        success: function (data) {
            if (data.episodes) {
            	poll_interval = 5000;
            }
            else {
            	poll_interval = 15000;
            }
        	
            updateImages(data);
            //cleanupManualSearches(data);
        },
        error: function () {
            poll_interval = 30000;
        },
        type: "GET",
        dataType: "json",
        complete: function () {
            setTimeout(check_manual_searches, poll_interval);
        },
        timeout: 15000 // timeout every 15 secs
    });
}


function updateImages(data) {
	$.each(data.episodes, function (name, ep) {
		console.debug(ep.searchstatus);
		// Get td element for current ep
		var loadingImage = 'loading16.gif';
        var queuedImage = 'queued.png';
        var searchImage = 'search16.png';
        var status = null;
        //Try to get the <a> Element
        el=$('a[id=' + ep.season + 'x' + ep.episode+']');
        img=el.children('img');
        parent=el.parent();        
        if (el) {
        	if (ep.searchstatus == 'searching') {
				//el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
				img.attr('title','Searching');
				img.attr('alt','earching');
				img.attr('src',sbRoot+'/images/' + loadingImage);
				disableLink(el);
				// Update Status and Quality
				var rSearchTerm = /(\w+)\s\((.+?)\)/;
	            HtmlContent = ep.searchstatus;
	            
        	}
        	else if (ep.searchstatus == 'queued') {
				//el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
				img.attr('title','Queued');
				img.attr('alt','queued');
				img.attr('src',sbRoot+'/images/' + queuedImage );
				disableLink(el);
				HtmlContent = ep.searchstatus;
			}
        	else if (ep.searchstatus == 'finished') {
				//el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
				img.attr('title','Searching');
				img.attr('alt','searching');
				img.parent().attr('class','epRetry');
				img.attr('src',sbRoot+'/images/' + searchImage);
				enableLink(el);
				
				// Update Status and Quality
				var rSearchTerm = /(\w+)\s\((.+?)\)/;
	            HtmlContent = ep.status.replace(rSearchTerm,"$1"+' <span class="quality '+ep.quality+'">'+"$2"+'</span>');
		        
			}
        	// update the status column if it exists
	        parent.siblings('.status_column').html(HtmlContent)
        	
        }
		
	});
}

$(document).ready(function () {

	check_manual_searches();

});

function enableLink(el) {
	el.on('click.disabled', false);
	el.attr('enableClick', '1');
	el.fadeTo("fast", 1)
}

function disableLink(el) {
	el.off('click.disabled');
	el.attr('enableClick', '0');
	el.fadeTo("fast", .5)
}

(function(){

	$.ajaxEpSearch = {
	    defaults: {
	        size:				16,
	        colorRow:         	false,
	        loadingImage:		'loading16.gif',
	        queuedImage:		'queued.png',
	        noImage:			'no16.png',
	        yesImage:			'yes16.png'
	    }
	};

	$.fn.ajaxEpSearch = function(options){
		options = $.extend({}, $.ajaxEpSearch.defaults, options);
		
	    $('.epSearch, .epRetry').click(function(event){
	    	event.preventDefault();
	        
	    	// Check if we have disabled the click
	    	if ( $(this).attr('enableClick') == '0' ) {
	    		console.debug("Already queued, not downloading!");
	    		return false;
	    	}
	    	
	    	if ( $(this).attr('class') == "epRetry" ) {
	    		if ( !confirm("Mark download as bad and retry?") )
	                return false;
	    	};
	    	
	    	var parent = $(this).parent();
	        
	    	// Create var for anchor
	    	link = $(this);
	    	
	    	// Create var for img under anchor and set options for the loading gif
	        img=$(this).children('img');
	        img.attr('title','loading');
			img.attr('alt','');
			img.attr('src',sbRoot+'/images/' + options.loadingImage);
			
	        
	        $.getJSON($(this).attr('href'), function(data){
	            
	        	// if they failed then just put the red X
	            if (data.result == 'failure') {
	                img_name = options.noImage;
	                img_result = 'failed';

	            // if the snatch was successful then apply the corresponding class and fill in the row appropriately
	            } else {
	                img_name = options.loadingImage;
	                img_result = 'success';
	                // color the row
	                if (options.colorRow)
	                	parent.parent().removeClass('skipped wanted qual good unaired').addClass('snatched');
	                // applying the quality class
                    var rSearchTerm = /(\w+)\s\((.+?)\)/;
	                    HtmlContent = data.result.replace(rSearchTerm,"$1"+' <span class="quality '+data.quality+'">'+"$2"+'</span>');
	                // update the status column if it exists
                    parent.siblings('.status_column').html(HtmlContent)
                    // Only if the queing was succesfull, disable the onClick event of the loading image
                    disableLink(link);
	            }

	            // put the corresponding image as the result of queuing of the manual search
	            img.attr('title',img_result);
				img.attr('alt',img_result);
				img.attr('height', options.size);
				img.attr('src',sbRoot+"/images/"+img_name);
	        });
	        // 
	        
	        // don't follow the link
	        return false;
	    });
	}
})();

