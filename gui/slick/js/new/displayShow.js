$(document).ready(function(){

    $('#srRoot').ajaxEpSearch({'colorRow': true});

    $('#srRoot').ajaxEpSubtitlesSearch();

    $('#seasonJump').on('change', function(){
        var id = $('#seasonJump option:selected').val();
        if (id && id !== 'jump') {
            var season = $('#seasonJump option:selected').data('season');
            $('html,body').animate({scrollTop: $('[name ="' + id.substring(1) + '"]').offset().top - 50}, 'slow');
            $('#collapseSeason-' + season).collapse('show');
            location.hash = id;
        }
        $(this).val('jump');
    });

    $("#prevShow").on('click', function(){
        $('#pickShow option:selected').prev('option').prop('selected', 'selected');
        $("#pickShow").change();
    });

    $("#nextShow").on('click', function(){
        $('#pickShow option:selected').next('option').prop('selected', 'selected');
        $("#pickShow").change();
    });

    $('#changeStatus').on('click', function(){
        var srRoot = $('#srRoot').val();
        var epArr = [];

        $('.epCheck').each(function () {
            if (this.checked === true) {
                epArr.push($(this).attr('id'));
            }
        });

        if (epArr.length === 0) { return false; }

        window.location.href = srRoot + '/home/setStatus?show=' + $('#showID').attr('value') + '&eps=' + epArr.join('|') + '&status=' + $('#statusSelect').val();
    });

    $('.seasonCheck').on('click', function(){
        var seasCheck = this;
        var seasNo = $(seasCheck).attr('id');

        $('#collapseSeason-' + seasNo).collapse('show');
        $('.epCheck:visible').each(function () {
            var epParts = $(this).attr('id').split('x');
            if (epParts[0] === seasNo) {
                this.checked = seasCheck.checked;
            }
        });
    });

    var lastCheck = null;
    $('.epCheck').on('click', function (event) {

        if (!lastCheck || !event.shiftKey) {
            lastCheck = this;
            return;
        }

        var check = this;
        var found = 0;

        $('.epCheck').each(function() {
            switch (found) {
                case 2:
                    return false;
                case 1:
                    this.checked = lastCheck.checked;
            }

            if (this === check || this === lastCheck) {
                found++;
            }
        });
    });

    // selects all visible episode checkboxes.
    $('.seriesCheck').on('click', function () {
        $('.epCheck:visible').each(function () {
            this.checked = true;
        });
        $('.seasonCheck:visible').each(function () {
            this.checked = true;
        });
    });

    // clears all visible episode checkboxes and the season selectors
    $('.clearAll').on('click', function () {
        $('.epCheck:visible').each(function () {
            this.checked = false;
        });
        $('.seasonCheck:visible').each(function () {
            this.checked = false;
        });
    });

    // handle the show selection dropbox
    $('#pickShow').on('change', function () {
        var srRoot = $('#srRoot').val();
        var val = $(this).val();
        if (val === 0) {
            return;
        }
        window.location.href = srRoot + '/home/displayShow?show=' + val;
    });

    // show/hide different types of rows when the checkboxes are changed
    $("#checkboxControls input").change(function () {
        var whichClass = $(this).attr('id');
        $(this).showHideRows(whichClass);
    });

    // initially show/hide all the rows according to the checkboxes
    $("#checkboxControls input").each(function() {
        var status = $(this).prop('checked');
        $("tr." + $(this).attr('id')).each(function() {
            if(status) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });

    $.fn.showHideRows = function(whichClass) {
        var status = $('#checkboxControls > input, #' + whichClass).prop('checked');
        $("tr." + whichClass).each(function() {
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
                numRows++;
            });
            if (numRows === 0) {
                $(this).hide();
                $('#' + seasonNo + '-cols').hide();
            } else {
                $(this).show();
                $('#' + seasonNo + '-cols').show();
            }
        });
    };

    function setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode) {
        var srRoot = $('#srRoot').val();
        var showId = $('#showID').val();
        var indexer = $('#indexer').val();

        if (sceneSeason === '') { sceneSeason = null; }
        if (sceneEpisode === '') { sceneEpisode = null; }

        $.getJSON(srRoot + '/home/setSceneNumbering',{
            'show': showId,
            'indexer': indexer,
            'forSeason': forSeason,
            'forEpisode': forEpisode,
            'sceneSeason': sceneSeason,
            'sceneEpisode': sceneEpisode
        }, function(data) {
            //	Set the values we get back
            if (data.sceneSeason === null || data.sceneEpisode === null) {
                $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val('');
            } else {
                $('#sceneSeasonXEpisode_' + showId + '_' + forSeason + '_' + forEpisode).val(data.sceneSeason + 'x' + data.sceneEpisode);
            }
            if (!data.success) {
                if (data.errorMessage) {
                    alert(data.errorMessage);
                } else {
                    alert('Update failed.');
                }
            }
        });
    }

    function setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute) {
        var srRoot = $('#srRoot').val();
        var showId = $('#showID').val();
        var indexer = $('#indexer').val();

        if (sceneAbsolute === '') { sceneAbsolute = null; }

        $.getJSON(srRoot + '/home/setSceneNumbering', {
            'show': showId,
            'indexer': indexer,
            'forAbsolute': forAbsolute,
            'sceneAbsolute': sceneAbsolute
        },
        function(data) {
            //	Set the values we get back
            if (data.sceneAbsolute === null) {
                $('#sceneAbsolute_' + showId + '_' + forAbsolute).val('');
            } else {
                $('#sceneAbsolute_' + showId + '_' + forAbsolute).val(data.sceneAbsolute);
            }
            if (!data.success) {
                if (data.errorMessage) {
                    alert(data.errorMessage);
                } else {
                    alert('Update failed.');
                }
            }
        });
    }

    $('.sceneSeasonXEpisode').on('change', function() {
        //	Strip non-numeric characters
        $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
        var forSeason = $(this).attr('data-for-season');
        var forEpisode = $(this).attr('data-for-episode');
        var m = $(this).val().match(/^(\d+)x(\d+)$/i);
        var sceneSeason = null, sceneEpisode = null;
        if (m) {
            sceneSeason = m[1];
            sceneEpisode = m[2];
        }
        setEpisodeSceneNumbering(forSeason, forEpisode, sceneSeason, sceneEpisode);
    });

    $('.sceneAbsolute').on('change', function() {
        //	Strip non-numeric characters
        $(this).val($(this).val().replace(/[^0-9xX]*/g, ''));
        var forAbsolute = $(this).attr('data-for-absolute');

        var m = $(this).val().match(/^(\d{1,3})$/i);
        var sceneAbsolute = null;
        if (m) {
            sceneAbsolute = m[1];
        }
        setAbsoluteSceneNumbering(forAbsolute, sceneAbsolute);
    });

    $('.addQTip').each(function () {
        $(this).css({'cursor':'help', 'text-shadow':'0px 0px 0.5px #666'});
        $(this).qtip({
            show: {solo:true},
            position: {viewport:$(window), my:'left center', adjust:{ y: -10, x: 2 }},
            style: {tip:{corner:true, method:'polygon'}, classes:'qtip-rounded qtip-shadow ui-tooltip-sb'}
        });
    });
    $.fn.generateStars = function() {
        return this.each(function(i,e){$(e).html($('<span/>').width($(e).text()*12));});
    };

    $('.imdbstars').generateStars();

    $("#showTable, #animeTable").tablesorter({
        widgets: ['saveSort', 'stickyHeaders', 'columnSelector'],
        widgetOptions : {
            columnSelector_saveColumns: true, // jshint ignore:line
            columnSelector_layout : '<br><label><input type="checkbox">{name}</label>', // jshint ignore:line
            columnSelector_mediaquery: false, // jshint ignore:line
            columnSelector_cssChecked : 'checked' // jshint ignore:line
        }
    });

    $('#popover').popover({
        placement: 'bottom',
        html: true, // required if content has HTML
        content: '<div id="popover-target"></div>'
    })
    // bootstrap popover event triggered when the popover opens
    .on('shown.bs.popover', function () {
        $.tablesorter.columnSelector.attachTo( $("#showTable, #animeTable"), '#popover-target');
    });
});
