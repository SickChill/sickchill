$(document).ready(function() { 

    function make_row(indexer_id, season, episode, name, checked) {
        if (checked)
            var checked = ' checked';
        else
            var checked = '';
        
        var row_class = $('#row_class').val();
        
        var row = '';
        row += ' <tr class="'+row_class+' show-'+indexer_id+'">';
        row += '  <td class="tableleft" align="center"><input type="checkbox" class="'+indexer_id+'-epcheck" name="'+indexer_id+'-'+season+'x'+episode+'"'+checked+'></td>';
        row += '  <td>'+season+'x'+episode+'</td>';
        row += '  <td class="tableright" style="width: 100%">'+name+'</td>';
        row += ' </tr>'
        
        return row;
    }

    $('.allCheck').click(function(){
        var indexer_id = $(this).attr('id').split('-')[1];
        $('.'+indexer_id+'-epcheck').prop('checked', $(this).prop('checked'));
    });

    $('.get_more_eps').click(function(){
        var cur_indexer_id = $(this).attr('id');
        var checked = $('#allCheck-'+cur_indexer_id).prop('checked');
        var last_row = $('tr#'+cur_indexer_id);
        var clicked = $(this).attr('data-clicked');
        var action = $(this).attr('value');
        
        if (!clicked)  {
            $.getJSON(sbRoot+'/manage/showEpisodeStatuses',
                      {
                       indexer_id: cur_indexer_id,
                       whichStatus: $('#oldStatus').val()
                      },
                      function (data) {
                          $.each(data, function(season,eps){
                              $.each(eps, function(episode, name) {
                                  //alert(season+'x'+episode+': '+name);
                                  last_row.after(make_row(cur_indexer_id, season, episode, name, checked));
                              });
                          });
                      });
            $(this).attr('data-clicked',1);   
            $(this).prop('value', 'Collapse');
        } else {
            if (action === 'Collapse') {
                $('table tr').filter('.show-'+cur_indexer_id).hide();
                $(this).prop('value', 'Expand');
            }
            else if (action === 'Expand') {
                $('table tr').filter('.show-'+cur_indexer_id).show();
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