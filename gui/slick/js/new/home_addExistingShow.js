$(document).ready(function(){
    $( "#tabs" ).tabs({
        collapsible: true,
        selected: ($('meta[data-var="sickbeard.SORT_ARTICLE"]').data('content') == 'True' ? -1 : 0)
    });
});
