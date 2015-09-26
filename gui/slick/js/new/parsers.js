$.tablesorter.addParser({
    id: 'loadingNames',
    is: function(s) {
        return false;
    },
    format: function(s) {
        if (0 === s.indexOf('Loading...')){
            return s.replace('Loading...', '000');
        } else {
            return ($('meta[data-var="sickbeard.SORT_ARTICLE"]').data('content') == 'False' ? (s || '') : (s || '').replace(/^(The|A|An)\s/i,''));
        }
    },
    type: 'text'
});
$.tablesorter.addParser({
    id: 'quality',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return s.replace('hd1080p', 5).replace('hd720p', 4).replace('hd', 3).replace('sd', 2).replace('any', 1).replace('best', 0).replace('custom', 7);
    },
    type: 'numeric'
});
$.tablesorter.addParser({
    id: 'realISODate',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return new Date(s).getTime();
    },
    type: 'numeric'
});

$.tablesorter.addParser({
    id: 'cDate',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return s;
    },
    type: 'numeric'
});
