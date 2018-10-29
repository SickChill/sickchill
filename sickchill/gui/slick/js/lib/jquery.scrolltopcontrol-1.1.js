/* JQuery Scroll to Top Control script- (c) Dynamic Drive DHTML code library: http://www.dynamicdrive.com.
* Available/ usage terms at http://www.dynamicdrive.com (March 30th, 09')
*/

const scrolltotop = {
    // Startline: Integer. Number of pixels from top of doc scrollbar is scrolled before showing control
    // scrollto: Keyword (Integer, or "Scroll_to_Element_ID"). How far to scroll document up when control is clicked on (0=top).
    setting: {
        startline: 100,
        scrollto: 0,
        scrollduration: 1000,
        fadeduration: [500, 100]
    },
    controlHTML: topImageHtml, // eslint-disable-line no-undef
    // Offset of control relative to right/bottom of window corner
    controlattrs: {
        offsetx: 10,
        offsety: 10
    },
    anchorkeyword: '#top', // Enter href value of HTML anchors on the page that should also act as "Scroll Up" links
    state: {isvisible: false, shouldvisible: false},
    scrollup: function() {
        // If control is positioned using JavaScript
        if (!this.cssfixedsupport) {
            // Hide control immediately after clicking it
            this.$control.css({
                opacity: 0
            });
        }
        let dest = isNaN(this.setting.scrollto) ? this.setting.scrollto : parseInt(this.setting.scrollto, 10);
        if (typeof dest === 'string' && jQuery('#' + dest).length === 1) { // Check element set by string exists
            dest = jQuery('#' + dest).offset().top;
        } else {
            dest = 0;
        }
        this.$body.animate({scrollTop: dest}, this.setting.scrollduration);
    },
    keepfixed: function() {
        const $window = jQuery(window);
        const controlx = $window.scrollLeft() + $window.width() - this.$control.width() - this.controlattrs.offsetx;
        const controly = $window.scrollTop() + $window.height() - this.$control.height() - this.controlattrs.offsety;
        this.$control.css({left: controlx + 'px', top: controly + 'px'});
    },
    togglecontrol: function() {
        const scrolltop = jQuery(window).scrollTop();
        if (!this.cssfixedsupport) {
            this.keepfixed();
        }
        this.state.shouldvisible = (scrolltop >= this.setting.startline);
        if (this.state.shouldvisible && !this.state.isvisible) {
            this.$control.stop().animate({opacity: 1}, this.setting.fadeduration[0]);
            this.state.isvisible = true;
        } else if (this.state.shouldvisible === false && this.state.isvisible) {
            this.$control.stop().animate({opacity: 0}, this.setting.fadeduration[1]);
            this.state.isvisible = false;
        }
    },
    init: function() {
        jQuery(document).ready(function($) {
            const mainobj = scrolltotop;
            const iebrws = document.all;

            // Not IE or IE7+ browsers in standards mode
            mainobj.cssfixedsupport = !iebrws || iebrws && document.compatMode.toLowerCase() === 'CSS1Compat'.toLowerCase() && window.XMLHttpRequest; // eslint-disable-line no-mixed-operators
            mainobj.$body = (window.opera) ? (document.compatMode.toLowerCase() === 'CSS1Compat'.toLowerCase() ? $('html') : $('body')) : $('html,body');
            mainobj.$control = $('<div id="topcontrol">' + mainobj.controlHTML + '</div>').css({
                position: mainobj.cssfixedsupport ? 'fixed' : 'absolute',
                bottom: mainobj.controlattrs.offsety,
                right: mainobj.controlattrs.offsetx,
                opacity: 0,
                cursor: 'pointer'
            }).attr({
                title: 'Scroll Back to Top'
            }).on('click', function() {
                mainobj.scrollup();
                return false;
            }).appendTo('body');

            // Loose check for IE6 and below, plus whether control contains any text
            if (document.all && !window.XMLHttpRequest && mainobj.$control.text() !== '') {
                // IE6- seems to require an explicit width on a DIV containing text
                mainobj.$control.css({
                    width: mainobj.$control.width()
                });
            }
            mainobj.togglecontrol();
            $('a[href="' + mainobj.anchorkeyword + '"]').on('click', function() {
                mainobj.scrollup();
                return false;
            });
            $(window).on('scroll resize', function() {
                mainobj.togglecontrol();
            });
        });
    }
};

scrolltotop.init();
