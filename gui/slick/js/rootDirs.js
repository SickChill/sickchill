// Avoid `console` errors in browsers that lack a console.
(function() {
    var method;
    var noop = function noop() {};
    var methods = [
        'assert', 'clear', 'count', 'debug', 'dir', 'dirxml', 'error',
        'exception', 'group', 'groupCollapsed', 'groupEnd', 'info', 'log',
        'markTimeline', 'profile', 'profileEnd', 'table', 'time', 'timeEnd',
        'timeStamp', 'trace', 'warn'
    ];
    var length = methods.length;
    var console = (window.console = window.console || {});

    while (length--) {
        method = methods[length];

        // Only stub undefined methods.
        if (!console[method]) {
            console[method] = noop;
        }
    }
}());

$(document).ready(function() {
    function addRootDir(path) {
        if (!path.length){
            return;
        }

        // check if it's the first one
        var isDefault = false;
        if (!$('#whichDefaultRootDir').val().length){
            isDefault = true;
        }

        $('#rootDirs').append('<option value="'+path+'">'+path+'</option>');

        syncOptionIDs();

        if (isDefault) {
            setDefault($('#rootDirs option').attr('id'));
        }

        refreshRootDirs();
        $.get(srRoot+'/config/general/saveRootDirs', { rootDirString: $('#rootDirText').val() });
    }

    function editRootDir(path) {
        if (!path.length){
            return;
        }

        // as long as something is selected
        if ($("#rootDirs option:selected").length) {

            // update the selected one with the provided path
            if ($("#rootDirs option:selected").attr('id') === $("#whichDefaultRootDir").val()) {
                $("#rootDirs option:selected").text('*'+path);
            } else {
                $("#rootDirs option:selected").text(path);
            }
            $("#rootDirs option:selected").val(path);
        }

        refreshRootDirs();
        $.get(srRoot+'/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
    }

    $('#addRootDir').click(function(){$(this).nFileBrowser(addRootDir);});
    $('#editRootDir').click(function(){$(this).nFileBrowser(editRootDir, {initialDir: $("#rootDirs option:selected").val()});});

    $('#deleteRootDir').click(function() {
        if ($("#rootDirs option:selected").length) {

            var toDelete = $("#rootDirs option:selected");

            var newDefault = (toDelete.attr('id') === $("#whichDefaultRootDir").val());
            var deletedNum = $("#rootDirs option:selected").attr('id').substr(3);

            toDelete.remove();
            syncOptionIDs();

            if (newDefault) {

                console.log('new default when deleting');

                // we deleted the default so this isn't valid anymore
                $("#whichDefaultRootDir").val('');

                // if we're deleting the default and there are options left then pick a new default
                if ($("#rootDirs option").length) {
                    setDefault($('#rootDirs option').attr('id'));
                }

            } else if ($("#whichDefaultRootDir").val().length) {
                var oldDefaultNum = $("#whichDefaultRootDir").val().substr(3);
                if (oldDefaultNum > deletedNum) {
                    $("#whichDefaultRootDir").val('rd-'+(oldDefaultNum-1));
                }
            }

        }
        refreshRootDirs();
        $.get(srRoot+'/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
    });

    $('#defaultRootDir').click(function(){
        if ($("#rootDirs option:selected").length) {
            setDefault($("#rootDirs option:selected").attr('id'));
        }
        refreshRootDirs();
        $.get(srRoot+'/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
    });

    function setDefault(which, force){
        console.log('setting default to '+which);

        if (which !== undefined && !which.length) { return; }

        if ($('#whichDefaultRootDir').val() === which && force !== true) { return; }

        // put an asterisk on the text
        if ($('#'+which).text().charAt(0) !== '*') { $('#'+which).text('*'+$('#'+which).text()); }

        // if there's an existing one then take the asterisk off
        if ($('#whichDefaultRootDir').val() && force !== true) {
            var oldDefault = $('#'+$('#whichDefaultRootDir').val());
            oldDefault.text(oldDefault.text().substring(1));
        }

        $('#whichDefaultRootDir').val(which);
    }

    function syncOptionIDs() {
        // re-sync option ids
        var i = 0;
        $('#rootDirs option').each(function() {
            $(this).attr('id', 'rd-'+(i++));
        });
    }

    function refreshRootDirs() {

        if (!$("#rootDirs").length) { return; }

        var doDisable = 'true';

        // re-sync option ids
        syncOptionIDs();

        // if nothing's selected then select the default
        if (!$("#rootDirs option:selected").length && $('#whichDefaultRootDir').val().length) {
            $('#'+$('#whichDefaultRootDir').val()).prop("selected", true);
        }

        // if something's selected then we have some behavior to figure out
        if ($("#rootDirs option:selected").length) {
            doDisable = '';
        }

        // update the elements
        $('#deleteRootDir').prop('disabled', doDisable);
        $('#defaultRootDir').prop('disabled', doDisable);
        $('#editRootDir').prop('disabled', doDisable);

        var logString = '';
        var dirString = '';
        if ($('#whichDefaultRootDir').val().length >= 4){
            dirString = $('#whichDefaultRootDir').val().substr(3);
        }
        $('#rootDirs option').each(function() {
            logString += $(this).val()+'='+$(this).text()+'->'+$(this).attr('id')+'\n';
            if (dirString.length) {
                dirString += '|' + $(this).val();
            }
        });
        logString += 'def: '+ $('#whichDefaultRootDir').val();
        console.log(logString);

        $('#rootDirText').val(dirString);
        $('#rootDirText').change();
        console.log('rootDirText: '+$('#rootDirText').val());
    }

    $('#rootDirs').click(refreshRootDirs);

    // set up buttons on page load
    syncOptionIDs();
    setDefault($('#whichDefaultRootDir').val(), true);
    refreshRootDirs();
});
