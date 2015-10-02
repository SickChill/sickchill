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
            9: function(node) { return $(node).find("img").attr("alt"); },
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
            7: { sorter: 'archive_firstmatch'},
            8: { sorter: 'paused'},
            9: { sorter: 'subtitle'},
           10: { sorter: 'default_ep_status'},
           11: { sorter: 'status'},
           12: { sorter: false},
           13: { sorter: false},
           14: { sorter: false},
           15: { sorter: false},
           16: { sorter: false},
           17: { sorter: false}
        }
    });
});
