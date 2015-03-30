var search_status_url = sbRoot + '/home/getManualSearchStatus';
var failedDownload = false
var qualityDownload = false
var selectedEpisode = ""
PNotify.prototype.options.maxonscreen = 5;

$.fn.manualSearches = [];

function check_manual_searches() {
    var poll_interval = 5000;
    showId = $('#showID').val()
    var url = ""
    if ( showId !== undefined) {
    	var url = search_status_url + '?show=' + showId;
    } else {
    	var url = search_status_url;
    }
    
    $.ajax({
        url: url,
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
		// Get td element for current ep
		var loadingImage = 'loading16.gif';
        var queuedImage = 'queued.png';
        var searchImage = 'search16.png';
        var status = null;
        //Try to get the <a> Element
        el=$('a[id=' + ep.show + 'x' + ep.season + 'x' + ep.episode+']');
        img=el.children('img');
        parent=el.parent();        
        if (el) {
        	if (ep.searchstatus == 'searching') {
				//el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
				img.prop('title','Searching');
				img.prop('alt','Searching');
				img.prop('src',sbRoot+'/images/' + loadingImage);
				disableLink(el);
				// Update Status and Quality
				var rSearchTerm = /(\w+)\s\((.+?)\)/;
	            HtmlContent = ep.searchstatus;
	            
        	}
        	else if (ep.searchstatus == 'queued') {
				//el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
				img.prop('title','Queued');
				img.prop('alt','queued');
				img.prop('src',sbRoot+'/images/' + queuedImage );
				disableLink(el);
				HtmlContent = ep.searchstatus;
			}
        	else if (ep.searchstatus == 'finished') {
				//el=$('td#' + ep.season + 'x' + ep.episode + '.search img');
				img.prop('title','Searching');
				img.prop('alt','searching');
				img.parent().prop('class','epRetry');
				img.prop('src',sbRoot+'/images/' + searchImage);
				enableLink(el);
				
				// Update Status and Quality
				var rSearchTerm = /(\w+)\s\((.+?)\)/;
	            HtmlContent = ep.status.replace(rSearchTerm,"$1"+' <span class="quality '+ep.quality+'">'+"$2"+'</span>');
	            parent.closest('tr').prop("class", ep.overview + " season-" + ep.season + " seasonstyle")
		        
			}
        	// update the status column if it exists
	        parent.siblings('.col-status').html(HtmlContent)
        	
        }
        el_comEps=$('a[id=forceUpdate-' + ep.show + 'x' + ep.season + 'x' + ep.episode+']');
        img_comEps=el_comEps.children('img');
        if (el_comEps) {
        	if (ep.searchstatus == 'searching') {
        		img_comEps.prop('title','Searching');
        		img_comEps.prop('alt','Searching');
        		img_comEps.prop('src',sbRoot+'/images/' + loadingImage);
        		disableLink(el_comEps);
        	} else if (ep.searchstatus == 'queued') {
        		img_comEps.prop('title','Queued');
        		img_comEps.prop('alt','queued');
        		img_comEps.prop('src',sbRoot+'/images/' + queuedImage );
        	} else if (ep.searchstatus == 'finished') {
        		img_comEps.prop('title','Manual Search');
        		img_comEps.prop('alt','[search]');
        		img_comEps.prop('src',sbRoot+'/images/' + searchImage);
        		if (ep.overview == 'snatched') {
        			el_comEps.closest('tr').remove();
        		} else {
        			enableLink(el_comEps);
        		}
        	}
        }
	});
}

$(document).ready(function () {

	check_manual_searches();

});

function enableLink(el) {
	el.on('click.disabled', false);
	el.prop('enableClick', '1');
	el.fadeTo("fast", 1)
}

function disableLink(el) {
	el.off('click.disabled');
	el.prop('enableClick', '0');
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
		
		$('.epRetry').click(function(event){
	    	event.preventDefault();
			
			// Check if we have disabled the click
	    	if ( $(this).prop('enableClick') == '0' ) {
	    		return false;
	    	};
			
			selectedEpisode = $(this)
			
			$("#manualSearchModalFailed").modal('show');
		});
		
		$('.epSearch').click(function(event){
	    	event.preventDefault();
			
			// Check if we have disabled the click
	    	if ( $(this).prop('enableClick') == '0' ) {
	    		return false;
	    	};
			
			selectedEpisode = $(this);
			
			if ($(this).parent().parent().children(".col-status").children(".quality").length) {
				$("#manualSearchModalQuality").modal('show');
			} else {
				manualSearch();
			}
		});
		
		$('#manualSearchModalFailed .btn').click(function(){
			val=$(this).text();
			if(val=='Yes'){
				failedDownload = true;
			} else {
				failedDownload = false;
			}
			$("#manualSearchModalQuality").modal('show');
		});
		
		$('#manualSearchModalQuality .btn').click(function(){
			val=$(this).text();
			if(val=='Yes'){
				qualityDownload = true;
			} else {
				qualityDownload = false;
			}
			manualSearch();
		});
		
		function manualSearch(){
			var parent = selectedEpisode.parent();
	        
	    	// Create var for anchor
	    	link = selectedEpisode;
	    	
	    	// Create var for img under anchor and set options for the loading gif
	        img=selectedEpisode.children('img');
	        img.prop('title','loading');
			img.prop('alt','');
			img.prop('src',sbRoot+'/images/' + options.loadingImage);
			
			var url = selectedEpisode.prop('href');
			
			if (failedDownload === false) {
				url = url.replace("retryEpisode", "searchEpisode"); 
			}
			
			if (qualityDownload === true) {
				url = url + "&downCurQuality=1";
			} else {
				url = url + "&downCurQuality=0";
			}
			
	        $.getJSON(url, function(data){
	            
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
                    parent.siblings('.col-status').html(HtmlContent)
                    // Only if the queuing was successful, disable the onClick event of the loading image
                    disableLink(link);
	            }

	            // put the corresponding image as the result of queuing of the manual search
	            img.prop('title',img_result);
				img.prop('alt',img_result);
				img.prop('height', options.size);
				img.prop('src',sbRoot+"/images/"+img_name);
	        });
	        // 
	        
	        // don't follow the link
	        return false;
		};
		
	};
})();
