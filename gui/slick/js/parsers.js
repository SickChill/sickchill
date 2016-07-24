$.tablesorter.addParser({
    id: 'loadingNames',
    is: function() {
        return false;
    },
    format: function(s) {
        if (0 === s.indexOf('Loading...')) {
            return s.replace('Loading...', '000');
        } else {
            return (metaToBool('sickbeard.SORT_ARTICLE') ? (s || '') : (s || '').replace(/^(The|A|An)\s/i,''));
        }
    },
    type: 'text'
});
$.tablesorter.addParser({
    id: 'quality',
    is: function() {
        return false;
    },
    format: function(s) {
        var replacements = {
            'custom': 11,
            'bluray': 10, // Custom: Only bluray
            'hd1080p': 9,
            '1080p': 8, // Custom: Only 1080p
            'hdtv': 7, // Custom: 1080p and 720p (only HDTV)
            'web-dl': 6, // Custom: 1080p and 720p (only WEB-DL)
            'hd720p': 5,
            '720p': 4, // Custom: Only 720p
            'hd': 3,
            'sd': 2,
            'any': 1,
            'best': 0
        };
        return replacements[s.toLowerCase()];
    },
    type: 'numeric'
});
$.tablesorter.addParser({
    id: 'realISODate',
    is: function() {
        return false;
    },
    format: function(s) {
        return new Date(s).getTime();
    },
    type: 'numeric'
});

$.tablesorter.addParser({
    id: 'cDate',
    is: function() {
        return false;
    },
    format: function(s) {
        return s;
    },
    type: 'numeric'
});
$.tablesorter.addParser({
    id: 'eps',
    is: function() {
        return false;
    },
    format: function(s) {
        var match = s.match(/^(.*)/);

        if (match === null || match[1] === "?") { return -10; }

        var nums = match[1].split(" / ");
        if (nums[0].indexOf("+") !== -1) {
            var numParts = nums[0].split("+");
            nums[0] = numParts[0];
        }

        nums[0] = parseInt(nums[0]);
        nums[1] = parseInt(nums[1]);

        if (nums[0] === 0) { return nums[1]; }
        var finalNum = parseInt((getMeta('max_download_count'))*nums[0]/nums[1]);
        var pct = Math.round((nums[0]/nums[1])*100) / 1000;
        if (finalNum > 0) { finalNum += nums[0]; }

        return finalNum + pct;
    },
    type: 'numeric'
});
