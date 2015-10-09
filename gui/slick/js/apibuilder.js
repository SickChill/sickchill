$(document).ready(function() {
    // Perform an API call
    $('[data-action=api-call]').on('click', function() {
        var parameters = $('[data-command=' + $(this).data('command-name') + ']');
        var profile = $('#option-profile').is(':checked');
        var targetId = $(this).data('target');
        var timeId = $(this).data('time');
        var url = srRoot + $('#' + $(this).data('base-url')).text();
        var urlId = $(this).data('url');

        $.each(parameters, function (index, item) {
            var name = $(item).attr('name');
            var value = $(item).val();

            if(name !== undefined && value !== undefined && name != value && value) {
                if($.isArray(value)) {
                    value = value.join('|');
                }

                url += '&' + name + '=' + value;
            }
        });

        if(profile) url += '&profile=1';

        var requestTime = new Date().getTime();
        $.get(url, function (data, textStatus, jqXHR) {
            var responseTime = new Date().getTime() - requestTime;
            var jsonp = $('#option-jsonp').is(':checked');
            var responseType = jqXHR.getResponseHeader('content-type') || '';
            var target = $(targetId);

            $(timeId).text(responseTime + 'ms');
            $(urlId).text(url + (jsonp ? '&jsonp=foo' : ''));

            if(responseType.slice(0, 6) == 'image/') {
                target.html($('<img/>').attr('src', url));
            } else {
                var json = JSON.stringify(data, null, 4);

                if(jsonp) {
                    target.text('foo(' + json + ');');
                } else {
                    target.text(json);
                }
            }

            target.parents('.result-wrapper').removeClass('hidden');
        });
    });

    // Remove the result of an API call
    $('[data-action=clear-result]').on('click', function() {
        $($(this).data('target')).html('').parents('.result-wrapper').addClass('hidden');
    });

    // Update the list of episodes
    $('[data-action=update-episodes').on('change', function() {
        var command = $(this).data('command');
        var select = $('[data-command=' + command + '][name=episode]');
        var season = $(this).val();
        var show = $('[data-command=' + command + '][name=indexerid]').val();

        if(select !== undefined) {
            select.removeClass('hidden');
            select.find('option:gt(0)').remove();

            for(var episode in episodes[show][season]) {
                select.append($('<option>', {
                    value: episodes[show][season][episode],
                    label: 'Episode ' + episodes[show][season][episode],
                }));
            }
        }
    });

    // Update the list of seasons
    $('[data-action=update-seasons').on('change', function() {
        var command = $(this).data('command');
        var select = $('[data-command=' + command + '][name=season]');
        var show = $(this).val();

        if(select !== undefined) {
            select.removeClass('hidden');
            select.find('option:gt(0)').remove();

            for(var season in episodes[show]) {
                select.append($('<option>', {
                    value: season,
                    label: (season === 0) ? 'Specials' : 'Season ' + season,
                }));
            }
        }
    });

    // Enable command search
    $('#command-search').typeahead({
        source: commands,
    });
    $('#command-search').on('change', function() {
        var command = $(this).typeahead('getActive');

        if(command) {
            var commandId = command.replace('.', '-');
            $('[href=#command-' + commandId + ']').click();
        }
    });
});
