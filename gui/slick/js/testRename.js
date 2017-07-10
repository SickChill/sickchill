$(document).ready(function() {
    $('.seriesCheck').click(function() {
        const serCheck = this;

        $('.seasonCheck:visible').each(function() {
            this.checked = serCheck.checked;
        });

        $('.epCheck:visible').each(function() {
            this.checked = serCheck.checked;
        });
    });

    $('.seasonCheck').click(function() {
        const seasCheck = this;
        const seasNo = $(seasCheck).attr('id');

        $('.epCheck:visible').each(function() {
            const epParts = $(this).attr('id').split('x');

            if (epParts[0] === seasNo) {
                this.checked = seasCheck.checked;
            }
        });
    });

    $('input[type=submit]').click(function() {
        const epArr = [];

        $('.epCheck').each(function() {
            if (this.checked === true) {
                epArr.push($(this).attr('id'));
            }
        });

        if (epArr.length === 0) {
            return false;
        }
        $.redirect(srRoot + '/home/doRename', {show: $('#showID').attr('value'), eps: epArr.join('|')}, 'POST');
    });
});
