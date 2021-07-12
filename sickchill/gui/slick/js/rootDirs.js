// Avoid `console` errors in browsers that lack a console.
(function () {
    let method;
    const noop = function () {};
    const methods = [
        'assert',
        'clear',
        'count',
        'debug',
        'dir',
        'dirxml',
        'error',
        'exception',
        'group',
        'groupCollapsed',
        'groupEnd',
        'info',
        'log',
        'markTimeline',
        'profile',
        'profileEnd',
        'table',
        'time',
        'timeEnd',
        'timeStamp',
        'trace',
        'warn',
    ];
    let length = methods.length;
    const console = (window.console = window.console || {}); // eslint-disable-line no-multi-assign

    while (length--) {
        method = methods[length];

        // Only stub undefined methods.
        if (!console[method]) {
            console[method] = noop;
        }
    }
})();

$(document).ready(() => {
    function setDefault(which, force) {
        if (which === undefined || which.length === 0) {
            return;
        }

        if ($('#whichDefaultRootDir').val() === which && force !== true) {
            return;
        }

        console.log('setting default to ' + which);

        // Put an asterisk on the text
        if ($('#' + which).text().charAt(0) !== '*') {
            $('#' + which).text('*' + $('#' + which).text());
        }

        // If there's an existing one then take the asterisk off
        if ($('#whichDefaultRootDir').val() && force !== true) {
            const oldDefault = $('#' + $('#whichDefaultRootDir').val());
            oldDefault.text(oldDefault.text().slice(1));
        }

        $('#whichDefaultRootDir').val(which);
    }

    function syncOptionIDs() {
        // Re-sync option ids
        let i = 0;
        $('#rootDirs option').each(function () {
            $(this).attr('id', 'rd-' + (i++));
        });
    }

    function refreshRootDirs() {
        if ($('#rootDirs').length === 0) {
            return;
        }

        let doDisable = 'true';

        // Re-sync option ids
        syncOptionIDs();

        // If nothing's selected then select the default
        if ($('#rootDirs option:selected').length === 0 && $('#whichDefaultRootDir').val().length > 0) {
            $('#' + $('#whichDefaultRootDir').val()).prop('selected', true);
        }

        // If something's selected then we have some behavior to figure out
        if ($('#rootDirs option:selected').length > 0) {
            doDisable = '';
        }

        // Update the elements
        $('#deleteRootDir').prop('disabled', doDisable);
        $('#defaultRootDir').prop('disabled', doDisable);
        $('#editRootDir').prop('disabled', doDisable);

        let logString = '';
        let dirString = '';
        if ($('#whichDefaultRootDir').val().length >= 4) {
            dirString = $('#whichDefaultRootDir').val().slice(3);
        }

        $('#rootDirs option').each(function () {
            logString += $(this).val() + '=' + $(this).text() + '->' + $(this).attr('id') + '\n';
            if (dirString.length > 0) {
                dirString += '|' + $(this).val();
            }
        });
        logString += 'def: ' + $('#whichDefaultRootDir').val();
        console.log(logString);

        $('#rootDirText').val(dirString);
        $('#rootDirText').change();
        console.log('rootDirText: ' + $('#rootDirText').val());
    }

    function addRootDir(path) {
        if (path.length === 0) {
            return;
        }

        // Check if it's the first one
        let isDefault = false;
        if ($('#whichDefaultRootDir').val().length === 0) {
            isDefault = true;
        }

        $('#rootDirs').append('<option value="' + path + '">' + path + '</option>');

        syncOptionIDs();

        if (isDefault) {
            setDefault($('#rootDirs option').attr('id'));
        }

        refreshRootDirs();
        $.get(scRoot + '/config/general/saveRootDirs', {rootDirString: $('#rootDirText').val()});
    }

    function editRootDir(path) {
        if (path.length === 0) {
            return;
        }

        // As long as something is selected
        if ($('#rootDirs option:selected').length > 0) {
            // Update the selected one with the provided path
            if ($('#rootDirs option:selected').attr('id') === $('#whichDefaultRootDir').val()) {
                $('#rootDirs option:selected').text('*' + path);
            } else {
                $('#rootDirs option:selected').text(path);
            }

            $('#rootDirs option:selected').val(path);
        }

        refreshRootDirs();
        $.get(scRoot + '/config/general/saveRootDirs', {
            rootDirString: $('#rootDirText').val(),
        });
    }

    $('#addRootDir').on('click', function () {
        $(this).nFileBrowser(addRootDir);
    });
    $('#editRootDir').on('click', function () {
        $(this).nFileBrowser(editRootDir, {
            initialDir: $('#rootDirs option:selected').val(),
        });
    });

    $('#deleteRootDir').on('click', () => {
        if ($('#rootDirs option:selected').length > 0) {
            const toDelete = $('#rootDirs option:selected');
            const newDefault = (toDelete.attr('id') === $('#whichDefaultRootDir').val());
            const deletedNumber = $('#rootDirs option:selected').attr('id').slice(3);

            toDelete.remove();
            syncOptionIDs();

            if (newDefault) {
                console.log('new default when deleting');

                // We deleted the default so this isn't valid anymore
                $('#whichDefaultRootDir').val('');

                // If we're deleting the default and there are options left then pick a new default
                if ($('#rootDirs option').length > 0) {
                    setDefault($('#rootDirs option').attr('id'));
                }
            } else if ($('#whichDefaultRootDir').val().length > 0) {
                const oldDefaultNumber = $('#whichDefaultRootDir').val().slice(3);
                if (oldDefaultNumber > deletedNumber) {
                    $('#whichDefaultRootDir').val('rd-' + (oldDefaultNumber - 1));
                }
            }
        }

        refreshRootDirs();
        $.get(scRoot + '/config/general/saveRootDirs', {
            rootDirString: $('#rootDirText').val(),
        });
    });

    $('#defaultRootDir').on('click', () => {
        if ($('#rootDirs option:selected').length > 0) {
            setDefault($('#rootDirs option:selected').attr('id'));
        }

        refreshRootDirs();
        $.get(scRoot + '/config/general/saveRootDirs', {
            rootDirString: $('#rootDirText').val(),
        });
    });
    $('#rootDirs').click(refreshRootDirs);

    // Set up buttons on page load
    syncOptionIDs();
    setDefault($('#whichDefaultRootDir').val(), true);
    refreshRootDirs();
});
