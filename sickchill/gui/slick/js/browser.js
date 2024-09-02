(function ($) {
    $.Browser = {
        defaults: {
            title: _('Choose Directory'),
            url: scRoot + '/browser/',
            autocompleteURL: scRoot + '/browser/complete',
            includeFiles: 0,
            fileTypes: [], // File extensions to include, 'images' is an alias for image types
            showBrowseButton: true,
        },
    };

    let fileBrowserDialog = null;
    let currentBrowserPath = null;
    let currentRequest = null;

    function browse(path, endpoint, includeFiles, fileTypes) {
        if (currentBrowserPath === path) {
            return;
        }

        currentBrowserPath = path;

        if (currentRequest) {
            currentRequest.abort();
        }

        fileBrowserDialog.dialog('option', 'dialogClass', 'browserDialog busy');

        currentRequest = $.getJSON(endpoint, {
            path,
            includeFiles,
            fileTypes: fileTypes.join(','),
        }, data => {
            fileBrowserDialog.empty();
            let list = null;
            let link = null;

            // Log data to debug
            console.log('Received data:', data);

            const preData = $.grep(data, (value, index) => index !== 0);
            // Separate folders and files
            const folders = preData.filter(item => item.type === 'folder');
            const files = preData.filter(item => item.type !== 'folder');

            // Sort folders and files alphabetically
            folders.sort((a, b) => a.name.localeCompare(b.name));
            files.sort((a, b) => a.name.localeCompare(b.name));

            // Concatenate sorted folders and files
            const innerData = folders.concat(files);

            const inputContainer = $('<div class="fileBrowserFieldContainer"></div>');

            $('<input type="text" class="form-control input-sm">').val(currentBrowserPath).on('keypress', event => {
                if (event.key === 'Enter') {
                    browse(event.target.value, endpoint, includeFiles, fileTypes);
                }
            }).appendTo(inputContainer.appendTo(fileBrowserDialog)).fileBrowser({
                showBrowseButton: false,
            }).on('autocompleteselect', (event, ui) => {
                browse(ui.item.value, endpoint, includeFiles, fileTypes);
            });

            const listContainer = $('<div class="ui-dialog-scrollable-child">');
            list = $('<ul>').appendTo(listContainer.appendTo(fileBrowserDialog));
            $.each(innerData, (i, entry) => {
                /**
                 * @param entry
                 * @param entry.isFile
                 * @param entry.isImage
                 * @param entry.isAllowed
                 */
                // noinspection OverlyComplexBooleanExpressionJS
                if (entry.isFile && fileTypes) {
                    const isAllowed = (entry.isAllowed || (fileTypes.includes('images') && entry.isImage));
                    if (!isAllowed) {
                        return true;
                    }
                }

                link = $('<a href="javascript:void(0)">').on('click', () => {
                    if (entry.isFile) {
                        currentBrowserPath = entry.path;
                        $('.browserDialog .ui-button:contains("Ok")').click();
                    } else {
                        browse(entry.path, endpoint, includeFiles, fileTypes);
                    }
                }).text(entry.name);
                if (entry.isImage) {
                    link.prepend('<span class="ui-icon ui-icon-image"></span>');
                } else if (entry.isFile) {
                    link.prepend('<span class="ui-icon ui-icon-document"></span>');
                } else {
                    link.prepend('<span class="ui-icon ui-icon-folder-collapsed"></span>').on('mouseenter', function () {
                        $('span', this).addClass('ui-icon-folder-open');
                    }).on('mouseleave', function () {
                        $('span', this).removeClass('ui-icon-folder-open');
                    });
                }

                link.appendTo(list);
            });
            $('a', list).wrap('<li class="ui-state-default ui-corner-all">');
            fileBrowserDialog.dialog('option', 'dialogClass', 'browserDialog');

            const scrollableHeight = fileBrowserDialog.height() - inputContainer.outerHeight();

            listContainer.height(scrollableHeight).css('maxHeight', scrollableHeight);
        });
    }

    $.fn.nFileBrowser = function (callback, options) {
        const newOptions = $.extend({}, $.Browser.defaults, options);

        // Make a fileBrowserDialog object if one doesn't exist already
        if (fileBrowserDialog) {
            // The title may change, even if fileBrowserDialog already exists
            fileBrowserDialog.dialog('option', 'title', newOptions.title);
        } else {
            const margin = 80;
            // Set up the jquery dialog
            fileBrowserDialog = $('<div class="fileBrowserDialog"></div>').appendTo('body').dialog({
                dialogClass: 'browserDialog',
                classes: {
                    'ui-dialog': 'ui-dialog-scrollable-by-child',
                },
                title: newOptions.title,
                position: {my: 'center top', at: 'center top+' + margin, of: window},
                minWidth: Math.min($(document).width() - margin, $(window).width() - margin),
                height: Math.min($(document).height() - margin, $(window).height() - margin),
                maxHeight: Math.min($(document).height() - margin, $(window).height() - margin),
                maxWidth: Math.min($(document).width() - margin, $(window).width() - margin),
                modal: true,
                autoOpen: false,
            });
        }

        fileBrowserDialog.dialog('option', 'buttons', [{
            text: 'Ok',
            class: 'btn',
            click() {
                // Store the browsed path to the associated text field
                callback(newOptions.includeFiles ? $(this).find('.fileBrowserField').val() : currentBrowserPath, newOptions);
                $(this).dialog('close');
            },
        }, {
            text: 'Cancel',
            class: 'btn',
            click() {
                $(this).dialog('close');
            },
        }]);

        // Set up the browser and launch the dialog
        browse(newOptions.initialDirectory || '', newOptions.url, newOptions.includeFiles, newOptions.fileTypes);
        fileBrowserDialog.dialog('open');

        return false;
    };

    $.fn.fileBrowser = function (options) {
        const newOptions = $.extend({}, $.Browser.defaults, options);
        // Text field used for the result
        newOptions.field = $(this);

        if (newOptions.field.autocomplete && newOptions.autocompleteURL) {
            let query = '';
            newOptions.field.autocomplete({
                position: {my: 'top', at: 'bottom', collision: 'flipfit'},
                source(request, response) {
                    // Keep track of user submitted search term
                    query = $.ui.autocomplete.escapeRegex(request.term, newOptions.includeFiles);
                    $.ajax({
                        url: newOptions.autocompleteURL,
                        data: request,
                        dataType: 'json',
                        success(data) {
                            // Implement a startsWith filter for the results
                            const matcher = new RegExp('^' + query, 'i');
                            const match = $.grep(data, item => matcher.test(item));
                            response(match);
                        },
                    });
                },
                open() {
                    $('.ui-autocomplete li.ui-menu-item a').removeClass('ui-corner-all');
                },
            }).data('ui-autocomplete')._renderItem = function (ul, item) {
                // Highlight the matched search term from the item -- note that this is global and will match anywhere
                let resultItem = item.label;
                const matcher = new RegExp('(?![^&;]+;)(?!<[^<>]*)(' + query + ')(?![^<>]*>)(?![^&;]+;)', 'gi');
                resultItem = resultItem.replace(matcher, fullMatch => '<b>' + fullMatch + '</b>');
                return $('<li></li>').data('ui-autocomplete-item', item).append('<a class="nowrap">' + resultItem + '</a>').appendTo(ul);
            };
        }

        let path = false;
        let callback = false;
        let hasLocalStorage = false;
        // If the text field is empty, and we're given a key then populate it with the last browsed value from localStorage
        try {
            hasLocalStorage = Boolean(localStorage.getItem);
        } catch {
            console.log('no local storage permissions');
        }

        if (hasLocalStorage && newOptions.key) {
            path = localStorage['fileBrowser-' + newOptions.key];
        }

        if (newOptions.key && newOptions.field.val().length === 0 && path) {
            newOptions.field.val(path);
        }

        callback = function (path, newOptions) {
            newOptions.field.val(path);

            // Use a localStorage to remember for next time -- no ie6/7
            if (hasLocalStorage && newOptions.key) {
                localStorage['fileBrowser-' + newOptions.key] = path;
            }
        };

        newOptions.field.addClass('fileBrowserField');
        if (newOptions.showBrowseButton) {
            // Append the browse button and give it a click behaviour
            newOptions.field.after(
                $('<input type="button" value="Browse&hellip;" class="btn btn-inline fileBrowser">').on('click', function () {
                    const optionsWithInitialDirectory = $.extend({}, newOptions, {initialDirectory: newOptions.field.val() || (newOptions.key && path) || ''});
                    $(this).nFileBrowser(callback, optionsWithInitialDirectory);

                    return false;
                }),
            );
        }

        return newOptions.field;
    };
})(jQuery);
