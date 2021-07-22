(function ($) {
    const SIZES_BY_TYPE = {
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

    function createImage(imageSrc, thumbSrc) {
        const image = $('<img>').on('click', ev => {
            $('.image-selector-item-selected').removeClass('image-selector-item-selected');
            $(ev.target).addClass('image-selector-item-selected');
        }).attr('data-image-type', imageSelectorDialog.data('image-type'))
            .addClass('image-selector-item');

        const wrapUrl = new URL(scRoot + '/imageSelector/url_wrap/', location.href);
        if (thumbSrc) {
            wrapUrl.searchParams.append('url', thumbSrc);
            image.attr('data-thumb', thumbSrc);
        } else {
            wrapUrl.searchParams.append('url', imageSrc);
        }

        image.attr('src', wrapUrl.href).attr('data-image', imageSrc);

        image.appendTo(imagesContainer);
    }

    $.fn.nImageSelector = function (imageSelectorElement) {
        const field = $(this);
        imageType = field.data('image-type');

        imageSelectorDialog = imageSelectorElement.dialog({
            dialogClass: 'image-selector-dialog',
            classes: {
                'ui-dialog': 'ui-dialog-scrollable-by-child',
            },
            title: _('Choose Image'),
            position: {my: 'center top', at: 'center top+60', of: window},
            minWidth: Math.min($(document).width() - 80, 650),
            height: Math.min($(document).height() - 80, $(window).height() - 80),
            maxHeight: Math.min($(document).height() - 80, $(window).height() - 80),
            maxWidth: $(document).width() - 80,
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
                    const src = selectedImage.attr('src');
                    $('[name=' + imageType + ']').val((image ? image + '|' : '') + thumb);
                    field.attr('src', src).addClass('modified');
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
        const $this = $(this);

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
                const loadFunction = ev => {
                    const img = new Image();
                    img.addEventListener('load', () => {
                        if (SIZES_BY_TYPE[imageType].validate(img)) {
                            createImage(img.src);
                        } else {
                            imageSelectorElement.children('.error').text(SIZES_BY_TYPE[imageType].errorMsg);
                            imageSelectorElement.children('.error').show();
                        }
                    });
                    img.src = ev.target.result;
                };

                for (const file of this.files) {
                    const reader = new FileReader();
                    reader.addEventListener('load', loadFunction);
                    reader.readAsDataURL(file);
                }
            }
        });

        $this.on('click', function () {
            $(this).nImageSelector(imageSelectorElement);
            return false;
        });

        return $this;
    };
})(jQuery);
