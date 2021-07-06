function generateBlackWhiteList() { // eslint-disable-line no-unused-vars
    let realvalues = [];

    $('#white option').each((i, selected) => {
        realvalues[i] = $(selected).val();
    });
    $('#whitelist').val(realvalues.join(','));

    realvalues = [];
    $('#black option').each((i, selected) => {
        realvalues[i] = $(selected).val();
    });
    $('#blacklist').val(realvalues.join(','));
}

function updateBlackWhiteList(showName) { // eslint-disable-line no-unused-vars
    $('#pool').children().remove();

    $('#blackwhitelist').show();
    if (showName) {
        $.getJSON(scRoot + '/home/fetch_releasegroups', {
            show_name: showName, // eslint-disable-line camelcase
        }, data => {
            if (data.result === 'success') {
                $.each(data.groups, (i, group) => {
                    const option = $('<option>');
                    option.attr('value', group.name);
                    option.html(group.name + ' | ' + group.rating + ' | ' + group.range);
                    option.appendTo('#pool');
                });
            }
        });
    }
}

$('#removeW').on('click', () => {
    !$('#white option:selected').remove().appendTo('#pool'); // eslint-disable-line no-unused-expressions
});

$('#addW').on('click', () => {
    !$('#pool option:selected').remove().appendTo('#white'); // eslint-disable-line no-unused-expressions
});

$('#addB').on('click', () => {
    !$('#pool option:selected').remove().appendTo('#black'); // eslint-disable-line no-unused-expressions
});

$('#removeP').on('click', () => {
    !$('#pool option:selected').remove(); // eslint-disable-line no-unused-expressions
});

$('#removeB').on('click', () => {
    !$('#black option:selected').remove().appendTo('#pool'); // eslint-disable-line no-unused-expressions
});

$('#addToWhite').on('click', () => {
    const group = $('#addToPoolText').val();
    if (group !== '') {
        const option = $('<option>');
        option.attr('value', group);
        option.html(group);
        option.appendTo('#white');
        $('#addToPoolText').val('');
    }
});

$('#addToBlack').on('click', () => {
    const group = $('#addToPoolText').val();
    if (group !== '') {
        const option = $('<option>');
        option.attr('value', group);
        option.html(group);
        option.appendTo('#black');
        $('#addToPoolText').val('');
    }
});
