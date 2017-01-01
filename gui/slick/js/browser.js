;(function ($) {
    'use strict';

    $.Browser = {
        defaults: {
            title:             'Choose Directory',
            url:               srRoot + '/browser/',
            autocompleteURL:   srRoot + '/browser/complete',
            includeFiles:      0,
            showBrowseButton:  true
        }
    };

    var fileBrowserDialog, currentBrowserPath, currentRequest = null;

    function browse(path, endpoint, includeFiles) {
        if (currentBrowserPath === path) {
            return;
        }

        currentBrowserPath = path;

        if (currentRequest) {
            currentRequest.abort();
        }

        fileBrowserDialog.dialog('option', 'dialogClass', 'browserDialog busy');

        currentRequest = $.getJSON(endpoint, { path: path, includeFiles: includeFiles }, function (data) {
            fileBrowserDialog.empty();
            var firstVal = data[0];
            var i = 0;
            var list, link = null;
            data = $.grep(data, function () {
                return i++ !== 0;
            });

            $('<input type="text" class="form-control input-sm">')
                .val(firstVal.currentPath)
                .on('keypress', function (e) {
                    if (e.which === 13) {
                        browse(e.target.value, endpoint, includeFiles);
                    }
                })
                .appendTo(fileBrowserDialog)
                .fileBrowser({showBrowseButton: false})
                .on('autocompleteselect', function (e, ui) {
                    browse(ui.item.value, endpoint, includeFiles);
                });

            list = $('<ul>').appendTo(fileBrowserDialog);
            $.each(data, function (i, entry) {
                link = $('<a href="javascript:void(0)">').on('click', function () {
                    if (entry.isFile) {
                        currentBrowserPath = entry.path;
                        $('.browserDialog .ui-button:contains("Ok")').click();
                    } else {
                        browse(entry.path, endpoint, includeFiles);
                    }
                }).text(entry.name);
                if (entry.isFile) {
                    link.prepend('<span class="ui-icon ui-icon-blank"></span>');
                } else {
                    link.prepend('<span class="ui-icon ui-icon-folder-collapsed"></span>')
                        .on('mouseenter', function () { $('span', this).addClass('ui-icon-folder-open'); })
                        .on('mouseleave', function () { $('span', this).removeClass('ui-icon-folder-open'); });
                }
                link.appendTo(list);
            });
            $('a', list).wrap('<li class="ui-state-default ui-corner-all">');
            fileBrowserDialog.dialog('option', 'dialogClass', 'browserDialog');
        });
    }

    $.fn.nFileBrowser = function (callback, options) {
        options = $.extend({}, $.Browser.defaults, options);

        // make a fileBrowserDialog object if one doesn't exist already
        if (!fileBrowserDialog) {
            // set up the jquery dialog
            fileBrowserDialog = $('<div class="fileBrowserDialog" style="display:none"></div>').appendTo('body').dialog({
                dialogClass: 'browserDialog',
                title:       options.title,
                position:    { my: 'center top', at: 'center top+60', of: window },
                minWidth:    Math.min($(document).width() - 80, 650),
                height:      Math.min($(document).height() - 80, $(window).height() - 80),
                maxHeight:   Math.min($(document).height() - 80, $(window).height() - 80),
                maxWidth:    $(document).width() - 80,
                modal:       true,
                autoOpen:    false
            });
        } else {
            // The title may change, even if fileBrowserDialog already exists
            fileBrowserDialog.dialog('option', 'title', options.title);
        }

        fileBrowserDialog.dialog('option', 'buttons', [{
            text: 'Ok',
            'class': 'btn',
            click: function () {
                // store the browsed path to the associated text field
                callback($('.fileBrowserField').val(), options);
                $(this).dialog('close');
            }
        }, {
            text: 'Cancel',
            'class': 'btn',
            click: function () {
                $(this).dialog('close');
            }
        }]);

        // set up the browser and launch the dialog
        var initialDir = '';
        if (options.initialDir) {
            initialDir = options.initialDir;
        }

        browse(initialDir, options.url, options.includeFiles);
        fileBrowserDialog.dialog('open');

        return false;
    };

    $.fn.fileBrowser = function (options) {
        options = $.extend({}, $.Browser.defaults, options);
        // text field used for the result
        options.field = $(this);

        if (options.field.autocomplete && options.autocompleteURL) {
            var query = '';
            options.field.autocomplete({
                position: { my : 'top', at: 'bottom', collision: 'flipfit' },
                source: function (request, response) {
                    //keep track of user submitted search term
                    query = $.ui.autocomplete.escapeRegex(request.term, options.includeFiles);
                    $.ajax({
                        url: options.autocompleteURL,
                        data: request,
                        dataType: 'json',
                        success: function (data) {
                            //implement a startsWith filter for the results
                            var matcher = new RegExp('^' + query, 'i');
                            var a = $.grep(data, function (item) {
                                return matcher.test(item);
                            });
                            response(a);
                        }
                    });
                },
                open: function () {
                    $('.ui-autocomplete li.ui-menu-item a').removeClass('ui-corner-all');
                }
            }).data('ui-autocomplete')._renderItem = function (ul, item) {
                //highlight the matched search term from the item -- note that this is global and will match anywhere
                var resultItem = item.label;
                var x = new RegExp('(?![^&;]+;)(?!<[^<>]*)(' + query + ')(?![^<>]*>)(?![^&;]+;)', 'gi');
                resultItem = resultItem.replace(x, function (fullMatch) {
                    return '<b>' + fullMatch + '</b>';
                });
                return $('<li></li>')
                    .data('ui-autocomplete-item', item)
                    .append('<a class="nowrap">' + resultItem + '</a>')
                    .appendTo(ul);
            };
        }

        var path, callback, ls = false;
        // if the text field is empty and we're given a key then populate it with the last browsed value from localStorage
        try { ls = !!(localStorage.getItem); } catch (e) {}
        if (ls && options.key) {
            path = localStorage['fileBrowser-' + options.key];
        }
        if (options.key && options.field.val().length === 0 && path) {
            options.field.val(path);
        }

        callback = function (path, options) {

            path = $('.fileBrowserField').val();
            // store the browsed path to the associated text field
            options.field.val(path);

            // use a localStorage to remember for next time -- no ie6/7
            if (ls && options.key) {
                localStorage['fileBrowser-' + options.key] = path;
            }
        };

        options.field.addClass('fileBrowserField');
        if (options.showBrowseButton) {
            // append the browse button and give it a click behaviour
            options.field.after(
                $('<input type="button" value="Browse&hellip;" class="btn btn-inline fileBrowser">').on('click', function () {
                    var initialDir = options.field.val() || (options.key && path) || '';
                    var optionsWithInitialDir = $.extend({}, options, {initialDir: initialDir});
                    $(this).nFileBrowser(callback, optionsWithInitialDir);
                    return false;
                })
            );
        }
        return options.field;
    };
})(jQuery);
