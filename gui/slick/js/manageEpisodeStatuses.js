$(document).ready(function() {

    function makeRow(indexerId, season, episode, name, checked) {
        var row = '';
        row += ' <tr class="' + $('#row_class').val() + ' show-' + indexerId + '">';
        row += '  <td class="tableleft" align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
        row += '  <td>' + season + 'x' + episode + '</td>';
        row += '  <td class="tableright" style="width: 100%">' + name + '</td>';
        row += ' </tr>';

        return row;
    }

    $('.allCheck').click(function(){
        var indexerId = $(this).attr('id').split('-')[1];
        $('.' + indexerId + '-epcheck').prop('checked', $(this).prop('checked'));
    });

    $('.get_more_eps').click(function(){
        var curIndexerId = $(this).attr('id');
        var checked = $('#allCheck-' + curIndexerId).prop('checked');
        var lastRow = $('tr#' + curIndexerId);
        var clicked = $(this).attr('data-clicked');
        var action = $(this).attr('value');

        if(!clicked) {
            $.getJSON(srRoot+'/manage/showEpisodeStatuses',{
                indexer_id: curIndexerId, // jshint ignore:line
                whichStatus: $('#oldStatus').val()
            }, function (data) {
                $.each(data, function(season,eps){
                    $.each(eps, function(episode, name) {
                        //alert(season+'x'+episode+': '+name);
                        lastRow.after(makeRow(curIndexerId, season, episode, name, checked));
                    });
                });
            });
            $(this).attr('data-clicked',1);
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
