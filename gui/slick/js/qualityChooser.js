$(document).ready(function() {
    function setFromPresets (preset) {
        if (parseInt(preset) === 0) {
            $('#customQuality').show();
            return;
        } else {
            $('#customQuality').hide();
        }

        $('#anyQualities option').each(function() {
            var result = preset & $(this).val(); // jshint ignore:line
            if (result > 0) {
                $(this).attr('selected', 'selected');
            } else {
                $(this).attr('selected', false);
            }
        });

        $('#bestQualities option').each(function() {
            var result = preset & ($(this).val() << 16); // jshint ignore:line
            if (result > 0) {
                $(this).attr('selected', 'selected');
            } else {
                $(this).attr('selected', false);
            }
        });

        return;
    }

    $('#qualityPreset').on('change', function() {
        setFromPresets($('#qualityPreset :selected').val());
    });

    setFromPresets($('#qualityPreset :selected').val());
});
