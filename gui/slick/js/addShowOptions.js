$(document).ready(function () {
    $('#saveDefaultsButton').click(function () {
        var allowedQualArray = [];
        var preferredQualArray = [];
        $('#allowed_qualities option:selected').each(function (i, d) {
            allowedQualArray.push($(d).val());
        });
        $('#preferred_qualities option:selected').each(function (i, d) {
            preferredQualArray.push($(d).val());
        });

        $.get(srRoot + '/config/general/saveAddShowDefaults', {
            'default_ep_status': $('#statusSelect').val(),
            'allowed_qualities': allowedQualArray.join(','),
            'preferred_qualities': preferredQualArray.join(','),
            'default_flatten_folders': $('#flatten_folders').prop('checked'),
            'subtitles': $('#subtitles').prop('checked'),
            'anime': $('#anime').prop('checked'),
            'scene': $('#scene').prop('checked'),
            'default_status_after_add': $('#statusSelectAfter').val(),
        });

        $(this).attr('disabled', true);
        new PNotify({
            title: 'Saved Defaults',
            text: 'Your "add show" defaults have been set to your current selections.',
            shadow: false
        });
    });

    $('#statusSelect, #quality_preset, #flatten_folders, #allowed_qualities, #preferred_qualities, #subtitles, #scene, #anime, #statusSelectAfter').change(function () {
        $('#saveDefaultsButton').attr('disabled', false);
    });

    $('#quality_preset').on('change', function() {
        //fix issue #181 - force re-render to correct the height of the outer div
        $('span.prev').click();
        $('span.next').click();
    });

});
