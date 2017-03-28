$(document).ready(function(){
    $('.seriesCheck').click(function(){
        var serCheck = this;

        $('.seasonCheck:visible').each(function(){
            this.checked = serCheck.checked;
        });

        $('.epCheck:visible').each(function(){
            this.checked = serCheck.checked;
        });
    });

    $('.seasonCheck').click(function(){
        var seasCheck = this;
        var seasNo = $(seasCheck).attr('id');

        $('.epCheck:visible').each(function(){
            var epParts = $(this).attr('id').split('x');

            if (epParts[0] === seasNo) {
                this.checked = seasCheck.checked;
            }
        });
    });

    $('input[type=submit]').click(function(){
        var epArr = [];

        $('.epCheck').each(function() {
            if (this.checked === true) {
                epArr.push($(this).attr('id'));
            }
        });

        if (epArr.length === 0) { return false; }

        var url = srRoot+'/home/doRename?show='+$('#showID').attr('value')+'&eps='+epArr.join('|');
        if(url.length < 2083) {
            window.location.href = url;
        } else {
            alert( _("You've selected too many shows, please uncheck some and try again. [{totalLen}/2083 characters]").replace(/{totalLen}/, url.length) );
        }
    });

});
