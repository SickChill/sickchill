(function ($) {
    'use strict';

    let imageSelectorDialog = null;
    let currentRequest = null;

    function fetchImages() {
        const type = imageSelectorDialog.data('image-type');
        if (currentRequest) {
            currentRequest.abort();
        }

        imageSelectorDialog.dialog('option', 'dialogClass', 'browserDialog busy');

        currentRequest = $.getJSON(scRoot + '/imageSelector/', {
            show: $('#showID').attr('value'),
            image_type: type,
            provider: $('#images-provider').val(),
        }, data => {
            const container = imageSelectorDialog.children('.images');
            let image = null;

            container.empty();
            $.each(data, (i, entry) => {
                const thumbPath = typeof entry === 'string' ? entry : entry.thumb;
                const imagePath = typeof entry === 'string' ? entry : entry.image;

                image = $('<img>').on('click', (ev) => {
                    $('.image-selector-item-selected').removeClass('image-selector-item-selected');
                    $(ev.target).addClass('image-selector-item-selected')
                }).attr('src', thumbPath)
                    .attr('data-image', imagePath)
                    .attr('data-image-type', type)
                    .addClass('image-selector-item');

                image.appendTo(container);
            });

            imageSelectorDialog.dialog('option', 'dialogClass', 'browserDialog');
        });
    }

    $.fn.nImageSelector = function () {
        const field = $(this)
        const type = field.data('image-type');

        imageSelectorDialog = $('.image-selector-dialog');
        imageSelectorDialog.data('image-type', type);

        imageSelectorDialog.dialog({
            dialogClass: 'image-selector-dialog',
            title: _('Choose Image'),
            position: {my: 'center top', at: 'center top+60', of: window},
            minWidth: Math.min($(document).width() - 80, 650),
            height: Math.min($(document).height() - 80, $(window).height() - 80),
            maxHeight: Math.min($(document).height() - 80, $(window).height() - 80),
            maxWidth: $(document).width() - 80,
            modal: true,
            autoOpen: false
        });

        imageSelectorDialog.dialog('option', 'buttons', [{
            text: 'Ok',
            class: 'btn',
            click() {
                const selectedImage = $('.image-selector-item-selected');

                if (selectedImage) {
                    const image = selectedImage.data('image');
                    const thumb = selectedImage.attr('src');
                    $('[name=' + type + ']').val(image + '|' + thumb);
                    field.attr('src', thumb).addClass('modified')
                }
                $(this).dialog('close');
            }
        }, {
            text: 'Cancel',
            class: 'btn',
            click() {
                $(this).dialog('close');
            }
        }]);

        fetchImages();
        imageSelectorDialog.dialog('open');

        return false;
    };

    $.fn.imageSelector = function () {
        const $this = $(this);
        $this.on('click', function () {
            $(this).nImageSelector();
            return false;
        })

        return $this;
    };
})(jQuery);
