$(document).ready(function(){
	
	var shiftReturn = function(array){
		// Performs .shift() on array.
		// Returns: the new array
		if (array.length <= 1) { return []; }
		array.shift();
		return array;
	};
	
	$('a.removehistory').on('click', function(){
        var removeArr = [];
		var removeCount = 0;

        $('.removeCheck').each(function() {
            if(this.checked === true) {
				removeArr.push(shiftReturn($(this).attr('id').split('-')));
				removeCount++; }
        });

        if(removeCount < 1) { return false; }
		
		$.confirm({
			title: "Remove Logs",
			text: "You have selected to remove " + removeCount + " download history log(s).<br /><br />This cannot be undone.<br />Are you sure you wish to continue?",
			confirmButton: "Yes",
			cancelButton: "Cancel",
			dialogClass: "modal-dialog",
			post: false,
			confirm: function() {
				var url = srRoot + '/history/removeHistory';
				var params = 'toRemove='+removeArr.join('|');
				$.post(url, params, function() { location.reload(true); });
			}
		});
		
		return false; // disable link action - don't go anywhere!
    });

    ['.removeCheck'].forEach(function(name) {
        var lastCheck = null;

        $(name).on('click', function(event) {
            if(!lastCheck || !event.shiftKey) {
                lastCheck = this;
                return;
            }

            var check = this;
            var found = 0;

            $(name).each(function() {
                switch (found) {
                    case 2: return false;
                    case 1: if(!this.disabled) { this.checked = lastCheck.checked; }
                }
                if(this === check || this === lastCheck) { found++; }
            });
        });
    });
});
