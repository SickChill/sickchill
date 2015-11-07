$(document).ready(function(){
    $('#minLevel,#logFilter,#logSearch').on('keyup change', _.debounce(function (e) {
        if ($('#logSearch').val().length > 0){
            $('#logFilter option[value="<NONE>"]').prop('selected', true);
            $('#minLevel option[value=5]').prop('selected', true);
        }
        $('#minLevel').prop('disabled', true);
        $('#logFilter').prop('disabled', true);
        document.body.style.cursor='wait';
        var url = srRoot + '/errorlogs/viewlog/?minLevel='+$('select[name=minLevel]').val()+'&logFilter='+$('select[name=logFilter]').val()+'&logSearch='+$('#logSearch').val();
        $.get(url, function(data){
            history.pushState('data', '', url);
            $('pre').html($(data).find('pre').html());
            $('#minLevel').prop('disabled', false);
            $('#logFilter').prop('disabled', false);
            document.body.style.cursor='default';
        });
    }, 500));
});
