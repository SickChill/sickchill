$(document).ready(function () {

    $("#massUpdateTable:has(tbody tr)").tablesorter({
        sortList: [[1, 0]],
        textExtraction: {
            2: function (node) {
                return $(node).find("span").text().toLowerCase();
            },
            3: function (node) {
                return $(node).find("img").attr("alt");
            },
            4: function (node) {
                return $(node).find("img").attr("alt");
            },
            5: function (node) {
                return $(node).find("img").attr("alt");
            },
            6: function (node) {
                return $(node).find("img").attr("alt");
            },
            7: function (node) {
                return $(node).find("img").attr("alt");
            },
            8: function (node) {
                return $(node).find("img").attr("alt");
            },
            9: function (node) {
                return $(node).find("img").attr("alt");
            }
        },
        widgets: ['zebra', 'filter', 'columnSelector'],
        headers: {
            0: {sorter: false, filter: false},
            1: {sorter: 'showNames'},
            2: {sorter: 'quality'},
            3: {sorter: 'sports'},
            4: {sorter: 'scene'},
            5: {sorter: 'anime'},
            6: {sorter: 'flatfold'},
            7: {sorter: 'paused'},
            8: {sorter: 'subtitle'},
            9: {sorter: 'default_ep_status'},
            10: {sorter: 'status'},
            11: {sorter: false},
            12: {sorter: false},
            13: {sorter: false},
            14: {sorter: false},
            15: {sorter: false},
            16: {sorter: false}
        },
        widgetOptions: {
            'columnSelector_mediaquery': false
        }
    });

    ['.editCheck', '.updateCheck', '.refreshCheck', '.renameCheck', '.deleteCheck', '.removeCheck'].forEach(function(name) {
        var lastCheck = null;

        $(name).on('click', function(event) {
            if(!lastCheck || !event.shiftKey) {
                lastCheck = this;
                return;
            }

            var check = this;
            var found = 0;

            $(name).each(function() {
                switch (found) {
                    case 2: return false;
                    case 1: if(!this.disabled) { this.checked = lastCheck.checked; }
                }
                if(this === check || this === lastCheck) { found++; }
            });
        });
    });

    $('#popover').popover({
        placement: 'bottom',
        html: true, // required if content has HTML
        content: '<div id="popover-target"></div>'
    }).on('shown.bs.popover', function () { // bootstrap popover event triggered when the popover opens
        // call this function to copy the column selection code into the popover
        $.tablesorter.columnSelector.attachTo($('#massUpdateTable'), '#popover-target');
    });

});

$('.resetsorting').on('click', function () {
    $('table').trigger('filterReset');
});

$('.submitMassEdit').on('click', function(){
    var editArr = [];

    $('.editCheck').each(function() {
        if(this.checked === true) { editArr.push($(this).attr('id').split('-')[1]); }
    });

    if(editArr.length === 0) { return; }

    var submitForm = $(
        "<form method='post' action='" + srRoot + "/manage/massEdit'>" +
        "<input type='hidden' name='toEdit' value='" + editArr.join('|') + "'/>" +
        "</form>"
    );
    submitForm.appendTo('body');

    submitForm.submit();
});

$('.submitMassUpdate').on('click', function(){
    var updateArr = [];
    var refreshArr = [];
    var renameArr = [];
    var subtitleArr = [];
    var deleteArr = [];
    var removeArr = [];
    var metadataArr = [];

    $('.updateCheck').each(function() {
        if(this.checked === true) { updateArr.push($(this).attr('id').split('-')[1]); }
    });

    $('.refreshCheck').each(function() {
        if(this.checked === true) { refreshArr.push($(this).attr('id').split('-')[1]); }
    });

    $('.renameCheck').each(function() {
        if(this.checked === true) { renameArr.push($(this).attr('id').split('-')[1]); }
    });

    $('.subtitleCheck').each(function() {
        if(this.checked === true) { subtitleArr.push($(this).attr('id').split('-')[1]); }
    });

    $('.removeCheck').each(function() {
        if(this.checked === true) { removeArr.push($(this).attr('id').split('-')[1]); }
    });

    var deleteCount = 0;

    $('.deleteCheck').each(function() {
        if(this.checked === true) { deleteCount++; }
    });

    if(deleteCount >= 1) {
        $.confirm({
            title: "Delete Shows",
            text: "You have selected to delete " + deleteCount + " show(s).  Are you sure you wish to continue? All files will be removed from your system.",
            confirmButton: "Yes",
            cancelButton: "Cancel",
            dialogClass: "modal-dialog",
            post: false,
            confirm: function() {
                $('.deleteCheck').each(function() {
                    if(this.checked === true) {
                        deleteArr.push($(this).attr('id').split('-')[1]);
                    }
                });
                if(updateArr.length + refreshArr.length + renameArr.length + subtitleArr.length + deleteArr.length + removeArr.length + metadataArr.length === 0) {
                    return false;
                }
                var url = srRoot + '/manage/massUpdate';
                var params = 'toUpdate='+updateArr.join('|')+'&toRefresh='+refreshArr.join('|')+'&toRename='+renameArr.join('|')+'&toSubtitle='+subtitleArr.join('|')+'&toDelete='+deleteArr.join('|')+'&toRemove='+removeArr.join('|')+'&toMetadata='+metadataArr.join('|');
                $.post(url, params, function() { location.reload(true); });
            }
        });
    }
    if(updateArr.length + refreshArr.length + renameArr.length + subtitleArr.length + deleteArr.length + removeArr.length + metadataArr.length === 0) {
        return false;
    }
    var url = srRoot + '/manage/massUpdate';
    var params = 'toUpdate='+updateArr.join('|')+'&toRefresh='+refreshArr.join('|')+'&toRename='+renameArr.join('|')+'&toSubtitle='+subtitleArr.join('|')+'&toDelete='+deleteArr.join('|')+'&toRemove='+removeArr.join('|')+'&toMetadata='+metadataArr.join('|');
    $.post(url, params, function() { location.reload(true); });
});
