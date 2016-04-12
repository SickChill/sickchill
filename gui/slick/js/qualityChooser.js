$(document).ready(function() {
    function setFromPresets (preset) {
        if (parseInt(preset) === 0) {
            $('#customQuality').show();
            return;
        } else {
            $('#customQuality').hide();
        }

        $('#allowed_qualities option').each(function() {
            var result = preset & $(this).val(); // jshint ignore:line
            if (result > 0) {
                $(this).attr('selected', 'selected');
            } else {
                $(this).attr('selected', false);
            }
        });

        $('#preferred_qualities option').each(function() {
            var result = preset & ($(this).val() << 16); // jshint ignore:line
            if (result > 0) {
                $(this).attr('selected', 'selected');
            } else {
                $(this).attr('selected', false);
            }
        });

        return;
    }

    $('#quality_preset').on('change', function() {
        setFromPresets($('#quality_preset :selected').val());
    });

    setFromPresets($('#quality_preset :selected').val());
});
