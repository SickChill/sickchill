var all_exceptions = [];

$('#location').fileBrowser({ title: 'Select Show Location' });

$('#submit').click(function(){
    all_exceptions = [];

    $("#exceptions_list option").each  ( function() {
        all_exceptions.push( $(this).val() );
    });

    $("#exceptions_list").val(all_exceptions);

    if(metaToBool('show.is_anime')) generate_bwlist();
});
$('#addSceneName').click(function() {
    var scene_ex = $('#SceneName').val();
    var option = $("<option>");
    all_exceptions = [];

    $("#exceptions_list option").each  ( function() {
       all_exceptions.push($(this).val());
    });

    $('#SceneName').val('');

    if ($.inArray(scene_ex, all_exceptions) > -1 || (scene_ex === '')) return;

    $("#SceneException").show();

    option.attr("value",scene_ex);
    option.html(scene_ex);
    return option.appendTo('#exceptions_list');
});

$('#removeSceneName').click(function() {
    $('#exceptions_list option:selected').remove();

    $(this).toggle_SceneException();
});

$.fn.toggle_SceneException = function() {
    all_exceptions = [];

    $("#exceptions_list option").each  ( function() {
        all_exceptions.push( $(this).val() );
    });

    if (all_exceptions === ''){
        $("#SceneException").hide();
    } else {
        $("#SceneException").show();
    }
};

$(this).toggle_SceneException();
