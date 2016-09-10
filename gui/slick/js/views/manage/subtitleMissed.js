$('.allCheck').on('click', function () {
    var indexerId = $(this).attr('id').split('-')[1];
    $('.' + indexerId + '-epcheck').prop('checked', $(this).prop('checked'));
});

$('.get_more_eps').on('click', function () {
    var indexerId = $(this).attr('id');
    var checked = $('#allCheck-' + indexerId).prop('checked');
    var lastRow = $('tr#' + indexerId);
    var clicked = $(this).attr('data-clicked');
    var action = $(this).attr('value');

    if (!clicked) {
        $.getJSON(srRoot + '/manage/showSubtitleMissed', {
            'indexer_id': indexerId,
            'whichSubs': $('#selectSubLang').val()
        }, function (data) {
            $.each(data, function (season, eps) {
                $.each(eps, function (episode, data) {
                    lastRow.after($.makeSubtitleRow(indexerId, season, episode, data.name, data.subtitles, checked));
                });
            });
        });
        $(this).attr('data-clicked', 1);
        $(this).prop('value', 'Collapse');
    } else {
        if (action === 'Collapse') {
            $('table tr').filter('.show-' + indexerId).hide();
            $(this).prop('value', 'Expand');
        } else if (action === 'Expand') {
            $('table tr').filter('.show-' + indexerId).show();
            $(this).prop('value', 'Collapse');
        }
    }
});

// @TODO these two should be able to be merged by using a generic class for the selector

// selects all visible episode checkboxes.
$('.selectAllShows').on('click', function () {
    $('.allCheck').each(function () {
        this.checked = true;
    });
    $('input[class*="-epcheck"]').each(function () {
        this.checked = true;
    });
});

// clears all visible episode checkboxes and the season selectors
$('.unselectAllShows').on('click', function () {
    $('.allCheck').each(function () {
        this.checked = false;
    });
    $('input[class*="-epcheck"]').each(function () {
        this.checked = false;
    });
});
