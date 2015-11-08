$(document).ready(function(){
    $.fn.showHideServices = function() {
        $('.serviceDiv').each(function(){
            var serviceName = $(this).attr('id');
            var selectedService = $('#editAService :selected').val();

            if (selectedService+'Div' === serviceName){
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    };

    $.fn.addService = function (id, name, url, key, isDefault, showService) {
        if (url.match('/$') === null) { url = url + '/'; }

        if ($('#service_order_list > #'+id).length === 0 && showService !== false) {
            var toAdd = '<li class="ui-state-default" id="' + id + '"> <input type="checkbox" id="enable_' + id + '" class="service_enabler" CHECKED> <a href="' + anonURL + url + '" class="imgLink" target="_new"><img src="' + srRoot + '/images/services/newznab.gif" alt="' + name + '" width="16" height="16"></a> ' + name + '</li>';

            $('#service_order_list').append(toAdd);
            $('#service_order_list').sortable("refresh");
        }
    };

    $.fn.deleteService = function (id) {
        $('#service_order_list > #'+id).remove();
    };

    $.fn.refreshServiceList = function() {
        var idArr = $("#service_order_list").sortable('toArray');
        var finalArr = [];
        $.each(idArr, function(key, val) {
            var checked = + $('#enable_'+val).prop('checked') ? '1' : '0';
            finalArr.push(val + ':' + checked);
        });
        $("#service_order").val(finalArr.join(' '));
    };

    $('#editAService').change(function(){
        $(this).showHideServices();
    });

    $('.service_enabler').on('click', function(){
        $(this).refreshServiceList();
    });

    // initialization stuff
    $(this).showHideServices();

    $("#service_order_list").sortable({
        placeholder: 'ui-state-highlight',
        update: function () {
            $(this).refreshServiceList();
        }
    });

    $("#service_order_list").disableSelection();
});
