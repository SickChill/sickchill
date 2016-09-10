$(document).ready(function () {

    $('#Backup').on('click', function () {
        $("#Backup").attr("disabled", true);
        $('#Backup-result').html(loading);
        var backupDir = $("#backupDir").val();
        $.get(srRoot + "/config/backuprestore/backup", {'backupDir': backupDir})
            .done(function (data) {
                $('#Backup-result').html(data);
                $("#Backup").attr("disabled", false);
            });
    });
    $('#Restore').on('click', function () {
        $("#Restore").attr("disabled", true);
        $('#Restore-result').html(loading);
        var backupFile = $("#backupFile").val();
        $.get(srRoot + "/config/backuprestore/restore", {'backupFile': backupFile})
            .done(function (data) {
                $('#Restore-result').html(data);
                $("#Restore").attr("disabled", false);
            });
    });

    $('#backupDir').fileBrowser({title: 'Select backup folder to save to', key: 'backupPath'});
    $('#backupFile').fileBrowser({title: 'Select backup files to restore', key: 'backupFile', includeFiles: 1});
    $('#config-components').tabs();

});
