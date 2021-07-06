$(() => {
    $('.plotInfo').each(function () {
        const match = $(this).attr('id').match(/^plot_info_(\d+)_(\d+)_(\d+)$/);
        $(this).qtip({
            content: {
                text: _('Loading...'),
                ajax: {
                    url: scRoot + '/home/plotDetails',
                    type: 'GET',
                    data: {
                        show: match[1],
                        episode: match[3],
                        season: match[2],
                    },
                    success(data) {
                        this.set('content.text', data);
                    },
                },
            },
            show: {
                solo: true,
            },
            position: {
                viewport: $(window),
                my: 'left center',
                adjust: {
                    y: -10,
                    x: 2,
                },
            },
            style: {
                tip: {
                    corner: true,
                    method: 'polygon',
                },
                classes: 'qtip-rounded qtip-shadow ui-tooltip-sb',
            },
        });
    });
});
