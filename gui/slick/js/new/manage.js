$.tablesorter.addParser({
    id: 'showNames',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return ($('meta[data-var="sickbeard.SORT_ARTICLE"]').data('content') == 'True' ? (s || '') : (s || '').replace(/^(The|A|An)\s/i,''));
    },
    type: 'text'
});
$.tablesorter.addParser({
    id: 'quality',
    is: function(s) {
        return false;
    },
    format: function(s) {
        return s.replace('hd1080p',5).replace('hd720p',4).replace('hd',3).replace('sd',2).replace('any',1).replace('best',0).replace('custom',7);
    },
    type: 'numeric'
});

$(document).ready(function(){
    $("#massUpdateTable:has(tbody tr)").tablesorter({
        sortList: [[1,0]],
        textExtraction: {
            2: function(node) { return $(node).find("span").text().toLowerCase(); },
            3: function(node) { return $(node).find("img").attr("alt"); },
            4: function(node) { return $(node).find("img").attr("alt"); },
            5: function(node) { return $(node).find("img").attr("alt"); },
            6: function(node) { return $(node).find("img").attr("alt"); },
            7: function(node) { return $(node).find("img").attr("alt"); },
            8: function(node) { return $(node).find("img").attr("alt"); },
        },
        widgets: ['zebra'],
        headers: {
            0: { sorter: false},
            1: { sorter: 'showNames'},
            2: { sorter: 'quality'},
            3: { sorter: 'sports'},
            4: { sorter: 'scene'},
            5: { sorter: 'anime'},
            6: { sorter: 'flatfold'},
            7: { sorter: 'paused'},
            8: { sorter: 'subtitle'},
            9: { sorter: 'default_ep_status'},
           10: { sorter: 'status'},
           11: { sorter: false},
           12: { sorter: false},
           13: { sorter: false},
           14: { sorter: false},
           15: { sorter: false},
           16: { sorter: false},
           17: { sorter: false}
        }
    });
});
