$(document).ready(function () {
    $('a.shutdown').on('click', function(e) {
        e.preventDefault();
        var target = $(this).attr('href');
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

    $('a.restart').on('click', function(e) {
        e.preventDefault();
        var target = $(this).attr('href');
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

    $('a.removeshow').on('click', function(e) {
        e.preventDefault();
        var target = $(this).attr('href');
        var showname = document.getElementById("showtitle").getAttribute('data-showname');
        $.confirm({
            'title'		: 'Remove Show',
            'message'	: 'Are you sure you want to remove <span class="footerhighlight">' + showname + '</span> from the database ?<br><br><input type="checkbox" id="deleteFiles"> <span class="red-text">Check to delete files as well. IRREVERSIBLE</span></input>',
            'buttons'	: {
                'Yes'	: {
                    'class'	: 'green',
                    'action': function(){
                        location.href = target + (document.getElementById('deleteFiles').checked ? '&full=1' : '');
                        // If checkbox is ticked, remove show and delete files. Else just remove show.
                    }
                },
                'No'	: {
                    'class'	: 'red',
                    'action': function(){}	// Nothing to do in this case. You can as well omit the action property.
                }
            }
        });
    });

    $('a.clearhistory').on('click', function(e) {
        e.preventDefault();
        var target = $(this).attr('href');
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

    $('a.trimhistory').on('click', function(e) {
        e.preventDefault();
        var target = $(this).attr('href');
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

    $('a.submiterrors').on('click', function(e) {
        e.preventDefault();
        var target = $(this).attr('href');
        $.confirm({
            'title'		: 'Submit Errors',
            'message'	: 'Are you sure you want to submit these errors ?<br><br><span class="red-text">Make sure SickRage is updated and trigger<br> this error with debug enabled before submitting</span>',
            'buttons'	: {
                'Yes'	: {
                    'class' : 'green',
                    'action': function(){
                        location.href = target;
                    }
                },
                'No'	: {
                    'class' : 'red',
                    'action': function(){}  // Nothing to do in this case. You can as well omit the action property.
                }
            }
        });
    });
});
