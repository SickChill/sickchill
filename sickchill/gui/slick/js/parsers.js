$.tablesorter.addParser({
    id: 'loadingNames',
    is() {
        return false;
    },
    format(s) {
        if (s.indexOf(_('Loading...')) === 0) {
            return s.replace(_('Loading...'), '000');
        }

        return latinize(metaToBool('settings.SORT_ARTICLE') ? (s || '') : (s || '').replace(/^(the|a|an)\s/i, '').normalize('NFC'));
    },
    type: 'text',
});
$.tablesorter.addParser({
    id: 'quality',
    is() {
        return false;
    },
    format(s, table, cell) {
        return $(cell).find('span').data('quality');
    },
    type: 'numeric',
});
$.tablesorter.addParser({
    id: 'realISODate',
    is() {
        return false;
    },
    format(s) {
        return new Date(s).getTime();
    },
    type: 'numeric',
});

$.tablesorter.addParser({
    id: 'cDate',
    is() {
        return false;
    },
    format(s) {
        return s;
    },
    type: 'numeric',
});
$.tablesorter.addParser({
    id: 'eps',
    is() {
        return false;
    },
    format(s) {
        const match = s.match(/^(.*)/);

        if (match === null || match[1] === '?') {
            return -10;
        }

        const nums = match[1].split(' / ');
        if (nums[0].includes('+')) {
            const numberParts = nums[0].split('+');
            nums[0] = numberParts[0];
        }

        nums[0] = Number.parseInt(nums[0], 10);
        nums[1] = Number.parseInt(nums[1], 10);

        if (nums[0] === 0) {
            return nums[1];
        }

        let finalNumber = Number.parseInt((getMeta('max_download_count')) * nums[0] / nums[1], 10);
        const pct = Math.round((nums[0] / nums[1]) * 100) / 1000;
        if (finalNumber > 0) {
            finalNumber += nums[0];
        }

        return finalNumber + pct;
    },
    type: 'numeric',
});
