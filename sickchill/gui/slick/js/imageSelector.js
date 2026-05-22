(function ($) {
    const imageTypeSizes = {
        poster: {
            minHeight: 269,
            targetRatio: 40 / 57,
            tolerance: 0.02,
            validate(img) {
                if (img.height < this.minHeight) {
                    return false;
                }

                const actualRatio = img.width / img.height;
                const diff = Math.abs(actualRatio - this.targetRatio);
                return diff <= this.tolerance;
            },
            errorMsg: 'Poster must have aspect ratio ≈ 40:57 (≈0.7018) and height ≥ 269px.',
        },
        banner: {
            minHeight: 37,
            targetRatio: 200 / 37,
            tolerance: 0.03,
            validate(img) {
                if (img.height < this.minHeight) {
                    return false;
                }

                const actualRatio = img.width / img.height;
                const diff = Math.abs(actualRatio - this.targetRatio);
                return diff <= this.tolerance;
            },
            errorMsg: 'Banner must have aspect ratio ≈ 200:37 (5.405:1) and height ≥ 37px.',
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

                    // Special handling for uploaded images
                    const finalValue = source && source.startsWith('data:image')
                        ? source
                        : (image ? image + '|' : '') + thumb;

                    // Update hidden field and main preview
                    $('[name=' + imageType + ']').val(finalValue);
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

            if (this.files && this.files.length > 0) {
                const file = this.files[0];
                console.log('📤 File selected:', file.name);

                const reader = new FileReader();
                reader.addEventListener('load', event_ => {
                    const dataUrl = event_.target.result;

                    if (typeof dataUrl !== 'string' || !dataUrl.startsWith('data:image')) {
                        console.error('❌ Invalid data URL');
                        return;
                    }

                    console.log('📸 Data URL length:', dataUrl.length);

                    const img = new Image();
                    img.addEventListener('load', () => {
                        if (imageTypeSizes[imageType].validate(img)) {
                            console.log('✅ Image validated for', imageType);

                            // === MULTIPLE FALLBACK SELECTORS FOR HIDDEN FIELD ===
                            let hiddenInput = null;
                            const selectors = [
                                'input[name="' + imageType + '"]',
                                '#' + imageType,
                                'input[type="hidden"][name="' + imageType + '"]',
                            ];

                            for (const sel of selectors) {
                                hiddenInput = $(sel);
                                if (hiddenInput.length > 0) {
                                    break;
                                }
                            }

                            if (hiddenInput && hiddenInput.length > 0) {
                                hiddenInput.val(dataUrl);
                                console.log('✅ SUCCESS: Hidden field updated using selector');
                            } else {
                                console.error('❌ Could not find hidden input for', imageType);
                            }

                            // Update preview
                            $('.image-selector-dialog .images').empty().append($('<img alt="Selector preview">')
                                .attr('src', dataUrl)
                                .css({
                                    'max-width': '100%',
                                    'max-height': '320px',
                                    'object-fit': 'contain',
                                }));
                        } else {
                            imageSelectorElement.children('.error').text(imageTypeSizes[imageType].errorMsg).show();
                        }
                    });

                    img.src = dataUrl;
                });

                reader.readAsDataURL(file);
            }
        });

        element.on('click', function () {
            $(this).nImageSelector(imageSelectorElement);
            return false;
        });

        return element;
    };
})(jQuery);
