function generate_bwlist() {
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

function update_bwlist(show_name) {
        $('#pool').children().remove();

        $('#blackwhitelist').show();
        if (show_name) {
            $.getJSON(srRoot + '/home/fetch_releasegroups', {'show_name': show_name}, function (data) {
            if (data.result == 'success') {
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
    !$('#white option:selected').remove().appendTo('#pool');
});

$('#addW').click(function() {
    !$('#pool option:selected').remove().appendTo('#white');
});

$('#addB').click(function() {
    !$('#pool option:selected').remove().appendTo('#black');
});

$('#removeP').click(function() {
    !$('#pool option:selected').remove();
});

$('#removeB').click(function() {
    !$('#black option:selected').remove().appendTo('#pool');
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
