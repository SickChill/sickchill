$(document).ready(function () {
    $('#searchResults').html('<img id="searchingAnim" src="' + sbRoot + '/images/loading32' + themeSpinner + '.gif" height="32" width="32" /> loading recommended shows...');
    function getRecommendedShows() {
        $.getJSON(sbRoot + '/home/addShows/getRecommendedShows', {}, function (data) {
            var firstResult = true;
            var resultStr = '<fieldset>\n<legend>Recommended Shows:</legend>\n';
            var checked = '';

            if (data.results.length === 0) {
                resultStr += '<b>No recommended shows found, update your watched shows list on trakt.tv.</b>';
            } else {
                $.each(data.results, function (index, obj) {
                    if (obj[2] !== null) {
                        if (firstResult) {
                            checked = ' checked';
                            firstResult = false;
                        } else {
                            checked = '';
                        }
                        
                        var whichSeries = obj.join('|');
                        
                        resultStr += '<input type="radio" id="whichSeries" name="whichSeries" value="' + whichSeries + '"' + checked + ' /> ';
                        resultStr += '<a href="' + anonURL + obj[1] + '" onclick="window.open(this.href, \'_blank\'); return false;"><b>' + obj[2] + '</b></a>';
                        
                        if (obj[4] !== null) {
                            var startDate = new Date(obj[4]);
                            var today = new Date();
                            if (startDate > today) {
                                resultStr += ' (will debut on ' + obj[4] + ')';
                            } else {
                                resultStr += ' (started on ' + obj[4] + ')';
                            }
                        }
                        
                        if (obj[0] !== null) {
                            resultStr += ' [' + obj[0] + ']';
                        }
                        
                        if (obj[3] !== null) {
                            resultStr += '<br />' + obj[3];
                        }
                        
                        resultStr += '<p /><br />';
                    }
                });
                resultStr += '</ul>';
            }
            resultStr += '</fieldset>';
            $('#searchResults').html(resultStr);
            updateSampleText();
            myform.loadsection(0);
        });
    }

    $('#addShowButton').click(function () {
        // if they haven't picked a show don't let them submit
        if (!$("input:radio[name='whichSeries']:checked").val() && !$("input:hidden[name='whichSeries']").val().length) {
            alert('You must choose a show to continue');
            return false;
        }

        $('#recommendedShowsForm').submit();
    });

    $('#qualityPreset').change(function () {
        myform.loadsection(2);
    });

    var myform = new formtowizard({
        formid: 'recommendedShowsForm',
        revealfx: ['slide', 500],
        oninit: function () {
            getRecommendedShows();
            updateSampleText();
        }
    });

    function goToStep(num) {
        $('.step').each(function () {
            if ($.data(this, 'section') + 1 == num) {
                $(this).click();
            }
        });
    }

    function updateSampleText() {
        // if something's selected then we have some behavior to figure out

        var show_name, sep_char;
        // if they've picked a radio button then use that
        if ($('input:radio[name=whichSeries]:checked').length) {
            show_name = $('input:radio[name=whichSeries]:checked').val().split('|')[2];
        } else {
            show_name = '';
        }

        var sample_text = 'Adding show <b>' + show_name + '</b> into <b>';

        // if we have a root dir selected, figure out the path
        if ($("#rootDirs option:selected").length) {
            var root_dir_text = $('#rootDirs option:selected').val();
            if (root_dir_text.indexOf('/') >= 0) {
                sep_char = '/';
            } else if (root_dir_text.indexOf('\\') >= 0) {
                sep_char = '\\';
            } else {
                sep_char = '';
            }

            if (root_dir_text.substr(sample_text.length - 1) != sep_char) {
                root_dir_text += sep_char;
            }
            root_dir_text += '<i>||</i>' + sep_char;

            sample_text += root_dir_text;
        } else if ($('#fullShowPath').length && $('#fullShowPath').val().length) {
            sample_text += $('#fullShowPath').val();
        } else {
            sample_text += 'unknown dir.';
        }

        sample_text += '</b>';

        // if we have a show name then sanitize and use it for the dir name
        if (show_name.length) {
            $.get(sbRoot + '/home/addShows/sanitizeFileName', {name: show_name}, function (data) {
                $('#displayText').html(sample_text.replace('||', data));
            });
        // if not then it's unknown
        } else {
            $('#displayText').html(sample_text.replace('||', '??'));
        }

        // also toggle the add show button
        if (($("#rootDirs option:selected").length || ($('#fullShowPath').length && $('#fullShowPath').val().length)) &&
            ($('input:radio[name=whichSeries]:checked').length)) {
            $('#addShowButton').attr('disabled', false);
        } else {
            $('#addShowButton').attr('disabled', true);
        }
    }

    $('#rootDirText').change(updateSampleText);
    $('#searchResults').on('change', '#whichSeries', updateSampleText);

});
