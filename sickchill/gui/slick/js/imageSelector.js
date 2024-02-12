(function ($) {
    const imageTypeSizes = {
        poster: {
            minHeight: 269,
            ratio: 40 / 57,
            validate(img) {
                return img.height >= this.minHeight
                    && img.width / img.height === this.ratio;
            },
            errorMsg: 'The height of the poster can not be lower than 269 pixels and the aspect ratio should be 40:57.',
        },
        banner: {
            minHeight: 37,
            ratio: 200 / 37,
            validate(img) {
                return img.height >= this.minHeight
                    && img.width / img.height === this.ratio;
            },
            errorMsg: 'The height of the banner can not be lower than 37 pixels and the aspect ratio should be 200:37.',
        },
        fanart: {
            minHeight: 200,
            minWidth: 200,
            validate(img) {
                return img.height >= this.minHeight
                    && img.width >= this.minWidth;
            },
            errorMsg: 'The minimum allowed size for a fanart is 200x200.',
        },
    };

    let imageSelectorDialog = null;
    let imagesContainer = null;
    let imageType = null;
    let currentRequest = null;

    function fetchImages() {
        imagesContainer.empty();

        if (currentRequest) {
            currentRequest.abort();
        }

        imageSelectorDialog.dialog('option', 'dialogClass', 'browserDialog busy');

        currentRequest = $.getJSON(scRoot + '/imageSelector/', {
            show: $('#showID').attr('value'),
            imageType,
            provider: $('#images-provider').val(),
        }, data => {
            $.each(data, (i, entry) => {
                if (typeof entry === 'string') {
                    createImage(entry);
                } else {
                    createImage(entry.image, entry.thumb);
                }
            });

            imageSelectorDialog.dialog('option', 'dialogClass', 'browserDialog');
        });

        const scrollableHeight = imageSelectorDialog.outerHeight()
            - imageSelectorDialog.find('.image-provider-container').outerHeight()
            - 15;

        imagesContainer.height(scrollableHeight).css('maxHeight', scrollableHeight);
    }

    function createImage(imageSource, thumbSource) {
        const image = $('<img alt="' + $('#showID').attr('value') + ' ' + imageType + '"/>')
            .attr('data-image-type', imageSelectorDialog.data('image-type'))
            .addClass('image-selector-item').on('click', event_ => {
                $('.image-selector-item-selected').removeClass('image-selector-item-selected');
                $(event_.target).addClass('image-selector-item-selected');
            });

        const wrapUrl = new URL(scRoot + '/imageSelector/url_wrap/', location.href);
        if (thumbSource) {
            wrapUrl.searchParams.append('url', thumbSource);
            image.attr('data-thumb', thumbSource);
        } else {
            wrapUrl.searchParams.append('url', imageSource);
        }

        image.attr('src', wrapUrl.href).attr('data-image', imageSource);

        image.appendTo(imagesContainer);
    }

    $.fn.nImageSelector = function (imageSelectorElement) {
        const field = $(this);
        const margin = 80;
        const minimumWidth = 650;
        imageType = field.data('image-type');

        imageSelectorDialog = imageSelectorElement.dialog({
            dialogClass: 'image-selector-dialog',
            classes: {
                'ui-dialog': 'ui-dialog-scrollable-by-child',
            },
            title: _('Choose Image'),
            position: {my: 'center top', at: 'center top+60', of: window},
            minWidth: Math.min($(document).width() - margin, minimumWidth),
            height: Math.min($(document).height() - margin, $(window).height() - margin),
            maxHeight: Math.min($(document).height() - margin, $(window).height() - margin),
            maxWidth: $(document).width() - margin,
            modal: true,
            autoOpen: false,
        });

        imageSelectorDialog.dialog('option', 'buttons', [{
            text: 'Ok',
            class: 'btn',
            click() {
                const selectedImage = $('.image-selector-item-selected');

                if (selectedImage.length > 0) {
                    const image = selectedImage.data('image');
                    const thumb = selectedImage.data('thumb');
                    const source = selectedImage.attr('src');
                    $('[name=' + imageType + ']').val((image ? image + '|' : '') + thumb);
                    field.attr('src', source).addClass('modified');
                }

                $(this).dialog('close');
            },
        }, {
            text: 'Cancel',
            class: 'btn',
            click() {
                $(this).dialog('close');
            },
        }]);

        const dropdown = imageSelectorDialog.children('#images-provider');
        dropdown.val(dropdown.data('default'));
        imageSelectorDialog.children('.upload').hide();
        imageSelectorDialog.children('.error').hide();

        imageSelectorDialog.dialog('open');
        fetchImages();

        return false;
    };

    $.fn.imageSelector = function () {
        const element = $(this);

        const imageSelectorElement = $('.image-selector-dialog');
        imagesContainer = imageSelectorElement.children('.images');

        imageSelectorElement.find('#images-provider').on('change', function () {
            const uploadContainer = imageSelectorElement.children('.upload');

            if ($(this).children('option:selected').val() === '-1') {
                imagesContainer.empty();
                uploadContainer.show();
            } else {
                uploadContainer.hide();
                fetchImages();
            }
        });

        $('.upload #upload-image-input').on('change', function () {
            imageSelectorElement.children('.error').hide();

            if (this.files) {
                const loadFunction = event_ => {
                    const img = new Image();
                    img.addEventListener('load', () => {
                        if (imageTypeSizes[imageType].validate(img)) {
                            createImage(img.src);
                        } else {
                            imageSelectorElement.children('.error').text(imageTypeSizes[imageType].errorMsg);
                            imageSelectorElement.children('.error').show();
                        }
                    });
                    img.src = event_.target.result;
                };

                for (const file of this.files) {
                    const reader = new FileReader();
                    reader.addEventListener('load', loadFunction);
                    reader.readAsDataURL(file);
                }
            }
        });

        element.on('click', function () {
            $(this).nImageSelector(imageSelectorElement);
            return false;
        });

        return element;
    };
})(jQuery);
