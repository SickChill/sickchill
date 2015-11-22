function generateBlackWhiteList() { // jshint ignore:line
    var realvalues = [];

    $('#white option').each(function(i, selected) {
        realvalues[i] = $(selected).val();
    });
    $("#whitelist").val(realvalues.join(","));

    realvalues = [];
    $('#black option').each(function(i, selected) {
        realvalues[i] = $(selected).val();
    });
    $("#blacklist").val(realvalues.join(","));
}

function updateBlackWhiteList(showName) { // jshint ignore:line
    $('#pool').children().remove();

    $('#blackwhitelist').show();
    if (showName) {
        $.getJSON(srRoot + '/home/fetch_releasegroups', {
            'show_name': showName
        }, function (data) {
            if (data.result === 'success') {
                $.each(data.groups, function(i, group) {
                    var option = $("<option>");
                    option.attr("value", group.name);
                    option.html(group.name + ' | ' + group.rating + ' | ' + group.range);
                    option.appendTo('#pool');
                });
            }
        });
    }
}

$('#removeW').click(function() {
    !$('#white option:selected').remove().appendTo('#pool'); // jshint ignore:line
});

$('#addW').click(function() {
    !$('#pool option:selected').remove().appendTo('#white'); // jshint ignore:line
});

$('#addB').click(function() {
    !$('#pool option:selected').remove().appendTo('#black'); // jshint ignore:line
});

$('#removeP').click(function() {
    !$('#pool option:selected').remove(); // jshint ignore:line
});

$('#removeB').click(function() {
    !$('#black option:selected').remove().appendTo('#pool'); // jshint ignore:line
});

$('#addToWhite').click(function() {
    var group = $('#addToPoolText').val();
    if(group !== '') {
        var option = $('<option>');
        option.attr('value',group);
        option.html(group);
        option.appendTo('#white');
        $('#addToPoolText').val('');
    }
});

$('#addToBlack').click(function() {
    var group = $('#addToPoolText').val();
    if(group !== '') {
        var option = $('<option>');
        option.attr('value',group);
        option.html(group);
        option.appendTo('#black');
        $('#addToPoolText').val('');
    }
});
