$(document).ready(function(){
    $('#minLevel,#logFilter,#logSearch').on('change', function(){
        if ($('#logSearch').val().length > 0){
            $('#logSearch').prop('disabled', true);
            $('#logFilter option[value="<NONE>"]').prop('selected', true);
            $('#minLevel option[value=5]').prop('selected', true);
        }
        $('#minLevel').prop('disabled', true);
        $('#logFilter').prop('disabled', true);
        $('#logSearch').prop('disabled', true);
        url = sbRoot + '/errorlogs/viewlog/?minLevel='+$('select[name=minLevel]').val()+'&logFilter='+$('select[name=logFilter]').val()+'&logSearch='+$('#logSearch').val();
        $.get(url, function(data){
            history.pushState('data', '', url);
            $('pre').html($(data).find('pre').html());
            $('#minLevel').removeProp('disabled');
            $('#logFilter').removeProp('disabled');
            $('#logSearch').removeProp('disabled');
        });
    });

    $(window).load(function(){
        if ( $('#logSearch').val().length === 0 ) {
            $('#minLevel').prop('disabled', false);
            $('#logFilter').prop('disabled', false);
            $('#logSearch').prop('disabled', false);
        } else {
            $('#minLevel').prop('disabled', true);
            $('#logFilter').prop('disabled', true);
            $('#logSearch').prop('disabled', false);
        }

        document.body.style.cursor='default';
    });

    $('#logSearch').on('keyup', function() {
        if ( $('#logSearch').val().length === 0 ) {
            $('#logFilter option[value=<NONE>]').prop('selected', true);
            $('#minLevel option[value=20]').prop('selected', true);
            $('#minLevel').prop('disabled', false);
            $('#logFilter').prop('disabled', false);
            url = sbRoot + '/errorlogs/viewlog/?minLevel='+$('select[name=minLevel]').val()+'&logFilter='+$('select[name=logFilter]').val()+'&logSearch='+$('#logSearch').val();
            $.get(url, function(data){
                history.pushState('data', '', url);
                $('pre').html($(data).find('pre').html());
                $('#minLevel').removeProp('disabled');
                $('#logFilter').removeProp('disabled');
                $('#logSearch').removeProp('disabled');
            });
        } else {
            $('#minLevel').prop('disabled', true);
            $('#logFilter').prop('disabled', true);
        }
    });
});

setTimeout(function () {
    "use strict";
    location.reload(true);
}, 60000);
