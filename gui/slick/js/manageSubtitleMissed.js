$(document).ready(function() {

    function makeRow(indexerId, season, episode, name, subtitles, checked) {
        checked = checked ? ' checked' : '';

        var row = '';
        row += ' <tr class="good show-' + indexerId + '">';
        row += '  <td align="center"><input type="checkbox" class="'+indexerId+'-epcheck" name="'+indexerId+'-'+season+'x'+episode+'"'+checked+'></td>';
        row += '  <td style="width: 1%;">'+season+'x'+episode+'</td>';
        row += '  <td>'+name+'</td>';
        row += ' </tr>';

        return row;
    }

    $('.allCheck').click(function(){
        var indexerId = $(this).attr('id').split('-')[1];
        $('.'+indexerId+'-epcheck').prop('checked', $(this).prop('checked'));
    });

    $('.get_more_eps').click(function(){
        var indexerId = $(this).attr('id');
        var checked = $('#allCheck-'+indexerId).prop('checked');
        var lastRow = $('tr#'+indexerId);
        var clicked = $(this).attr('data-clicked');
        var action = $(this).attr('value');

        if (!clicked) {
            $.getJSON(srRoot + '/manage/showSubtitleMissed', {
                indexer_id: indexerId, // jshint ignore:line
                whichSubs: $('#selectSubLang').val()
            }, function(data) {
                $.each(data, function(season, eps) {
                    $.each(eps, function(episode, data) {
                        //alert(season+'x'+episode+': '+name);
                        lastRow.after(makeRow(indexerId, season, episode, data.name, data.subtitles, checked));
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

    // selects all visible episode checkboxes.
    $('.selectAllShows').click(function(){
        $('.allCheck').each(function(){
                this.checked = true;
        });
        $('input[class*="-epcheck"]').each(function(){
                this.checked = true;
        });
    });

    // clears all visible episode checkboxes and the season selectors
    $('.unselectAllShows').click(function(){
        $('.allCheck').each(function(){
                this.checked = false;
        });
        $('input[class*="-epcheck"]').each(function(){
                this.checked = false;
        });
    });
});
