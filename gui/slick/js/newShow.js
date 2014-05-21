$(document).ready(function () {

    function populateSelect() {
        if (!$('#nameToSearch').length) {
            return;
        }

        if ($('#indexerLangSelect option').length <= 1) {
            $.getJSON(sbRoot + '/home/addShows/getIndexerLanguages', {}, function (data) {
                var selected, resultStr = '';

                if (data.results.length === 0) {
                    resultStr = '<option value="en" selected="selected">en</option>';
                } else {
                    $.each(data.results, function (index, obj) {
                        if (resultStr == '') {
                            selected = ' selected="selected"';
                        } else {
                            selected = '';
                        }

                        resultStr += '<option value="' + obj + '"' + selected + '>' + obj + '</option>';
                    });
                }

                $('#indexerLangSelect').html(resultStr);
                $('#indexerLangSelect').change(function () { searchIndexers(); });
            });
        }
    }

    var searchRequestXhr = null;

    function searchIndexers() {
        if (!$('#nameToSearch').val().length) {
            return;
        }

        if (searchRequestXhr) searchRequestXhr.abort();

        var searchingFor = $('#nameToSearch').val() + ' on ' + $('#providedIndexer option:selected').text() + ' in ' + $('#indexerLangSelect').val();
        $('#searchResults').empty().html('<img id="searchingAnim" src="' + sbRoot + '/images/loading32.gif" height="32" width="32" /> searching ' + searchingFor + '...');

        searchRequestXhr = $.ajax({
            url: sbRoot + '/home/addShows/searchIndexersForShowName',
            data: {'search_term': $('#nameToSearch').val(), 'lang': $('#indexerLangSelect').val(), 'indexer': $('#providedIndexer').val()},
            timeout: parseInt($('#indexer_timeout').val(), 10) * 1000,
            dataType: 'json',
            error: function () {
                $('#searchResults').empty().html('search timed out, try again or try another indexer');
            },
            success: function (data) {
                var firstResult = true;
                var resultStr = '<fieldset>\n<legend>Search Results:</legend>\n';
                var checked = '';

                if (data.results.length === 0) {
                    resultStr += '<b>No results found, try a different search.</b>';
                } else {
                    $.each(data.results, function (index, obj) {
                        if (firstResult) {
                            checked = ' checked';
                            firstResult = false;
                        } else {
                            checked = '';
                        }

                        var whichSeries = obj.join('|');


                        resultStr += '<input type="radio" id="whichSeries" name="whichSeries" value="' + whichSeries + '"' + checked + ' /> ';
                        if (data.langid && data.langid != "") {
                            resultStr += '<a href="'+ obj[2] + obj[3] + '&lid=' + data.langid + '" onclick=\"window.open(this.href, \'_blank\'); return false;\" ><b>' + obj[4] + '</b></a>';
                        } else {
                            resultStr += '<a href="'+ obj[2] + obj[3] + '" onclick=\"window.open(this.href, \'_blank\'); return false;\" ><b>' + obj[4] + '</b></a>';
                        }

                        if (obj[5] !== null) {
                            var startDate = new Date(obj[5]);
                            var today = new Date();
                            if (startDate > today) {
                                resultStr += ' (will debut on ' + obj[5] + ')';
                            } else {
                                resultStr += ' (started on ' + obj[5] + ')';
                            }
                        }

                        if (obj[0] !== null) {
                            resultStr += ' [' + obj[0] + ']';
                        }

                        resultStr += '<br />';
                    });
                    resultStr += '</ul>';
                }
                resultStr += '</fieldset>';
                $('#searchResults').html(resultStr);
                updateSampleText();
                myform.loadsection(0);
            }
        });
    }

    $('#searchName').click(function () { searchIndexers(); });

    if ($('#nameToSearch').length && $('#nameToSearch').val().length) {
        $('#searchName').click();
    }

    $('#addShowButton').click(function () {
        // if they haven't picked a show don't let them submit
        if (!$("input:radio[name='whichSeries']:checked").val() && !$("input:hidden[name='whichSeries']").val().length) {
            alert('You must choose a show to continue');
            return false;
        }

        $('#addShowForm').submit();
    });

    $('#skipShowButton').click(function () {
        $('#skipShow').val('1');
        $('#addShowForm').submit();
    });

    $('#qualityPreset').change(function () {
        myform.loadsection(2);
    });

    /***********************************************
    * jQuery Form to Form Wizard- (c) Dynamic Drive (www.dynamicdrive.com)
    * This notice MUST stay intact for legal use
    * Visit http://www.dynamicdrive.com/ for this script and 100s more.
    ***********************************************/

    var myform = new formtowizard({
        formid: 'addShowForm',
        revealfx: ['slide', 500],
        oninit: function () {
            populateSelect();
            updateSampleText();
            if ($('input:hidden[name=whichSeries]').length && $('#fullShowPath').length) {
                goToStep(3);
            }
        }
    });

    function goToStep(num) {
        $('.step').each(function () {
            if ($.data(this, 'section') + 1 == num) {
                $(this).click();
            }
        });
    }

    $('#nameToSearch').focus();

    function updateSampleText() {
        // if something's selected then we have some behavior to figure out

        var show_name, sep_char;
        // if they've picked a radio button then use that
        if ($('input:radio[name=whichSeries]:checked').length) {
            show_name = $('input:radio[name=whichSeries]:checked').val().split('|')[4];
        }
        // if we provided a show in the hidden field, use that
        else if ($('input:hidden[name=whichSeries]').length && $('input:hidden[name=whichSeries]').val().length) {
            show_name = $('#providedName').val();
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
            ($('input:radio[name=whichSeries]:checked').length) || ($('input:hidden[name=whichSeries]').length && $('input:hidden[name=whichSeries]').val().length)) {
            $('#addShowButton').attr('disabled', false);
        } else {
            $('#addShowButton').attr('disabled', true);
        }
    }

    $('#rootDirText').change(updateSampleText);
    $('#whichSeries').live('change', updateSampleText);

    $('#nameToSearch').keyup(function (event) {
        if (event.keyCode == 13) {
            $('#searchName').click();
        }
    });

});
