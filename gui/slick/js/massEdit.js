$(document).ready(function(){
    function findDirIndex(which){
        var dirParts = which.split('_');
        return dirParts[dirParts.length-1];
    }

    function editRootDir(path, options){
        $('#new_root_dir_'+options.whichId).val(path);
        $('#new_root_dir_'+options.whichId).change();
    }

    $('.new_root_dir').change(function(){
        var curIndex = findDirIndex($(this).attr('id'));
        $('#display_new_root_dir_'+curIndex).html('<b>'+$(this).val()+'</b>');
    });

    $('.edit_root_dir').click(function(){
        var curIndex = findDirIndex($(this).attr('id'));
        var initialDir = $("#new_root_dir_"+curIndex).val();
        $(this).nFileBrowser(editRootDir, {initialDir: initialDir, whichId: curIndex});
    });

    $('.delete_root_dir').click(function(){
        var curIndex = findDirIndex($(this).attr('id'));
        $('#new_root_dir_'+curIndex).val(null);
        $('#display_new_root_dir_'+curIndex).html('<b>DELETED</b>');
    });
});
