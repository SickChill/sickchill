// JQuery Scroll to Top Control script (c) Dynamic Drive DHTML code library: http://www.dynamicdrive.com.
// Terms at http://www.dynamicdrive.com (March 30th, 09')
import $ from 'jquery';

const scrolltotop = {
    // Startline: Integer. Number of pixels from top of doc scrollbar is scrolled before showing control
    // scrollto: Keyword (Integer, or "Scroll_to_Element_ID"). How far to scroll document up when control is clicked on (0=top).
    setting: {startline: 100, scrollto: 0, scrollduration: 1000, fadeduration: [500, 100]},
    controlattrs: {offsetx: 10, offsety: 10}, // Offset of control relative to right/ bottom of window corner
    anchorkeyword: '#top', // Enter href value of HTML anchors on the page that should also act as "Scroll Up" links

    state: {
        isvisible: false,
        shouldvisible: false
    },

    scrollup() {
        // If control is positioned using JavaScript
        if (!this.cssfixedsupport) {
            // Hide control immediately after clicking it
            this.$control.css({opacity: 0});
        }
        let dest = isNaN(this.setting.scrollto) ? this.setting.scrollto : parseInt(this.setting.scrollto, 10);
        // Check element set by string exists
        if (typeof dest === 'string' && $('#' + dest).length === 1) {
            dest = $('#' + dest).offset().top;
        } else {
            dest = 0;
        }
        this.$body.animate({
            scrollTop: dest
        }, this.setting.scrollduration);
    },
    keepfixed() {
        const $window = $(window);
        const controlx = $window.scrollLeft() + $window.width() - this.$control.width() - this.controlattrs.offsetx;
        const controly = $window.scrollTop() + $window.height() - this.$control.height() - this.controlattrs.offsety;
        this.$control.css({
            left: controlx + 'px',
            top: controly + 'px'
        });
    },
    togglecontrol() {
        const scrolltop = $(window).scrollTop();
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
    init(opts) {
        opts = opts || {
            html: ''
        };
        const mainobj = scrolltotop;
        const iebrws = document.all;

        // Not IE or IE7+ browsers in standards mode
        mainobj.cssfixedsupport = !iebrws || (iebrws && document.compatMode.toLowerCase() === 'CSS1Compat'.toLowerCase() && window.XMLHttpRequest);
        mainobj.$body = (window.opera) ? (document.compatMode.toLowerCase() === 'CSS1Compat'.toLowerCase() ? $('html') : $('body')) : $('html,body');
        mainobj.$control = $('<div id="topcontrol">' + opts.html + '</div>').css({
            position: mainobj.cssfixedsupport ? 'fixed' : 'absolute',
            bottom: mainobj.controlattrs.offsety,
            right: mainobj.controlattrs.offsetx,
            opacity: 0,
            cursor: 'pointer'
        }).attr({
            title: 'Scroll Back to Top'
        }).click(() => {
            mainobj.scrollup();
            return false;
        }).appendTo('body');

        if (document.all && !window.XMLHttpRequest && mainobj.$control.text() !== '') { // Loose check for IE6 and below, plus whether control contains any text
            mainobj.$control.css({width: mainobj.$control.width()}); // IE6- seems to require an explicit width on a DIV containing text
        }
        mainobj.togglecontrol();
        $('a[href="' + mainobj.anchorkeyword + '"]').on('click', () => {
            mainobj.scrollup();
            return false;
        });
        $(window).on('scroll resize', () => {
            mainobj.togglecontrol();
        });
    }
};

export default scrolltotop;
