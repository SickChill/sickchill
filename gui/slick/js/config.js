$(document).ready(function(){
    $(".enabler").each(function(){
        if (!$(this).prop('checked'))
            $('#content_'+$(this).attr('id')).hide();
    });

    $(".enabler").click(function() {
        if ($(this).prop('checked'))
            $('#content_'+$(this).attr('id')).fadeIn("fast", "linear");
        else
            $('#content_'+$(this).attr('id')).fadeOut("fast", "linear");
    });

    $(".viewIf").click(function() {
        if ($(this).prop('checked')) {
            $('.hide_if_'+$(this).attr('id')).css('display','none');
            $('.show_if_'+$(this).attr('id')).fadeIn("fast", "linear");
        } else {
            $('.show_if_'+$(this).attr('id')).css('display','none');
            $('.hide_if_'+$(this).attr('id')).fadeIn("fast", "linear");
        }
    });

    $(".datePresets").click(function() {
        var def = $('#date_presets').val()
        if ($(this).prop('checked') && '%x' == def) {
            def = '%a, %b %d, %Y'
            $('#date_use_system_default').html('1')
        } else if (!$(this).prop('checked') && '1' == $('#date_use_system_default').html())
            def = '%x'

        $('#date_presets').attr('name', 'date_preset_old')
        $('#date_presets').attr('id', 'date_presets_old')

        $('#date_presets_na').attr('name', 'date_preset')
        $('#date_presets_na').attr('id', 'date_presets')

        $('#date_presets_old').attr('name', 'date_preset_na')
        $('#date_presets_old').attr('id', 'date_presets_na')

        if (def)
            $('#date_presets').val(def)
    });

    // bind 'myForm' and provide a simple callback function 
    $('#configForm').ajaxForm({
        beforeSubmit: function(){
            $('.config_submitter').each(function(){
                $(this).attr("disabled", "disabled");
                $(this).after('<span><img src="'+sbRoot+'/images/loading16.gif"> Saving...</span>');
                $(this).hide();
            });
        },
        success: function(){
            setTimeout('config_success()', 2000)
        }
    });

    $('#api_key').click(function(){ $('#api_key').select() });
    $("#generate_new_apikey").click(function(){
        $.get(sbRoot + '/config/general/generateKey', 
            function(data){
                if (data.error != undefined) {
                    alert(data.error);
                    return;
                }
                $('#api_key').val(data);
        });
    });

});

function config_success(){
    $('.config_submitter').each(function(){
        $(this).removeAttr("disabled");
        $(this).next().remove();
        $(this).show();
    });
    $('#email_show').trigger('notify');
}
