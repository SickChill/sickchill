function getMeta(pythonVariable) {
    return $('meta[data-var="' + pythonVariable + '"]').data('content');
}

const scRoot = getMeta('scRoot');
const scDefaultPage = getMeta('scDefaultPage');
const themeSpinner = getMeta('themeSpinner');
const anonURL = getMeta('anonURL');
const topImageHtml = '<img src="' + scRoot + '/images/top.gif" width="31" height="11" alt="Jump to top" />'; // eslint-disable-line no-unused-vars
const loading = '<img src="' + scRoot + '/images/loading16' + themeSpinner + '.gif" alt="loading" height="16" width="16" />';

const scPID = getMeta('scPID');

function configTabHashFromHref(href) {
    if (!href) {
        return '';
    }

    const hashAt = href.lastIndexOf('#');
    return hashAt === -1 ? '' : href.slice(hashAt);
}

function persistConfigTabHash($tabs) {
    if (!$tabs || $tabs.length === 0 || !$tabs.data('ui-tabs')) {
        return;
    }

    const href = $tabs.children('ul').find('li.ui-tabs-active a').attr('href');
    const nextHash = configTabHashFromHref(href);
    if (!nextHash) {
        return;
    }

    if (window.history.replaceState) {
        window.history.replaceState(null, '', window.location.pathname + window.location.search + nextHash);
    } else {
        window.location.hash = nextHash.slice(1);
    }
}

function initConfigComponentTabs() {
    const $tabs = $('#config-components').first();
    if ($tabs.length === 0) {
        return $tabs;
    }

    const {hash} = window.location;
    let active;
    if (hash && hash.length > 1) {
        const $link = $tabs.children('ul').find('a').filter(function () {
            return configTabHashFromHref(this.getAttribute('href') || this.href) === hash;
        });
        if ($link.length > 0) {
            active = $link.parent().index();
        }
    }

    const options = {};
    if (active !== undefined) {
        options.active = active;
    }

    if ($tabs.data('ui-tabs')) {
        if (active !== undefined) {
            $tabs.tabs('option', 'active', active);
        }
    } else {
        $tabs.tabs(options);
    }

    if (!$tabs.data('configTabHash')) {
        $tabs.data('configTabHash', true);
        $tabs.on('tabsactivate', () => {
            persistConfigTabHash($tabs);
        });
    }

    return $tabs;
}

function configSuccess(reload = true) {
    // Restore all save buttons once — do not reload inside .each() (Search Settings has 3 submitters)
    $('.config_submitter, .config_submitter_refresh').each(function () {
        $(this).removeAttr('disabled');
        $(this).next().remove();
        $(this).show();
    });
    $('#email_show').trigger('notify');
    $('#prowl_show').trigger('notify');
    persistConfigTabHash($('#config-components').first());
    if (!reload) {
        return;
    }

    window.location.reload();
}

function hydrateLazyImages() {
    const images = document.querySelectorAll('img[data-src]');
    for (const image of images) {
        if (!image.getAttribute('loading')) {
            image.setAttribute('loading', 'lazy');
        }

        image.setAttribute('src', image.dataset.src);
    }
}

function initProgressBars() {
    $('.progressbar').each(function () {
        const $bar = $(this);
        if ($bar.data('progressbarCss')) {
            return;
        }

        const percentage = Number($bar.data('progress-percentage')) || 0;
        const classToAdd = Math.max(20, percentage - (percentage % 20));
        const $value = $('<div class="progressbar-value"></div>')
            .addClass('progress-' + classToAdd)
            .css('width', percentage + '%');
        $bar.addClass('ui-progressbar ui-widget ui-widget-content ui-corner-all');
        $bar.append($value);
        if ($bar.data('progress-text')) {
            $bar.append('<div class="progressbarText" title="' + ($bar.data('progress-tip') || '') + '">' + $bar.data('progress-text') + '</div>');
        }

        $bar.data('progressbarCss', true);
    });
}

function bindMasonryImageLayout($grid) {
    if (!$grid || $grid.length === 0) {
        return;
    }

    const relayout = __.debounce(() => {
        if ($grid.data('isotope')) {
            $grid.isotope('layout');
        }
    }, 100);

    $grid.find('img').on('load', relayout);
}

function installGettext(data) {
    window.gt = data === undefined ? new Gettext() : new Gettext(data.messages);

    // Shortcut for normal gettext
    window._ = function (string) {
        return gt.gettext(string);
    };

    // Shortcut for plural gettext
    window._n = function (string, pluralString, number) {
        return gt.ngettext(string, pluralString, number);
    };
}

function shouldSkipLocaleFetch(lang) {
    const normalized = (lang || '').toString().trim().toLowerCase().replaceAll('_', '-');
    return !normalized || normalized === 'en' || normalized.startsWith('en-');
}

