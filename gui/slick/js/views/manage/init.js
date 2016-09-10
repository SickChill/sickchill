$.makeEpisodeRow = function (indexerId, season, episode, name, checked) {
    var row = '';
    row += ' <tr class="' + $('#row_class').val() + ' show-' + indexerId + '">';
    row += '  <td class="tableleft" align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
    row += '  <td>' + season + 'x' + episode + '</td>';
    row += '  <td class="tableright" style="width: 100%">' + name + '</td>';
    row += ' </tr>';

    return row;
};

$.makeSubtitleRow = function (indexerId, season, episode, name, subtitles, checked) {
    var row = '';
    row += '<tr class="good show-' + indexerId + '">';
    row += '<td align="center"><input type="checkbox" class="' + indexerId + '-epcheck" name="' + indexerId + '-' + season + 'x' + episode + '"' + (checked ? ' checked' : '') + '></td>';
    row += '<td style="width: 2%;">' + season + 'x' + episode + '</td>';
    if (subtitles.length > 0) {
        row += '<td style="width: 8%;">';
        subtitles = subtitles.split(',');
        for (var i in subtitles) {
            if (subtitles.hasOwnProperty(i)) {
                row += '<img src="' + srRoot + '/images/subtitles/flags/' + subtitles[i] + '.png" width="16" height="11" alt="' + subtitles[i] + '" />&nbsp;';
            }
        }
        row += '</td>';
    } else {
        row += '<td style="width: 8%;">None</td>';
    }
    row += '<td>' + name + '</td>';
    row += '</tr>';

    return row;
};
