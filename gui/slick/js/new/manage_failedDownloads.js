$(document).ready(function(){
    $("#failedTable:has(tbody tr)").tablesorter({
        widgets: ['zebra'],
        sortList: [[0,0]],
        headers: { 3: { sorter: false } }
    });
    $('#limit').change(function(){
        window.location.href = srRoot + '/manage/failedDownloads/?limit='+$(this).val();;
    });
});
