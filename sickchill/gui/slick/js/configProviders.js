$(document).ready(function () {
    $.fn.showHideProviders = function () {
        $('.providerDiv').each(function () {
            const providerName = $(this).attr('id');
            const selectedProvider = $('#editAProvider :selected').val();

            if (selectedProvider + 'Div' === providerName) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    };

    const ifExists = function (loopThroughArray, searchFor) {
        let found = false;

        for (const rootObject of loopThroughArray) {
            if (rootObject.name === searchFor) {
                found = true;
            }

            console.log(rootObject.name + ' while searching for: ' + searchFor);
        }

        return found;
    };

    /**
     * Gets categories for the provided newznab provider.
     * @param {String} isDefault
     * @param {Array} selectedProvider
     * @return no return data. Function updateNewznabCaps() is run at callback
     */
    $.fn.getCategories = function (isDefault, selectedProvider) {
        const name = selectedProvider[0];
        const url = selectedProvider[1];
        const key = selectedProvider[2];

        if (!name || !url || !key) {
            return;
        }

        const parameters = {url, name, key};

        $('.updating_categories').wrapInner('<span><img src="' + scRoot + '/images/loading16' + themeSpinner + '.gif"> Updating Categories ...</span>');
        const jqxhr = $.getJSON(scRoot + '/config/providers/getNewznabCategories', parameters, function (data) {
            $(this).updateNewznabCaps(data, selectedProvider);
            console.debug(data.tv_categories);
        });
        jqxhr.always(() => {
            $('.updating_categories').empty();
        });
    };

    const newznabProviders = [];
    const torrentRssProviders = [];

    const newznabProvidersCapabilities = [];

    $.fn.addProvider = function (id, name, url, key, cat, isDefault) { // eslint-disable-line max-params
        url = $.trim(url);
        if (!url) {
            return;
        }

        if (!/^https?:\/\//i.test(url)) {
            url = 'http://' + url;
        }

        if (url.match('/$') === null) {
            url += '/';
        }

        newznabProviders[id] = [isDefault, [name, url, key, cat]];

        $('#editANewznabProvider').addOption(id, name);
        $(this).populateNewznabSection();

        if ($('#provider_order_list > #' + id).length === 0) {
            const providerOrderList = $('#provider_order_list');
            providerOrderList.append('<li class="ui-state-default" id="' + id + '"> <input type="checkbox" id="enable_' + id + '" class="provider_enabler" CHECKED> <a href="' + anonURL + url + '" class="imgLink" target="_new"><img src="' + scRoot + '/images/providers/newznab.png" alt="' + name + '" width="16" height="16"></a> ' + name + '</li>');
            providerOrderList.sortable('refresh');
        }

        $(this).makeNewznabProviderString();
    };

    $.fn.addTorrentRssProvider = function (id, name, url, cookies, titleTAG) { // eslint-disable-line max-params
        torrentRssProviders[id] = [name, url, cookies, titleTAG];

        $('#editATorrentRssProvider').addOption(id, name);
        $(this).populateTorrentRssSection();

        if ($('#provider_order_list > #' + id).length === 0) {
            const providerOrderList = $('#provider_order_list');
            providerOrderList.append('<li class="ui-state-default" id="' + id + '"> <input type="checkbox" id="enable_' + id + '" class="provider_enabler" CHECKED> <a href="' + anonURL + url + '" class="imgLink" target="_new"><img src="' + scRoot + '/images/providers/torrentrss.png" alt="' + name + '" width="16" height="16"></a> ' + name + '</li>');
            providerOrderList.sortable('refresh');
        }

        $(this).makeTorrentRssProviderString();
    };

    $.fn.updateProvider = function (id, url, key, cat) {
        newznabProviders[id][1][1] = url;
        newznabProviders[id][1][2] = key;
        newznabProviders[id][1][3] = cat;
        $(this).populateNewznabSection();
        $(this).makeNewznabProviderString();
    };

    $.fn.deleteProvider = function (id) {
        $('#editANewznabProvider').removeOption(id);
        delete newznabProviders[id];
        $(this).populateNewznabSection();
        $('li').remove('#' + id);
        $(this).makeNewznabProviderString();
    };

    $.fn.updateTorrentRssProvider = function (id, url, cookies, titleTAG) {
        torrentRssProviders[id][1] = url;
        torrentRssProviders[id][2] = cookies;
        torrentRssProviders[id][3] = titleTAG;
        $(this).populateTorrentRssSection();
        $(this).makeTorrentRssProviderString();
    };

    $.fn.deleteTorrentRssProvider = function (id) {
        $('#editATorrentRssProvider').removeOption(id);
        delete torrentRssProviders[id];
        $(this).populateTorrentRssSection();
        $('li').remove('#' + id);
        $(this).makeTorrentRssProviderString();
    };

    $.fn.populateNewznabSection = function () {
        const selectedProvider = $('#editANewznabProvider :selected').val();
        let data = '';
        let isDefault = '';
        let rrcat = '';

        if (selectedProvider === 'addNewznab') {
            data = ['', '', ''];
            isDefault = 0;
            $('#newznab_add_div').show();
            $('#newznab_update_div').hide();
            $('#newznab_cat').attr('disabled', 'disabled');
            $('#newznab_cap').attr('disabled', 'disabled');
            $('#newznab_cat_update').attr('disabled', 'disabled');
            $('#newznabcapdiv').hide();

            $('#newznab_cat option').each(function () {
                $(this).remove();
            });

            $('#newznab_cap option').each(function () {
                $(this).remove();
            });
        } else {
            data = newznabProviders[selectedProvider][1];
            isDefault = newznabProviders[selectedProvider][0];
            $('#newznab_add_div').hide();
            $('#newznab_update_div').show();
            $('#newznab_cat').removeAttr('disabled');
            $('#newznab_cap').removeAttr('disabled');
            $('#newznab_cat_update').removeAttr('disabled');
            $('#newznabcapdiv').show();
        }

        $('#newznab_name').val(data[0]);
        $('#newznab_url').val(data[1]);
        $('#newznab_key').val(data[2]);

        // Check if not already array
        rrcat = typeof data[3] === 'string' ? data[3].split(',') : data[3];

        // Update the category select box (on the right)
        const newCatOptions = [];
        if (rrcat) {
            for (const cat of rrcat) {
                if (cat !== '') {
                    newCatOptions.push({text: cat, value: cat});
                }
            }

            $('#newznab_cat').replaceOptions(newCatOptions);
        }

        if (selectedProvider === 'addNewznab') {
            $('#newznab_name').removeAttr('disabled');
            $('#newznab_url').removeAttr('disabled');
        } else {
            $('#newznab_name').attr('disabled', 'disabled');

            if (isDefault) {
                $('#newznab_url').attr('disabled', 'disabled');
                $('#newznab_delete').attr('disabled', 'disabled');
            } else {
                $('#newznab_url').removeAttr('disabled');
                $('#newznab_delete').removeAttr('disabled');
            }

            // Get Categories Capabilities
            if (data[0] && data[1] && data[2] && !ifExists(newznabProvidersCapabilities, data[0])) {
                $(this).getCategories(isDefault, data);
            }

            $(this).updateNewznabCaps(null, data);
        }
    };

    /**
     * Updates the Global constant array newznabProvidersCapabilities with a combination of newznab prov name
     * and category capabilities. Return
     * @param {Array} newzNabCaps, is the returned object with newznabprovider Name and Capabilities.
     * @param {Array} selectedProvider
     * @return no return data. The multiselect input $("#newznab_cap") is updated, as a result.
     */
    $.fn.updateNewznabCaps = function (newzNabCaps, selectedProvider) {
        if (newzNabCaps && !ifExists(newznabProvidersCapabilities, selectedProvider[0])) {
            newznabProvidersCapabilities.push({name: selectedProvider[0], categories: newzNabCaps.tv_categories});
        }

        // Loop through the array and if currently selected newznab provider name matches one in the array, use it to
        // update the capabilities select box (on the left).
        $('#newznab_cap').empty();
        if (!selectedProvider[0]) {
            return;
        }

        for (const newzNabCap of newznabProvidersCapabilities) {
            if (newzNabCap.name && newzNabCap.name === selectedProvider[0] && Array.isArray(newzNabCap.categories)) {
                const newCapOptions = [];
                for (const categorySet of newzNabCap.categories) {
                    if (categorySet.id && categorySet.name) {
                        newCapOptions.push({value: categorySet.id, text: categorySet.name + '(' + categorySet.id + ')'});
                    }
                }

                $('#newznab_cap').replaceOptions(newCapOptions);
            }
        }
    };

    $.fn.makeNewznabProviderString = function () {
        const provStrings = [];
        for (const id in newznabProviders) {
            if (Object.prototype.hasOwnProperty.call(newznabProviders, id)) {
                provStrings.push(newznabProviders[id][1].join('|'));
            }
        }

        $('#newznab_string').val(provStrings.join('!!!'));
    };

    $.fn.populateTorrentRssSection = function () {
        const selectedProvider = $('#editATorrentRssProvider :selected').val();
        let data = '';

        if (selectedProvider === 'addTorrentRss') {
            data = ['', '', '', 'title'];
            $('#torrentrss_add_div').show();
            $('#torrentrss_update_div').hide();
        } else {
            data = torrentRssProviders[selectedProvider];
            $('#torrentrss_add_div').hide();
            $('#torrentrss_update_div').show();
        }

        $('#torrentrss_name').val(data[0]);
        $('#torrentrss_url').val(data[1]);
        $('#torrentrss_cookies').val(data[2]);
        $('#torrentrss_titleTAG').val(data[3]);

        if (selectedProvider === 'addTorrentRss') {
            $('#torrentrss_name').removeAttr('disabled');
            $('#torrentrss_url').removeAttr('disabled');
            $('#torrentrss_cookies').removeAttr('disabled');
            $('#torrentrss_titleTAG').removeAttr('disabled');
        } else {
            $('#torrentrss_name').attr('disabled', 'disabled');
            $('#torrentrss_url').removeAttr('disabled');
            $('#torrentrss_cookies').removeAttr('disabled');
            $('#torrentrss_titleTAG').removeAttr('disabled');
            $('#torrentrss_delete').removeAttr('disabled');
        }
    };

    $.fn.makeTorrentRssProviderString = function () {
        const provStrings = [];
        for (const id in torrentRssProviders) {
            if (Object.prototype.hasOwnProperty.call(torrentRssProviders, id)) {
                provStrings.push(torrentRssProviders[id].join('|'));
            }
        }

        $('#torrentrss_string').val(provStrings.join('!!!'));
    };

    $.fn.refreshProviderList = function () {
        const idArray = $('#provider_order_list').sortable('toArray');
        const finalArray = [];
        $.each(idArray, (key, value) => {
            const checked = $('#enable_' + value).is(':checked') ? '1' : '0';
            finalArray.push(value + ':' + checked);
        });

        $('#provider_order').val(finalArray.join(' '));
        $(this).refreshEditAProvider();
    };

    $.fn.refreshEditAProvider = function () {
        $('#editAProvider').empty();

        const idArray = $('#provider_order_list').sortable('toArray');
        const finalArray = [];
        $.each(idArray, (key, value) => {
            if ($('#enable_' + value).prop('checked')) {
                finalArray.push(value);
            }
        });

        if (finalArray.length > 0) {
            $('<select>').prop('id', 'editAProvider').addClass('form-control input-sm').appendTo('#provider-list');
            for (const id in finalArray) {
                if (Object.prototype.hasOwnProperty.call(finalArray, id)) {
                    const provider = finalArray[id];
                    $('#editAProvider').append($('<option>').prop('value', provider).text($.trim($('#' + provider).text()).replace(/\s\*$/, '').replace(/\s\*\*$/, '')));
                }
            }
        } else {
            document.querySelectorAll('.component-desc')[0].innerHTML = 'No providers available to configure.';
        }

        $(this).showHideProviders();
    };

    $(this).on('change', '.newznab_key', function () {
        let providerId = $(this).attr('id');
        providerId = providerId.slice(0, Math.max(0, providerId.length - '_hash'.length));

        const url = $('#' + providerId + '_url').val();
        const cat = $('#' + providerId + '_cat').val();
        const key = $(this).val();

        $(this).updateProvider(providerId, url, key, cat);
    });

    $('#newznab_key,#newznab_url').on('change', function () {
        const selectedProvider = $('#editANewznabProvider :selected').val();

        if (selectedProvider === 'addNewznab') {
            return;
        }

        const url = $('#newznab_url').val();
        const key = $('#newznab_key').val();

        const cat = $('#newznab_cat option').map((i, opt) => $(opt).text()).toArray().join(',');

        $(this).updateProvider(selectedProvider, url, key, cat);
    });

    $('#torrentrss_url,#torrentrss_cookies,#torrentrss_titleTAG').on('change', function () {
        const selectedProvider = $('#editATorrentRssProvider :selected').val();

        if (selectedProvider === 'addTorrentRss') {
            return;
        }

        const url = $('#torrentrss_url').val();
        const cookies = $('#torrentrss_cookies').val();
        const titleTAG = $('#torrentrss_titleTAG').val();

        $(this).updateTorrentRssProvider(selectedProvider, url, cookies, titleTAG);
    });

    $('body').on('change', '#editAProvider', function () {
        $(this).showHideProviders();
    });

    $('#editANewznabProvider').on('change', function () {
        $(this).populateNewznabSection();
    });

    $('#editATorrentRssProvider').on('change', function () {
        $(this).populateTorrentRssSection();
    });

    $('.provider_enabler').on('change', function () {
        $(this).refreshProviderList();
    });

    $('#newznab_cat_update').on('click', function () {
        console.debug('Clicked Button');

        // Maybe check if there is anything selected?
        $('#newznab_cat option').each(function () {
            $(this).remove();
        });

        const newOptions = [];

        // When the update botton is clicked, loop through the capabilities list
        // and copy the selected category id's to the category list on the right.
        $('#newznab_cap option:selected').each(function () {
            const selectedCat = $(this).val();
            console.debug(selectedCat);
            newOptions.push({text: selectedCat, value: selectedCat});
        });

        $('#newznab_cat').replaceOptions(newOptions);

        const selectedProvider = $('#editANewznabProvider :selected').val();
        if (selectedProvider === 'addNewznab') {
            return;
        }

        const url = $('#newznab_url').val();
        const key = $('#newznab_key').val();

        const cat = $('#newznab_cat option').map((i, opt) => $(opt).text()).toArray().join(',');

        $('#newznab_cat option:not([value])').remove();

        $(this).updateProvider(selectedProvider, url, key, cat);
    });

    $('#newznab_add').on('click', () => {
        const name = $.trim($('#newznab_name').val());
        const url = $.trim($('#newznab_url').val());
        const key = $.trim($('#newznab_key').val());
        // Var cat = $.trim($('#newznab_cat').val());

        const cat = $.trim($('#newznab_cat option').map((i, opt) => $(opt).text()).toArray().join(','));

        if (!name || !url || !key) {
            return;
        }

        const parameters = {name};

        // Send to the form with ajax, get a return value
        $.getJSON(scRoot + '/config/providers/canAddNewznabProvider', parameters, function (data) {
            if (data.error !== undefined) {
                alert(data.error); // eslint-disable-line no-alert
                return;
            }

            $(this).addProvider(data.success, name, url, key, cat, 0);
        });
    });

    $('.newznab_delete').on('click', function () {
        const selectedProvider = $('#editANewznabProvider :selected').val();
        $(this).deleteProvider(selectedProvider);
    });

    $('#torrentrss_add').on('click', () => {
        const name = $('#torrentrss_name').val();
        const url = $('#torrentrss_url').val();
        const cookies = $('#torrentrss_cookies').val();
        const titleTAG = $('#torrentrss_titleTAG').val();
        const parameters = {name, url, cookies, titleTAG};

        // Send to the form with ajax, get a return value
        $.getJSON(scRoot + '/config/providers/canAddTorrentRssProvider', parameters, function (data) {
            if (data.error !== undefined) {
                alert(data.error); // eslint-disable-line no-alert
                return;
            }

            $(this).addTorrentRssProvider(data.success, name, url, cookies, titleTAG);
            $(this).refreshEditAProvider();
        });
    });

    $('.torrentrss_delete').on('click', function () {
        $(this).deleteTorrentRssProvider($('#editATorrentRssProvider :selected').val());
        $(this).refreshEditAProvider();
    });

    $(this).on('change', '[class=\'providerDiv_tip\'] input', function () {
        $('div .providerDiv [name=' + $(this).attr('name') + ']').replaceWith($(this).clone());
        $('div .providerDiv [newznab_name=' + $(this).attr('id') + ']').replaceWith($(this).clone());
    });

    $(this).on('change', '[class=\'providerDiv_tip\'] select', function () {
        $(this).find('option').each(function () {
            if ($(this).is(':selected')) {
                $(this).prop('defaultSelected', true);
            } else {
                $(this).prop('defaultSelected', false);
            }
        });
        $('div .providerDiv [name=' + $(this).attr('name') + ']').empty().replaceWith($(this).clone());
    });

    $.fn.makeTorrentOptionString = function (providerId) {
        const seedRatio = $('.providerDiv_tip #' + providerId + '_seed_ratio').prop('value');
        const seedTime = $('.providerDiv_tip #' + providerId + '_seed_time').prop('value');
        const processMet = $('.providerDiv_tip #' + providerId + '_process_method').prop('value');
        const optionString = $('.providerDiv_tip #' + providerId + '_option_string');

        optionString.val([seedRatio, seedTime, processMet].join('|'));
    };

    $(this).on('change', '.seed_option', function () {
        const providerId = $(this).attr('id').split('_')[0];
        $(this).makeTorrentOptionString(providerId);
    });

    $.fn.replaceOptions = function (options) {
        function addOptions(providerObject, options) {
            providerObject.empty();
            $.each(options, (index, option) => {
                const $option = $('<option></option>').attr('value', option.value).text(option.text);
                providerObject.append($option);
            });
        }

        addOptions(this, options);
    };

    $(this).showHideProviders();

    $('#provider_order_list').sortable({
        placeholder: 'ui-state-highlight',
        update() {
            $(this).refreshProviderList();
        },
    });

    $('#provider_order_list').disableSelection();

    if ($('#editANewznabProvider').length > 0) {
        $(this).populateNewznabSection();
    }
});
