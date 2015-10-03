$.tablesorter.addParser({
    id: 'loadingNames',
    is: function(s) {
        return false;
    },
    format: function(s) {
        if (0 === s.indexOf('Loading...')){
            return s.replace('Loading...', '000');
        } else {
            return (metaToBool('sickbeard.SORT_ARTICLE') ? (s || '') : (s || '').replace(/^(The|A|An)\s/i,''));
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
$.tablesorter.addParser({
    id: 'eps',
    is: function(s) {
        return false;
    },
    format: function(s) {
        match = s.match(/^(.*)/);

        if (match === null || match[1] == "?") return -10;

        var nums = match[1].split(" / ");
        if (nums[0].indexOf("+") != -1) {
            var num_parts = nums[0].split("+");
            nums[0] = num_parts[0];
        }

        nums[0] = parseInt(nums[0]);
        nums[1] = parseInt(nums[1]);

        if (nums[0] === 0) return nums[1];
        var finalNum = parseInt((getMeta('max_download_count'))*nums[0]/nums[1]);
        var pct = Math.round((nums[0]/nums[1])*100) / 1000;
        if (finalNum > 0) finalNum += nums[0];

        return finalNum + pct;
    },
    type: 'numeric'
});
