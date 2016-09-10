$(document).ready(function () {

    $('#config-components').tabs();

    $(".enabler").each(function () {
        if (!$(this).prop('checked')) {
            $('#content_' + $(this).attr('id')).hide();
        }
    });

    $(".enabler").on('click', function () {
        if ($(this).prop('checked')) {
            $('#content_' + $(this).attr('id')).fadeIn("fast", "linear");
        } else {
            $('#content_' + $(this).attr('id')).fadeOut("fast", "linear");
        }
    });

    $(".viewIf").on('click', function () {
        if ($(this).prop('checked')) {
            $('.hide_if_' + $(this).attr('id')).css('display', 'none');
            $('.show_if_' + $(this).attr('id')).fadeIn("fast", "linear");
        } else {
            $('.show_if_' + $(this).attr('id')).css('display', 'none');
            $('.hide_if_' + $(this).attr('id')).fadeIn("fast", "linear");
        }
    });

    $(".datePresets").on('click', function () {
        var def = $('#date_presets').val();
        if ($(this).prop('checked') && '%x' === def) {
            def = '%a, %b %d, %Y';
            $('#date_use_system_default').html('1');
        } else if (!$(this).prop('checked') && '1' === $('#date_use_system_default').html()) {
            def = '%x';
        }

        $('#date_presets').attr('name', 'date_preset_old');
        $('#date_presets').attr('id', 'date_presets_old');

        $('#date_presets_na').attr('name', 'date_preset');
        $('#date_presets_na').attr('id', 'date_presets');

        $('#date_presets_old').attr('name', 'date_preset_na');
        $('#date_presets_old').attr('id', 'date_presets_na');

        if (def) {
            $('#date_presets').val(def);
        }
    });

// bind 'myForm' and provide a simple callback function
    $('#configForm').ajaxForm({
        beforeSubmit: function () {
            $('.config_submitter .config_submitter_refresh').each(function () {
                $(this).attr("disabled", "disabled");
                $(this).after('<span><img src="' + srRoot + '/images/loading16' + themeSpinner + '.gif"> Saving...</span>');
                $(this).hide();
            });
        },
        success: function () {
            setTimeout(function () {
                "use strict";
                configSuccess();
            }, 2000);
        }
    });

    $('#api_key').on('click', function () {
        $('#api_key').select();
    });

    $("#generate_new_apikey").on('click', function () {
        $.get(srRoot + '/config/general/generateApiKey', function (data) {
            if (data.error !== undefined) {
                alert(data.error);
                return;
            }
            $('#api_key').val(data);
        });
    });

    $('#branchCheckout').on('click', function () {
        var url = srRoot + '/home/branchCheckout?branch=' + $("#branchVersion").val();
        var checkDBversion = srRoot + "/home/getDBcompare";
        $.getJSON(checkDBversion, function (data) {
            if (data.status === "success") {
                if (data.message === "equal") {
                    //Checkout Branch
                    window.location.href = url;
                }
                if (data.message === "upgrade") {
                    if (confirm("Changing branch will upgrade your database.\nYou won't be able to downgrade afterward.\nDo you want to continue?")) {
                        //Checkout Branch
                        window.location.href = url;
                    }
                }
                if (data.message === "downgrade") {
                    alert("Can't switch branch as this will result in a database downgrade.");
                }
            }
        });
    });

});
