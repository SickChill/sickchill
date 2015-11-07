var srRoot = getMeta('srRoot'),
    themeSpinner = getMeta('themeSpinner'),
    anonURL = getMeta('anonURL'),
    top_image_html = '<img src="' + srRoot + '/images/top.gif" width="31" height="11" alt="Jump to top" />';

$(document).ready(function () {
    $("#config-components").tabs({
        activate: function (event, ui) {
            var lastOpenedPanel = $(this).data("lastOpenedPanel"),
                selected = $(this).tabs('option', 'selected');

            if (!lastOpenedPanel) { lastOpenedPanel = $(ui.oldPanel); }

            if (!$(this).data("topPositionTab")) { $(this).data("topPositionTab", $(ui.newPanel).position().top); }

            //Dont use the builtin fx effects. This will fade in/out both tabs, we dont want that
            //Fadein the new tab yourself
            $(ui.newPanel).hide().fadeIn(0);

            if (lastOpenedPanel) {
                // 1. Show the previous opened tab by removing the jQuery UI class
                // 2. Make the tab temporary position:absolute so the two tabs will overlap
                // 3. Set topposition so they will overlap if you go from tab 1 to tab 0
                // 4. Remove position:absolute after animation
                lastOpenedPanel
                    .toggleClass("ui-tabs-hide")
                    .css("position", "absolute")
                    .css("top", $(this).data("topPositionTab") + "px")
                    .fadeOut(0, function () {
                        $(this)
                            .css("position", "");
                    });
            }

            //Saving the last tab has been opened
            $(this).data("lastOpenedPanel", $(ui.newPanel));
        }
    });

    // hack alert: if we don't have a touchscreen, and we are already hovering the mouse, then click should link instead of toggle
    if ((navigator.maxTouchPoints || 0) < 2) {
        $('.dropdown-toggle').on('click', function(e) {
            var $this = $(this);
            if ($this.attr('aria-expanded') === 'true') {
                window.location.href = $this.attr('href');
            }
        });
    }

    if(metaToBool('sickbeard.FUZZY_DATING')){
        $.timeago.settings.allowFuture = true;
        $.timeago.settings.strings = {
            prefixAgo: null,
            prefixFromNow: 'In ',
            suffixAgo: "ago",
            suffixFromNow: "",
            seconds: "less than a minute",
            minute: "about a minute",
            minutes: "%d minutes",
            hour: "an hour",
            hours: "%d hours",
            day: "a day",
            days: "%d days",
            month: "a month",
            months: "%d months",
            year: "a year",
            years: "%d years",
            wordSeparator: " ",
            numbers: []
        };
        $("[datetime]").timeago();
    }
});