function metaToBool(pythonVariable) {
    let meta = $('meta[data-var="' + pythonVariable + '"]').data('content');
    if (meta === undefined) {
        console.log(pythonVariable + ' is empty, did you forget to add this to "main.mako"?');
        return meta;
    }

    meta = (Number.isNaN(meta) ? meta.toLowerCase() : meta.toString());
    meta = meta.toLowerCase();

    return !['false', 'none', '0'].includes(meta);
}

function isMeta(pythonVariable, result) {
    const reg = new RegExp(result.length > 1 ? result.join('|') : result);
    return (reg).test($('meta[data-var="' + pythonVariable + '"]').data('content'));
}

function notifyModal(message) {
    $('#site-notification-modal .modal-body').html(message);
    $('#site-notification-modal').modal();
}

function addSiteMessage(level = 'danger', tag = '', message = '') {
    $.post(scRoot + '/ui/set_site_message', {level, tag, message}, siteMessages => {
        const messagesDiv = $('#site-messages');
        if (messagesDiv === undefined) {
            return;
        }

        messagesDiv.empty();
        for (const key in siteMessages) {
            if (Object.hasOwn(siteMessages, key)) {
                messagesDiv.append('<div class="alert alert-' + siteMessages[key].level + ' upgrade-notification hidden-print" id="site-message-' + key + '" role="alert">'
                    + '<span>' + siteMessages[key].message + '</span><span class="glyphicon glyphicon-check site-message-dismiss pull-right" data-id="' + key + '"/>'
                    + '</div>');
            }
        }
    });

    $('#site-messages').on('click', '.site-message-dismiss', function () {
        const messageID = $(this).data('id');
        $('#site-message-' + messageID).hide();
        $.post(scRoot + '/ui/dismiss-site-message', {index: messageID});
    });
}

function shiftReturn(array) {
    // Performs .shift() on array.
    // Returns the new array
    if (array.length <= 1) {
        return [];
    }

    array.shift();
    return array;
}

const __ = _; // Moves `underscore` to __
// Temporary (gets replaced)
window._ = function (string) {
    return string;
};

