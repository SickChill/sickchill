$(document).ready(function () {

    $('.allCheck').on('click', function () {
        var indexerId = $(this).attr('id').split('-')[1];
        $('.' + indexerId + '-epcheck').prop('checked', $(this).prop('checked'));
    });

    $('.get_more_eps').on('click', function () {
        var curIndexerId = $(this).attr('id');
        var checked = $('#allCheck-' + curIndexerId).prop('checked');
        var lastRow = $('tr#' + curIndexerId);
        var clicked = $(this).attr('data-clicked');
        var action = $(this).attr('value');

        if (!clicked) {
            $.getJSON(srRoot + '/manage/showEpisodeStatuses', {
                'indexer_id': curIndexerId,
                whichStatus: $('#oldStatus').val()
            }, function (data) {
                $.each(data, function (season, eps) {
                    $.each(eps, function (episode, name) {
                        lastRow.after($.makeEpisodeRow(curIndexerId, season, episode, name, checked));
                    });
                });
            });
            $(this).attr('data-clicked', 1);
            $(this).prop('value', 'Collapse');
        } else {
            if (action.toLowerCase() === 'collapse') {
                $('table tr').filter('.show-' + curIndexerId).hide();
                $(this).prop('value', 'Expand');
            } else if (action.toLowerCase() === 'expand') {
                $('table tr').filter('.show-' + curIndexerId).show();
                $(this).prop('value', 'Collapse');
            }
        }
    });

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

});
