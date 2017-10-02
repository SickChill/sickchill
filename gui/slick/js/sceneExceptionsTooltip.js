$(function() {
    $('.title a').each(function() {
        const match = $(this).parent().attr('id').match(/^scene_exception_(\d+)$/);
        $(this).qtip({
            content: {
                text: _('Loading...'),
                ajax: {
                    url: srRoot + '/home/sceneExceptions',
                    type: 'GET',
                    data: {
                        show: match[1]
                    },
                    success: function(data) {
                        this.set('content.text', data);
                    }
                }
            },
            show: {
                solo: true
            },
            position: {
                viewport: $(window),
                my: 'bottom center',
                at: 'top center',
                adjust: {
                    y: 10,
                    x: 0
                }
            },
            style: {
                tip: {
                    corner: true,
                    method: 'polygon'
                },
                classes: 'qtip-rounded qtip-shadow ui-tooltip-sb'
            }
        });
    });
});
