$(document).ready(() => {
    $('.seriesCheck').on('click', function () {
        const serCheck = this;

        $('.seasonCheck:visible').each(function () {
            this.checked = serCheck.checked;
        });

        $('.epCheck:visible').each(function () {
            this.checked = serCheck.checked;
        });
    });

    $('.seasonCheck').on('click', function () {
        const seasCheck = this;
        const seasNo = $(seasCheck).attr('id');

        $('.epCheck:visible').each(function () {
            const epParts = $(this).attr('id').split('x');

            if (epParts[0] === seasNo) {
                this.checked = seasCheck.checked;
            }
        });
    });

    $('input[type=submit]').on('click', () => {
        const epArray = [];

        $('.epCheck').each(function () {
            if (this.checked === true) {
                epArray.push($(this).attr('id'));
            }
        });

        if (epArray.length === 0) {
            return false;
        }

        $.redirect(scRoot + '/home/doRename', {show: $('#showID').attr('value'), eps: epArray.join('|')}, 'POST');
    });
});
