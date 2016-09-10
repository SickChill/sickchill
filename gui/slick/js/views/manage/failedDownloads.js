$(document).ready(function () {

    $("#failedTable:has(tbody tr)").tablesorter({
        widgets: ['zebra'],
        sortList: [[1, 0]],
        headers: {3: {sorter: false}}
    });
    $('#limit').on('change', function () {
        window.location.href = srRoot + '/manage/failedDownloads/?limit=' + $(this).val();
    });

    $('#submitMassRemove').on('click', function () {
        var removeArr = [];

        $('.removeCheck').each(function () {
            if (this.checked === true) {
                removeArr.push($(this).attr('id').split('-')[1]);
            }
        });

        if (removeArr.length === 0) {
            return false;
        }

        $.post(srRoot + '/manage/failedDownloads', 'toRemove=' + removeArr.join('|'), function () {
            location.reload(true);
        });
    });

    if ($('.removeCheck').length) {
        $('.removeCheck').each(function (name) {
            var lastCheck = null;
            $(name).click(function (event) {
                if (!lastCheck || !event.shiftKey) {
                    lastCheck = this;
                    return;
                }

                var check = this;
                var found = 0;

                $(name + ':visible').each(function () {
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
        });
    }

});
