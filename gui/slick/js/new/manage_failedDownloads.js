$(document).ready(function(){
    $("#failedTable:has(tbody tr)").tablesorter({
        widgets: ['zebra'],
        sortList: [[0,0]],
        headers: { 3: { sorter: false } }
    });
    $('#limit').change(function(){
        url = srRoot + '/manage/failedDownloads/?limit='+$(this).val();
        window.location.href = url;
    });
});
