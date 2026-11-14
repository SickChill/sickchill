window.SICKCHILL ||= {};
window.SICKCHILL.history = {
    init() {},
    index() {
        $('#historyTable:has(tbody tr)').tablesorter({
            widgets: ['zebra', 'filter'],
            sortList: [[0, 1]],
            textExtraction: (function () {
                if (isMeta('settings.HISTORY_LAYOUT', ['detailed'])) {
                    return {
                        0(node) { // Time
                            return $(node).find('time').attr('datetime');
                        },
                        2(node) { // Provider
                            return ($(node).find('img').attr('alt') || 'unknown').toLowerCase();
                        },
                        4(node) { // Quality
                            return $(node).find('span').text().toLowerCase();
                        },
                    };
                }

                const compactExtract = {
                    0(node) { // Time
                        return $(node).find('time').attr('datetime');
                    },
                    2(node) { // Provider
                        return $(node).find('span').text().toLowerCase();
                    },
                };

                if (isMeta('settings.USE_SUBTITLES', ['True'])) {
                    compactExtract[4] = function (node) { // Subtitles
                        return $(node).find('img').attr('title');
                    };

                    compactExtract[5] = function (node) { // Quality
                        return $(node).find('span').text().toLowerCase();
                    };
                } else {
                    compactExtract[4] = function (node) { // Quality
                        return $(node).find('span').text().toLowerCase();
                    };
                }

                return compactExtract;
            })(),
            headers: (function () {
                if (isMeta('settings.HISTORY_LAYOUT', ['detailed'])) {
                    return {
                        0: {sorter: 'realISODate'},
                        1: {sorter: 'loadingNames'},
                        4: {sorter: 'quality'},
                        5: {sorter: false, filter: false},
                    };
                }

                if (isMeta('settings.USE_SUBTITLES', ['True'])) {
                    return {
                        0: {sorter: 'realISODate'},
                        1: {sorter: 'loadingNames'},
                        4: {sorter: false},
                        5: {sorter: 'quality'},
                        6: {sorter: false, filter: false},
                    };
                }

                return {
                    0: {sorter: 'realISODate'},
                    1: {sorter: 'loadingNames'},
                    4: {sorter: 'quality'},
                    5: {sorter: false, filter: false},
                };
            })(),
        });

        $('#layout').on('change', function () {
            window.location.assign($(this).find('option:selected').val());
        });

        $('#history_limit').on('change', function () {
            window.location.assign(scRoot + '/history/?limit=' + $(this).val());
        });

        $('a.removehistory').on('click', () => {
            const removeArray = [];
            let removeCount = 0;

            $('.removeCheck').each(function () {
                if (this.checked !== true) {
                    return;
                }

                removeArray.push(shiftReturn($(this).attr('id').split('-')));
                removeCount++;
            });

            if (removeCount < 1) {
                return false;
            }

            $.confirm({
                title: 'Remove Logs',
                text: 'You have selected to remove ' + removeCount + ' download history log(s).<br /><br />This cannot be undone.<br />Are you sure you wish to continue?',
                confirm() {
                    $.post(scRoot + '/history/removeHistory', {items: removeArray}, () => {
                        location.reload(true);
                    });
                },
            });

            return false;
        });

        for (const name of ['.removeCheck']) {
            let lastCheck = null;

            $(name).on('click', function (event) {
                if (!lastCheck || !event.shiftKey) {
                    lastCheck = this; // eslint-disable-line unicorn/no-this-assignment
                    return;
                }

                const check = this; // eslint-disable-line unicorn/no-this-assignment
                let found = 0;

                $(name).each(function () {
                    if (found === 1 && !this.disabled) {
                        this.checked = lastCheck.checked;
                    } else if (found === 2) {
                        return false;
                    }

                    if (this === check || this === lastCheck) {
                        found++;
                    }
                });
            });
        }
    },
};
