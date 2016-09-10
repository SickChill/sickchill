$(document).ready(function() {

    $('#tableDiv').on('click', '#checkAll', function () {
        var seasCheck = this;
        $('.dirCheck').each(function () {
            this.checked = seasCheck.checked;
        });
    });

    $('#submitShowDirs').on('click', function () {
        var dirArr = [];
        $('.dirCheck').each(function () {
            if (this.checked === true) {
                var show = $(this).attr('id');
                var indexer = $(this).closest('tr').find('select').val();
                dirArr.push(encodeURIComponent(indexer + '|' + show));
            }
        });

        if (dirArr.length === 0) {
            return false;
        }

        var url = srRoot + '/addShows/addExistingShows?promptForSettings=' + ($('#promptForSettings').prop('checked') ? 'on' : 'off') + '&shows_to_add=' + dirArr.join('&shows_to_add=');
        if (url.length < 2083) {
            window.location.href = url;
        } else {
            alert("You've selected too many shows, please uncheck some and try again. [" + url.length + "/2083 characters]");
        }
    });

    function loadContent() {
        var url = '';
        $('.dir_check').each(function (i, w) {
            if ($(w).is(':checked')) {
                if (url.length) {
                    url += '&';
                }
                url += 'rootDir=' + encodeURIComponent($(w).attr('id'));
            }
        });

        $('#tableDiv').html('<img id="searchingAnim" src="' + srRoot + '/images/loading32.gif" height="32" width="32" /> loading folders...');
        $.post(srRoot + '/addShows/massAddTable/', url, function (data) {
            $('#tableDiv').html(data);
            $("#addRootDirTable").tablesorter({
                //sortList: [[1,0]],
                widgets: ['zebra'],
                headers: {
                    0: {sorter: false}
                }
            });
        });
    }

    var lastTxt = '';
    // @TODO this needs a real name, for now this fixes the issue of the page not loading at all,
    //       before I added this I couldn't get the directories to show in the table
    var a = function () {
        if (lastTxt === $('#rootDirText').val()) {
            return false;
        } else {
            lastTxt = $('#rootDirText').val();
        }
        $('#rootDirStaticList').html('');
        $('#rootDirs option').each(function (i, w) {
            $('#rootDirStaticList').append('<li class="ui-state-default ui-corner-all"><input type="checkbox" class="cb dir_check" id="' + $(w).val() + '" checked=checked> <label for="' + $(w).val() + '">' + $(w).val() + '</label></li>');
        });
        loadContent();
    };

    a();

    $('#rootDirText').on('change', a);

    $('#rootDirStaticList').on('click', '.dir_check', loadContent);

    $('#tableDiv').on('click', '.showManage', function (event) {
        event.preventDefault();
        $("#tabs").tabs('option', 'active', 0);
        $('html,body').animate({scrollTop: 0}, 1000);
    });

});
