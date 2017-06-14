const generateBlackWhiteList = () => {
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
};

const updateBlackWhiteList = showName => {
    $('#pool').children().remove();

    $('#blackwhitelist').show();
    if (showName) {
        $.getJSON(srRoot + '/home/fetch_releasegroups', {
            show_name: showName // eslint-disable-line camelcase
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
};

$('#removeW').click(() => {
    !$('#white option:selected').remove().appendTo('#pool'); // eslint-disable-line no-unused-expressions
});

$('#addW').click(() => {
    !$('#pool option:selected').remove().appendTo('#white'); // eslint-disable-line no-unused-expressions
});

$('#addB').click(() => {
    !$('#pool option:selected').remove().appendTo('#black'); // eslint-disable-line no-unused-expressions
});

$('#removeP').click(() => {
    !$('#pool option:selected').remove(); // eslint-disable-line no-unused-expressions
});

$('#removeB').click(() => {
    !$('#black option:selected').remove().appendTo('#pool'); // eslint-disable-line no-unused-expressions
});

$('#addToWhite').click(() => {
    const group = $('#addToPoolText').val();
    if (group !== '') {
        const option = $('<option>');
        option.attr('value', group);
        option.html(group);
        option.appendTo('#white');
        $('#addToPoolText').val('');
    }
});

$('#addToBlack').click(() => {
    const group = $('#addToPoolText').val();
    if (group !== '') {
        const option = $('<option>');
        option.attr('value', group);
        option.html(group);
        option.appendTo('#black');
        $('#addToPoolText').val('');
    }
});

export {
    generateBlackWhiteList,
    updateBlackWhiteList
};
