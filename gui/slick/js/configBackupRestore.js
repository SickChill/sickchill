$(document).ready(function(){
    var loading = '<div id="wrap"><div class="spinner2"></div><div class="item"> Processing...</div></div>';

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