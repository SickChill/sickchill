var allExceptions = [];

$('#location').fileBrowser({ title: 'Select Show Location' });

$('#submit').click(function() {
    var allExceptions = [];

    $("#exceptions_list option").each(function() {
        allExceptions.push( $(this).val() );
    });

    $("#exceptions_list").val(allExceptions);

    if(metaToBool('show.is_anime')) { generate_bwlist(); }
});
$('#addSceneName').click(function() {
    var sceneEx = $('#SceneName').val();
    var option = $("<option>");
    allExceptions = [];

    $("#exceptions_list option").each(function() {
       allExceptions.push($(this).val());
    });

    $('#SceneName').val('');

    if ($.inArray(sceneEx, allExceptions) > -1 || (sceneEx === '')) { return; }

    $("#SceneException").show();

    option.attr("value",sceneEx);
    option.html(sceneEx);
    return option.appendTo('#exceptions_list');
});

$('#removeSceneName').click(function() {
    $('#exceptions_list option:selected').remove();

    $(this).toggleSceneException();
});

$.fn.toggleSceneException = function() {
    allExceptions = [];

    $("#exceptions_list option").each  ( function() {
        allExceptions.push( $(this).val() );
    });

    if (allExceptions === ''){
        $("#SceneException").hide();
    } else {
        $("#SceneException").show();
    }
};

$(this).toggleSceneException();
