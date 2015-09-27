$(document).ready(function(){
    var loading = '<img src="' + srRoot + '/images/loading16' + themeSpinner + '.gif" height="16" width="16" />';

    $('#Backup').click(function() {
        $("#Backup").attr("disabled", true);
        $('#Backup-result').html(loading);
        var backupDir = $("#backupDir").val();
        $.get(srRoot + "/config/backuprestore/backup", {'backupDir': backupDir})
            .done(function (data) {
                $('#Backup-result').html(data);
                $("#Backup").attr("disabled", false);
            });
    });
    $('#Restore').click(function() {
        $("#Restore").attr("disabled", true);
        $('#Restore-result').html(loading);
        var backupFile = $("#backupFile").val();
        $.get(srRoot + "/config/backuprestore/restore", {'backupFile': backupFile})
            .done(function (data) {
                $('#Restore-result').html(data);
                $("#Restore").attr("disabled", false);
            });
    });
});
