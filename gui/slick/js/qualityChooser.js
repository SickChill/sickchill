$(document).ready(function() {
    function setFromPresets (preset) {
        if (parseInt(preset) === 0) {
            $('#customQuality').show();
            return;
        } else {
            $('#customQuality').hide();
        }

        $('#anyQualities').find('option').each(function() {
            var result = preset & $(this).val(); // jshint ignore:line
            $(this).attr('selected', result > 0 ? 'selected' : false);
        });

        $('#bestQualities').find('option').each(function() {
            var result = preset & ($(this).val() << 16); // jshint ignore:line
            $(this).attr('selected', result > 0 ? 'selected' : false);
        });
    }

    var qualityPresets = $('#qualityPreset');
    qualityPresets.on('change', function() {
        setFromPresets(qualityPresets.find(':selected').val());
    });

    setFromPresets(qualityPresets.find(':selected').val());
});
