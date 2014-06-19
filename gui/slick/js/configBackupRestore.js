$(document).ready(function(){
    var loading = '<img src="' + sbRoot + '/images/loading16.gif" height="16" width="16" />';

    $('#Backup').click(function() {
        $("#Backup").attr("disabled", true);
        $('#Backup-result').html(loading);
        var backupDir = $("#backupDir").val();
        $.get(sbRoot + "/config/backup", {'backupDir': backupDir})
            .done(function (data) {
                $('#Backup-result').html(data);
                $("#Backup").attr("disabled", false);
            });
    });
    $('#Restore').click(function() {
        $("#Restore").attr("disabled", true);
        $('#Restore-result').html(loading);
        var backupFile = $("#backupFile").val();
        $.get(sbRoot + "/config/restore", {'backupFile': backupFile})
            .done(function (data) {
                $('#Restore-result').html(data);
                $("#Restore").attr("disabled", false);
            });
    });
});