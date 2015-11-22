$(document).ready(function(){
    $( "#tabs" ).tabs({
        collapsible: true,
        selected: (metaToBool('sickbeard.SORT_ARTICLE') ? -1 : 0)
    });
});
