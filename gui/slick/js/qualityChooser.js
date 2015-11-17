$(document).ready(function() {
    function setFromPresets (preset) {
        if (parseInt(preset) === 0) {
            $('#customQuality').show();
            return;
        } else {
            $('#customQuality').hide();
        }

        $('#anyQualities option').each(function() {
            var result = preset & $(this).val(); // @TODO Find out what this does
            if (result > 0) {
                $(this).attr('selected', 'selected');
            } else {
                $(this).attr('selected', false);
            }
        });

        $('#bestQualities option').each(function() {
            var result = preset & ($(this).val() << 16); // @TODO Find out what this does
            if (result > 0) {
                $(this).attr('selected', 'selected');
            } else {
                $(this).attr('selected', false);
            }
        });

        return;
    }

    $('#qualityPreset').change(function() {
        setFromPresets($('#qualityPreset :selected').val());
    });

    setFromPresets($('#qualityPreset :selected').val());
});
