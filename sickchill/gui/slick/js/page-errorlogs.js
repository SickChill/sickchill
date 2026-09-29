window.SICKCHILL ||= {};
window.SICKCHILL.errorlogs = {
    init() {},
    index() {},
    viewlogs() {
        $('#min_level,#log_filter,#log_search').on('keyup change', __.debounce(() => {
            if ($('#log_search').val().length > 0) {
                $('#log_filter option[value="<NONE>"]').prop('selected', true);
                $('#min_level option[value=5]').prop('selected', true);
            }

            $('#min_level').prop('disabled', true);
            $('#log_filter').prop('disabled', true);
            document.body.style.cursor = 'wait';
            const url = scRoot + '/errorlogs/viewlog/';
            const postData = 'min_level=' + $('select[name=min_level]').val() + '&log_filter=' + $('select[name=log_filter]').val() + '&log_search=' + $('#log_search').val();
            $.post(url, postData, data => {
                history.pushState('data', '', url);
                $('pre').html($(data).find('pre').html());
                $('#min_level').prop('disabled', false);
                $('#log_filter').prop('disabled', false);
                document.body.style.cursor = 'default';
            });
        }, 500));

        function updateLogData() {
            if ($('#log_update_toggle').data('state') === 'active') {
                const postData = 'min_level=' + $('select[name=min_level]').val() + '&log_filter=' + $('select[name=log_filter]').val() + '&log_search=' + $('#log_search').val();
                const url = scRoot + '/errorlogs/viewlog/';
                $.post(url, postData, data => {
                    $('pre').html($(data).find('pre').html());
                });
            }

            setTimeout(updateLogData, 500);
        }

        updateLogData();

        $('#log_update_toggle').on('click', function () {
            const wasActive = $(this).data('state') === 'active'; // State before clicking
            $(this).data('state', wasActive ? 'paused' : 'active');
            $(this).find('i').toggleClass('fa-pause fa-play');
            $(this).find('span').text(wasActive ? _('Resume') : _('Pause'));
            $(this).attr('title', wasActive ? _('Resume updating the log on this page.') : _('Pause updating the log on this page.'));
            return false;
        });
    },
};
