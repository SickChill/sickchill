/**
 * Fuzzy Moment - convert an absolute date text into a fuzzy moment
 *
 * containerClass string The class name of dom element to convert (default: 'fuzzydate')
 * dateHasTime boolean Whether containerClass contains a time (default: false)
 * dateFormat string The python token date formatting
 * timeFormat string The python token time formatting
 * trimZero Whether to trim leading "0"s (default : false)
 * dtGlue string To insert between the output of date and time (default: '<br />')
 * dtInline Bool Whether to output date inline or use more than one line
 */
 function fuzzyMoment(fmConfig) {

    var containerClass = (/undefined/i.test(typeof(fmConfig)) || /undefined/i.test(typeof(fmConfig.containerClass)) ? '.fuzzydate' : fmConfig.containerClass),
        dateWithTime = (/undefined/i.test(typeof(fmConfig)) || /undefined/i.test(typeof(fmConfig.dateHasTime)) ? false : !!fmConfig.dateHasTime),
        dateFormat = (/undefined/i.test(typeof(fmConfig)) || /undefined/i.test(typeof(fmConfig.dateFormat)) ? '' : fmConfig.dateFormat),
        timeFormat = (/undefined/i.test(typeof(fmConfig)) || /undefined/i.test(typeof(fmConfig.timeFormat)) ? '' : fmConfig.timeFormat),
        trimZero = (/undefined/i.test(typeof(fmConfig)) || /undefined/i.test(typeof(fmConfig.trimZero)) ? false : !!fmConfig.trimZero),
        dtGlue = (/undefined/i.test(typeof(fmConfig)) || /undefined/i.test(typeof(fmConfig.dtGlue)) ? '<br />' : fmConfig.dtGlue),
        dtInline = (/undefined/i.test(typeof(fmConfig)) || /undefined/i.test(typeof(fmConfig.dtInline)) ? false : fmConfig.dtInline),

        jd = (function (str) {
            var token_map = ['a', 'ddd', 'A', 'dddd', 'b', 'MMM', 'B', 'MMMM', 'd', 'DD', 'm', 'MM', 'y', 'YY', 'Y', 'YYYY', 'x', 'L',
                             'H', 'HH', 'I', 'hh', 'M', 'mm', 'S', 'ss', 'p', 'A'],
                result = '';

            for (var i = 0; i < str.length; i++)
                if (/[aAbBdmyYxHIMSp]/.test(str[i])) {
                    for (var t = 0; t < token_map.length; t = t + 2)
                        if (str[i] == token_map[t]) {
                            result += token_map[t + 1];
                            break;
                        }
                } else if ('%' != str[i])
                    result += str[i];

            return result;
        }),
        dateToken = jd(dateFormat),
        timeToken = jd(timeFormat),

        addQTip = (function() {
            $(this).css('cursor', 'help');
            $(this).qtip({
                show: {
                    solo: true
                },
                position: {
                    viewport: $(window),
                    my: 'left center',
                    adjust: {
                        y: -10,
                        x: 2
                    }
                },
                style: {
                    tip: {
                        corner: true,
                        method: 'polygon'
                    },
                    classes: 'qtip-rounded qtip-dark qtip-shadow ui-tooltip-sb'
                }
            });
        });

    if (trimZero) {
        timeToken = timeToken.replace(/hh/g, 'h');
        timeToken = timeToken.replace(/HH/g, 'H');
        dateToken = dateToken.replace(/\bDD\b/g, 'D');
    }

    $(containerClass).each(function() {
        var input = $(this).text(),
            dateA = '[<span class="fd">',
            dtSeparator = ' ',
            timeA = '</span>]', timeB = '[' + timeA;

        if (dateWithTime) {
            var timeMeta = input.match(/^.{6,}?([,\s]+)(\d{1,2}).(?:\d{2,2})(?:.(\d{2,2}))?(?:\s([ap]m))?$/im);
            if (null != timeMeta) {
                dtSeparator = (! /undefined/i.test(typeof(timeMeta[1])) ? timeMeta[1] : dtSeparator);
                // adjust timeToken to num digits of input hours
                timeToken = (! /undefined/i.test(typeof(timeMeta[2])) && 1 == timeMeta[2].length ? timeToken.replace(/hh/ig, 'h') : timeToken);
                // adjust timeToken to use seconds if input has them
                timeToken = (! /undefined/i.test(typeof(timeMeta[3])) && 2 == timeMeta[3].length ? timeToken : timeToken.replace(/.ss/, ''));
                // adjust timeToken to am/pm or AM/PM if input has it
                timeToken = (! /undefined/i.test(typeof(timeMeta[4])) && 2 == timeMeta[4].length ? timeToken.replace(/A$/, (/[ap]m/.test(timeMeta[4]) ? 'a' : 'A')) : timeToken);
            }
            timeA = '</span>' + dtGlue + '<span class="ft">]' + timeToken + '[' + timeA;
            timeB = '[</span>' + dtGlue + '<span class="ft">]' + timeToken + timeB;
        }

        var inputTokens = dateToken + dtSeparator + (dateWithTime ?  timeToken : 'HH:mm:ss');

        if (! moment(input + (dateWithTime ? '' : dtSeparator + '00:00:00'), inputTokens).isValid())
            return;

        moment.lang('en', {
            calendar: {
                lastDay:dateA + 'Yesterday' + timeA, sameDay:dateA + 'Today' + timeA, nextDay:dateA + 'Tomorrow' + timeA,
                lastWeek:dateA + 'last] ddd' + timeB, nextWeek:dateA + 'on] ddd' + timeB,
                sameElse:dateA + ']ddd, MMM D YYYY[' + timeA
            },
            relativeTime: {
                future:'in %s', past:'%s ago', s:'seconds', m:'a minute', mm:'%d minutes', h:'an hour', hh:'%d hours',
                d:'a day', dd:'%d days', M:'a month', MM:'%d months', y:'a year', yy:'%d years'
            }
        });

        var airdatetime = moment(input + (dateWithTime ? '' : dtSeparator + '00:00:00'), inputTokens),
            airdate = airdatetime.clone().hour(0).minute(0).second(0).millisecond(0),
            today = moment({}),
            day = Math.abs(airdate.diff(today, 'days')),
            week = Math.abs(weekdiff = airdate.diff(today, 'week')), isPast = weekdiff < 0,
            titleThis = false, qTipTime = false,
            result = (0 == week ? airdatetime.calendar() : '');

        if (/\bOn\b/i.test(result)) {
           var fuzzer = false, weekday = today.day();
            if (3 == weekday)
                fuzzer = (5 <= day);
            else if (4 == weekday || 5 == weekday)
                fuzzer = (4 <= day);
            else
                fuzzer = (6 == day);
            if (fuzzer)
                result = result.replace(/\bOn\b/i, 'Next');

        } else if (! /\b((yester|to)day\b|tomo|last\b)/i.test(result)) {
            if (14 > day)
                result = airdate.from(today) + (dateWithTime ? dtGlue + airdatetime.format(timeToken) : '');
            else if (4 > week) {
                result = (isPast ? '' : 'in ') + (1 == week ? 'a' : week) + ' week' + (1 == week ? '' : 's') + (isPast ? ' ago' : '');
                qTipTime = true;
            } else {
                result = airdate.from(today);
                qTipTime = true;
                var month = airdate.diff(today, 'month');
                if (1 == parseInt(airdate.year() - today.year()))
                    result += (dtInline ? ' ' : '<br />') + '(Next Year)';
            }
            titleThis = true;
        }

        var n = false; // disable for prod
        $(this).html(result);
        if (dateWithTime && /(yester|to)day/i.test(result))
            $(this).find('.fd').attr('title',(n?'1) ':'') + moment.duration(airdatetime.diff(moment(),'seconds'),'seconds').humanize(true)).each(addQTip);
        else if (dateWithTime)
            $(this).find('.fd').attr('title',(n?'2) ':'') + airdate.from(today)).each(addQTip);
        else if (! /today/i.test(result))
            $(this).find('.fd').attr('title',(n?'3) ':'') + airdate.from(today)).each(addQTip);
        else
            titleThis = false;

        if (titleThis)
            if (dateWithTime && qTipTime)
                $(this).attr('title',(n?'4) ':'') + airdatetime.format(inputTokens)).each(addQTip);
            else
                $(this).attr('title',(n?'5) ':'') + airdate.format(dateToken)).each(addQTip);
        else
            if (dateWithTime && qTipTime)
                $(this).find('.ft').attr('title',(n?'6) ':'') + airdatetime.format(inputTokens)).each(addQTip);
            else
                $(this).find('.ft').attr('title',(n?'7) ':'') + airdate.format(dateToken)).each(addQTip);
    });
}