window.SICKCHILL ||= {};
const {SICKCHILL} = window;
SICKCHILL.common = {
    init() {
        hydrateLazyImages();
        initProgressBars();

        if (metaToBool('settings.SICKCHILL_BACKGROUND')) {
            $.backstretch(scRoot + '/ui/sickchill_background');
            $('.backstretch').css('opacity', getMeta('settings.FANART_BACKGROUND_OPACITY')).fadeIn('500');
        }

        addSiteMessage(); // Show existing messages on ready.

        $.confirm.options = {
            confirmButton: 'Yes',
            cancelButton: 'Cancel',
            dialogClass: 'modal-dialog',
            post: false,
            confirm(event) {
                location.assign(event.context.href);
            },
        };

        $('a.shutdown').confirm({
            title: 'Shutdown',
            text: 'Are you sure you want to shut down SickChill?',
        });

        $('a.restart').confirm({
            title: 'Restart',
            text: 'Are you sure you want to restart SickChill?',
        });

        $('a.removeshow').confirm({
            title: 'Remove Show',
            text: 'Are you sure you want to remove <span class="footerhighlight">' + $('#showtitle').data('showname')
                + '</span> from the database?<br><br>'
                + '<input type="checkbox" id="deleteFiles" name="deleteFiles"/>&nbsp;'
                + '<label for="deleteFiles" class="red-text">Check to delete files as well. IRREVERSIBLE</label>',
            confirm(event) {
                location.assign(event.context.href + ($('#deleteFiles')[0].checked ? '&full=1' : '&full=0'));
            },
        });

        $('a.clearhistory').confirm({
            title: 'Clear History',
            text: 'Are you sure you want to clear all download history?',
        });

        $('a.trimhistory').confirm({
            title: 'Trim History',
            text: 'Are you sure you want to trim all download history older than 30 days?',
        });

        $('a.submiterrors').confirm({
            title: 'Submit Errors',
            text: 'Are you sure you want to submit these errors ?<br><br>'
                + '<span class="red-text">Make sure SickChill is updated and trigger<br>'
                + ' this error with debug enabled before submitting</span>',
        });

        initConfigComponentTabs();
        $('#config-components').first().tabs({
            activate(event, ui) {
                let lastOpenedPanel = $(this).data('lastOpenedPanel');

                lastOpenedPanel ||= $(ui.oldPanel);

                if (!$(this).data('topPositionTab')) {
                    $(this).data('topPositionTab', $(ui.newPanel).position().top);
                }

                // Don't use the builtin fx effects. This will fade in/out both tabs, we don't want that
                // Fadein the new tab yourself
                $(ui.newPanel).hide().fadeIn(0);

                if (lastOpenedPanel) {
                    // 1. Show the previous opened tab by removing the jQuery UI class
                    // 2. Make the tab temporary position:absolute so the two tabs will overlap
                    // 3. Set topposition, so they will overlap if you go from tab 1 to tab 0
                    // 4. Remove position:absolute after animation
                    lastOpenedPanel
                        .toggleClass('ui-tabs-hide')
                        .css('position', 'absolute')
                        .css('top', $(this).data('topPositionTab') + 'px')
                        .fadeOut(0, function () {
                            $(this).css('position', '');
                        });
                }

                // Saving the last tab has been opened
                $(this).data('lastOpenedPanel', $(ui.newPanel));
            },
        });

        // Second click on a hover-open dropdown follows the link on non-touch pointers.
        if ((navigator.maxTouchPoints || 0) < 2) {
            $('.dropdown-toggle').on('click', function () {
                const element = $(this);
                if (element.prop('ariaExpanded') === 'true') {
                    window.location.assign(element.prop('href'));
                }
            });
        }

        if (metaToBool('settings.FUZZY_DATING')) {
            $.timeago.settings.allowFuture = true;
            $.timeago.settings.strings = {
                prefixAgo: null,
                prefixFromNow: 'In ',
                suffixAgo: 'ago',
                suffixFromNow: '',
                seconds: 'less than a minute',
                minute: 'about a minute',
                minutes: '%d minutes',
                hour: 'an hour',
                hours: '%d hours',
                day: 'a day',
                days: '%d days',
                month: 'a month',
                months: '%d months',
                year: 'a year',
                years: '%d years',
                wordSeparator: ' ',
                numbers: [],
            };
            $('[datetime]').timeago();
        }

        $(document.body).on('click', 'a[data-no-redirect]', event => {
            event.preventDefault();
            $.get($(event.currentTarget).prop('href'));
            return false;
        });

        $(document.body).on('change', '.bulkCheck', event => {
            const checkbox = event.currentTarget;
            const childrenClass = '.' + checkbox.id + ':visible';

            $(childrenClass).each(function () {
                this.checked = checkbox.checked;
            });
        });
        $('.enabler').on('change', function () {
            if (this.checked) {
                $('#content_' + $(this).attr('id')).fadeIn('fast', 'linear');
            } else {
                $('#content_' + $(this).attr('id')).fadeOut('fast', 'linear');
            }
        });
    },
    QualityChooser: {
        setFromPresets(preset) {
            if (Number.parseInt(preset, 10) === 0) {
                $('#customQuality').show();
                return;
            }

            $('#customQuality').hide();

            $('#anyQualities').find('option').each(function () {
                const result = preset & $(this).val(); // eslint-disable-line no-bitwise
                $(this).prop('selected', result > 0);
            });

            $('#bestQualities').find('option').each(function () {
                const result = preset & ($(this).val() << 16); // eslint-disable-line no-bitwise
                $(this).prop('selected', result > 0);
            });
        },
        init() {
            const qualityPresets = $('#qualityPreset');

            qualityPresets.on('change', () => {
                this.setFromPresets(qualityPresets.find(':selected').val());
            });

            this.setFromPresets(qualityPresets.find(':selected').val());
        },
    },
    updateBlackWhiteList(showName) {
        $('#pool').children().remove();

        if ($('#anime').is(':checked')) {
            $('#blackwhitelist').show();
            if (showName) {
                $.getJSON(scRoot + '/home/fetch_releasegroups', {
                    show_name: showName, // eslint-disable-line camelcase
                }, data => {
                    if (data.result === 'success') {
                        $.each(data.groups, (i, group) => {
                            const option = $('<option>');
                            option.attr('value', group.name);
                            option.html(group.name + ' | ' + group.rating + ' | ' + group.range);
                            option.appendTo('#pool');
                        });
                    }
                });
            }
        } else {
            $('#blackwhitelist').hide();
        }
    },
};

const UTIL = {
    exec(controller, action) {
        const ns = SICKCHILL;
        action = (action === undefined) ? 'init' : action;

        if (controller !== '' && Object.hasOwn(ns, controller) && typeof ns[controller][action] === 'function') {
            ns[controller][action]();
        }
    },
    init() {
        const {body} = document;
        const {controller} = body.dataset;
        const {action} = body.dataset;

        UTIL.exec('common');
        UTIL.exec(controller);
        UTIL.exec(controller, action);
    },
};

function startSickchillUi() {
    if (!navigator.userAgent.includes('PhantomJS')) {
        $(document).ready(UTIL.init);
    }
}

Object.assign(window, {
    scDefaultPage,
    anonURL,
    loading,
    scPID,
    configSuccess,
    bindMasonryImageLayout,
    installGettext,
    shouldSkipLocaleFetch,
    isMeta,
    notifyModal,
    shiftReturn,
    startSickchillUi,
    initConfigComponentTabs,
    __,
});
