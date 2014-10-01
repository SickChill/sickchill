$(document).ready(function () {
	$('a.shutdown').bind("click",function(e) {
		e.preventDefault();
		var target = $( this ).attr('href');
		$.confirm({
			'title'		: 'Shutdown',
			'message'	: 'Are you sure you want to shutdown SickRage ?',
			'buttons'	: {
				'Yes'	: {
					'class'	: 'green',
					'action': function(){
						location.href = target;
					}
				},
				'No'	: {
					'class'	: 'red',
					'action': function(){}	// Nothing to do in this case. You can as well omit the action property.
				}
			}
		});
	});

	$('a.restart').bind("click",function(e) {
		e.preventDefault();
		var target = $( this ).attr('href');
		$.confirm({
			'title'		: 'Restart',
			'message'	: 'Are you sure you want to restart SickRage ?',
			'buttons'	: {
				'Yes'	: {
					'class'	: 'green',
					'action': function(){
						location.href = target;
					}
				},
				'No'	: {
					'class'	: 'red',
					'action': function(){}	// Nothing to do in this case. You can as well omit the action property.
				}
			}
		});
	});
	
	$('a.delete').bind("click",function(e) {
		e.preventDefault();
		var target = $( this ).attr('href');
		var showname = document.getElementById("showtitle").getAttribute('data-showname');
		$.confirm({
			'title'		: 'Delete Show',
			'message'	: 'Are you sure you want to permanently delete <font color="#09A2FF">' + showname + '</font> ? <br /><br /> <font color="red">WARNING - This process will also delete all stored files. <br /> This process cannot be un-done.</font>',
			'buttons'	: {
				'Yes'	: {
					'class'	: 'green',
					'action': function(){
						location.href = target;
					}
				},
				'No'	: {
					'class'	: 'red',
					'action': function(){}	// Nothing to do in this case. You can as well omit the action property.
				}
			}
		});
	});
	
	$('a.remove').bind("click",function(e) {
		e.preventDefault();
		var target = $( this ).attr('href');
		var showname = document.getElementById("showtitle").getAttribute('data-showname');
		$.confirm({
			'title'		: 'Remove Show',
			'message'	: 'Are you sure you want to remove <font color="#09A2FF">' + showname + '</font> from the database ?',
			'buttons'	: {
				'Yes'	: {
					'class'	: 'green',
					'action': function(){
						location.href = target;
					}
				},
				'No'	: {
					'class'	: 'red',
					'action': function(){}	// Nothing to do in this case. You can as well omit the action property.
				}
			}
		});
	});

	$('a.clearhistory').bind("click",function(e) {
		e.preventDefault();
		var target = $( this ).attr('href');
		$.confirm({
			'title'		: 'Clear History',
			'message'	: 'Are you sure you want to clear all download history ?',
			'buttons'	: {
				'Yes'	: {
					'class'	: 'green',
					'action': function(){
						location.href = target;
					}
				},
				'No'	: {
					'class'	: 'red',
					'action': function(){}	// Nothing to do in this case. You can as well omit the action property.
				}
			}
		});
	});
	
	$('a.trimhistory').bind("click",function(e) {
		e.preventDefault();
		var target = $( this ).attr('href');
		$.confirm({
			'title'		: 'Trim History',
			'message'	: 'Are you sure you want to trim all download history older than 30 days ?',
			'buttons'	: {
				'Yes'	: {
					'class'	: 'green',
					'action': function(){
						location.href = target;
					}
				},
				'No'	: {
					'class'	: 'red',
					'action': function(){}	// Nothing to do in this case. You can as well omit the action property.
				}
			}
		});
	});
	
});