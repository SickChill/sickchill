$(document).load(function(){
    $('#backupDir').fileBrowser({ title: 'Select backup folder to save to', key: 'backupPath' });
    $('#backupFile').fileBrowser({ title: 'Select backup files to restore', key: 'backupFile', includeFiles: 1 });
    $('#config-components').tabs();
});
