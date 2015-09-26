$(document).ready(function(){
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
            columnSelector_saveColumns: true,
            columnSelector_layout : '<br/><label><input type="checkbox">{name}</label>',
            columnSelector_mediaquery: false,
            columnSelector_cssChecked : 'checked'
        },
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
