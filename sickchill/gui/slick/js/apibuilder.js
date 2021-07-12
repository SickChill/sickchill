$(document).ready(() => {
    // Perform an API call
    $('[data-action="api-call"]').on('click', function () {
        const parameters = $('[data-command="' + $(this).data('command-name') + '"]');
        const profile = $('#option-profile').is(':checked');
        const targetId = $(this).data('target');
        const timeId = $(this).data('time');
        let url = scRoot + $('#' + $(this).data('base-url')).text();
        const urlId = $(this).data('url');

        $.each(parameters, (index, item) => {
            const name = $(item).attr('name');
            let value = $(item).val();

            if (name !== undefined && value !== undefined && name !== value && value) {
                if ($.isArray(value)) {
                    value = value.join('|');
                }

                url += '&' + name + '=' + value;
            }
        });

        if (profile) {
            url += '&profile=1';
        }

        const requestTime = Date.now();
        $.get(url, (data, textStatus, jqXHR) => {
            const responseTime = Date.now() - requestTime;
            const jsonp = $('#option-jsonp').is(':checked');
            const responseType = jqXHR.getResponseHeader('content-type') || '';
            const target = $(targetId);

            $(timeId).text(responseTime + 'ms');
            $(urlId).text(url + (jsonp ? '&jsonp=foo' : ''));

            if (responseType.slice(0, 6) === 'image/') {
                target.html($('<img/>', {src: url}));
            } else {
                const json = JSON.stringify(data, null, 4);

                if (jsonp) {
                    target.text('foo(' + json + ');');
                } else {
                    target.text(json);
                }
            }

            target.parents('.result-wrapper').removeClass('hidden');
        });
    });

    // Remove the result of an API call
    $('[data-action="clear-result"]').on('click', function () {
        $($(this).data('target')).html('').parents('.result-wrapper').addClass('hidden');
    });

    // Update the list of episodes
    $('[data-action="update-episodes"]').on('change', function () {
        const command = $(this).data('command');
        const select = $('[data-command="' + command + '"][name="episode"]');
        const season = $(this).val();
        const show = $('[data-command="' + command + '"][name="indexerid"]').val();

        if (select !== undefined) {
            select.removeClass('hidden');
            select.find('option:gt(0)').remove();

            for (const episode in episodes[show][season]) { // eslint-disable-line no-undef,guard-for-in
                select.append($('<option>', {
                    value: episodes[show][season][episode], // eslint-disable-line no-undef
                    label: 'Episode ' + episodes[show][season][episode], // eslint-disable-line no-undef
                }));
            }
        }
    });

    // Update the list of seasons
    $('[data-action="update-seasons"]').on('change', function () {
        const command = $(this).data('command');
        const select = $('[data-command="' + command + '"][name="season"]');
        const show = $(this).val();

        if (select !== undefined) {
            select.removeClass('hidden');
            select.find('option:gt(0)').remove();

            for (const season in episodes[show]) { // eslint-disable-line no-undef,guard-for-in
                select.append($('<option>', {
                    value: season,
                    label: (season === 0) ? 'Specials' : 'Season ' + season,
                }));
            }
        }
    });

    // Enable command search
    $.fn.goTo = function () {
        $('html, body').animate({
            scrollTop: $(this).offset().top - $('nav').outerHeight(true) + 'px',
        }, 'fast');
        return this;
    };

    $('#command-search').typeahead({
        source: commands, // eslint-disable-line no-undef
    });
    $('#command-search').on('change', function () {
        const command = $(this).typeahead('getActive');

        if (command) {
            const commandObject = $('[href="#command-' + command.replace('.', '-') + '"]');
            commandObject.click();

            setTimeout(() => {
                commandObject.goTo();
            }, 250);
        }
    });
});
