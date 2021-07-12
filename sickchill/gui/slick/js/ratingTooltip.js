$(() => {
    $('.imdbstars').qtip({
        content: {
            text() {
                // Retrieve content from custom attribute of the $('.selector') elements.
                return $(this).data('qtip-content');
            },
        },
        show: {
            solo: true,
        },
        position: {
            viewport: $(window),
            my: 'right center',
            at: 'center left',
            adjust: {
                y: 0,
                x: -6,
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
