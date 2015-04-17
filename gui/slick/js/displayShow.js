$(document).ready(function () {

    $('#sbRoot').ajaxEpSearch({'colorRow': true});

    $('#sbRoot').ajaxEpSubtitlesSearch();

    $('#seasonJump').change(function () {
        var id = $('#seasonJump option:selected').val();
        if (id && id != 'jump') {
        	$('html,body').animate({scrollTop: $('[name ="' + id.substring(1) + '"]').offset().top - 50}, 'slow');
            location.hash = id;
        }
        $(this).val('jump');
    });

    $("#prevShow").click(function () {
        $('#pickShow option:selected').prev('option').prop('selected', 'selected');
        $("#pickShow").change();
    });

    $("#nextShow").click(function () {
        $('#pickShow option:selected').next('option').prop('selected', 'selected');
        $("#pickShow").change();
    });

    $('#changeStatus').click(function () {
        var sbRoot = $('#sbRoot').val();
        var epArr = new Array()

        $('.epCheck').each(function () {

            if (this.checked == true) {
                epArr.push($(this).attr('id'))
            }

        });

        if (epArr.length == 0)
            return false;

        url = sbRoot + '/home/setStatus?show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|') + '&status=' + $('#statusSelect').val();
        window.location.href = url

    });

    $('.seasonCheck').click(function () {
        var seasCheck = this;
        var seasNo = $(seasCheck).attr('id');

        $('.epCheck:visible').each(function () {
            var epParts = $(this).attr('id').split('x');

            if (epParts[0] == seasNo) {
                this.checked = seasCheck.checked
            }
        });
    });

    var lastCheck = null;
    $('.epCheck').click(function (event) {

        if (!lastCheck || !event.shiftKey) {
            lastCheck = this;
            return;
        }

        var check = this;
        var found = 0;

        $('.epCheck').each(function () {
            switch (found) {
                case 2:
                    return false;
                case 1:
                    this.checked = lastCheck.checked;
            }

            if (this == check || this == lastCheck)
                found++;
        });

        lastClick = this;
    });

    // selects all visible episode checkboxes.
    $('.seriesCheck').click(function () {
        $('.epCheck:visible').each(function () {
            this.checked = true
        });
        $('.seasonCheck:visible').each(function () {
            this.checked = true
        })
    });

    // clears all visible episode checkboxes and the season selectors
    $('.clearAll').click(function () {
        $('.epCheck:visible').each(function () {
            this.checked = false
        });
        $('.seasonCheck:visible').each(function () {
            this.checked = false
        });
    });

    // handle the show selection dropbox
    $('#pickShow').change(function () {
        var sbRoot = $('#sbRoot').val();
        var val = $(this).val();
        if (val == 0)
            return;
        url = sbRoot + '/home/displayShow?show=' + val;
        window.location.href = url
    });

    // show/hide different types of rows when the checkboxes are changed
    $("#checkboxControls input").change(function (e) {
        var whichClass = $(this).attr('id');
        $(this).showHideRows(whichClass);
    });

    // initially show/hide all the rows according to the checkboxes
    $("#checkboxControls input").each(function (e) {
        var status = this.checked;
        $("tr." + $(this).attr('id')).each(function (e) {
            if (status) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });

    $.fn.showHideRows = function (whichClass) {

        var status = $('#checkboxControls > input, #' + whichClass).prop('checked');
        $("tr." + whichClass).each(function (e) {
            if (status) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });

        // hide season headers with no episodes under them
        $('tr.seasonheader').each(function () {
            var numRows = 0;
            var seasonNo = $(this).attr('id');
            $('tr.' + seasonNo + ' :visible').each(function () {
                numRows++
            });
            if (numRows == 0) {
                $(this).hide();
                $('#' + seasonNo + '-cols').hide()
            } else {
                $(this).show();
                $('#' + seasonNo + '-cols').show()
            }

        });
    };

    function setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode) {
        var sbRoot = $('#sbRoot').val();
        var showId = $('#showID').val();
        var indexer = $('#indexer').val();

        if (sceneSeason === '') sceneSeason = null;
        if (sceneEpisode === '') sceneEpisode = null;

        $.getJSON(sbRoot + '/home/setSceneNumbering',
            {
                'show': showId,
                'indexer': indexer,
                'forSeason': forSeason,
                'forEpisode': forEpisode,
                'sceneSeason': sceneSeason,
                'sceneEpisode': sceneEpisode
            },
            function (data) {
                //	Set the values we get back
                if (data.sceneSeason === null || data.sceneEpisode === null) {
                    $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val('');
                }
                else {
                    $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val(data.sceneSeason + 'x' + data.sceneEpisode);
                }
                if (!data.success) {
                    if (data.errorMessage) {
                        alert(data.errorMessage);
                    } else {
                        alert('Update failed.');
                    }
                }
            }
        );
    }

    function setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute) {
        var sbRoot = $('#sbRoot').val();
        var showId = $('#showID').val();
        var indexer = $('#indexer').val();

        if (sceneAbsolute === '') sceneAbsolute = null;

        $.getJSON(sbRoot + '/home/setSceneNumbering',
            {
                'show': showId,
                'indexer': indexer,
                'forAbsolute': forAbsolute,
                'sceneAbsolute': sceneAbsolute
            },
            function (data) {
                //	Set the values we get back
                if (data.sceneAbsolute === null) {
                    $('#sceneAbsolute_' + showId + '_' + forAbsolute).val('');
                }
                else {
                    $('#sceneAbsolute_' + showId + '_' + forAbsolute).val(data.sceneAbsolute);
                }
                if (!data.success) {
                    if (data.errorMessage) {
                        alert(data.errorMessage);
                    } else {
                        alert('Update failed.');
                    }
                }
            }
        );
    }

    $('.sceneSeasonXEpisode').change(function () {
        //	Strip non-numeric characters
        $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
        var forSeason = $(this).attr('data-for-season');
        var forEpisode = $(this).attr('data-for-episode');
        var showId = $('#showID').val();
        var indexer = $('#indexer').val();

        //var sceneEpisode = $('#sceneEpisode_' + showId + '_' + forSeason +'_' + forEpisode).val();
        var m = $(this).val().match(/^(\d+)x(\d+)$/i);
        var sceneSeason = null, sceneEpisode = null;
        if (m) {
            sceneSeason = m[1];
            sceneEpisode = m[2];
        }
        setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode);
    });

    $('.sceneAbsolute').change(function () {
        //	Strip non-numeric characters
        $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
        var forAbsolute = $(this).attr('data-for-absolute');
        var showId = $('#showID').val();
        var indexer = $('#indexer').val();

        var m = $(this).val().match(/^(\d{1,3})$/i);
        var sceneAbsolute = null;
        if (m) {
            sceneAbsolute = m[1];
        }
        setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute);
    });   
});
