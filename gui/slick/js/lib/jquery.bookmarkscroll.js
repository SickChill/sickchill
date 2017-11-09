/* Scrolling HTML Bookmarks script- (c) Dynamic Drive DHTML code library: http://www.dynamicdrive.com.
*  Available/ usage terms at http://www.dynamicdrive.com/ (April 11th, 09')
*/

var bookmarkscroll = {
    setting: {
        duration: 1000,
        yoffset: -50
    },
    topkeyword: '#top', // Keyword used in your anchors and scrollTo() to cause script to scroll page to very top
    scrollTo: function(dest, options) {
        const $ = jQuery;
        options = options || {};
        const $dest = (typeof dest === 'string' && dest.length > 0) ? (dest === this.topkeyword ? 0 : $('#' + dest)) : (dest) ? $(dest) : []; // Get element based on id, topkeyword, or dom ref
        if ($dest === 0 || $dest.length === 1 && (!options.autorun || options.autorun && Math.abs($dest.offset().top + (options.yoffset || this.setting.yoffset) - $(window).scrollTop()) > 5)) { // eslint-disable-line no-mixed-operators
            this.$body.animate({
                scrollTop: ($dest === 0) ? 0 : $dest.offset().top + (options.yoffset || this.setting.yoffset)
            }, (options.duration || this.setting.duration));
        }
    },
    urlparamselect: function() {
        var param = window.location.search.match(/scrollto=[\w\-_,]+/i); // Search for scrollto=divid
        return (param) ? param[0].split('=')[1] : null;
    },
    init: function() {
        jQuery(document).ready(function($) {
            const mainobj = bookmarkscroll;
            mainobj.$body = (window.opera) ? (document.compatMode === 'CSS1Compat' ? $('html') : $('body')) : $('html,body');

            // Get div of page.htm?scrollto=divid
            const urlselectid = mainobj.urlparamselect();
            // If id defined
            if (urlselectid) {
                setTimeout(function() {
                    mainobj.scrollTo(document.getElementById(urlselectid) || $('a[name=' + urlselectid + ']:eq(0)').get(0), {
                        autorun: true
                    });
                }, 100);
            }
            // Loop through links with "#" prefix
            $('a[href^="#"]').each(function() {
                // If hash value is more than just "#"
                if (this.hash.length > 1) {
                    const $bookmark = $('a[name=' + this.hash.substr(1) + ']:eq(0)');

                    // If HTML anchor with given ID exists or href==topkeyword
                    if ($bookmark.length === 1 || this.hash === mainobj.topkeyword) {
                        // Non IE, or IE7+
                        if ($bookmark.length === 1 && !document.all) {
                            $bookmark.html('.').css({position: 'absolute', fontSize: 1, visibility: 'hidden'});
                        }
                        $(this).click(function(event) {
                            mainobj.scrollTo((this.hash === mainobj.topkeyword) ? mainobj.topkeyword : $bookmark.get(0), {}, this.hash);
                            event.preventDefault();
                        });
                    }
                }
            });
        });
    }
};

bookmarkscroll.init();
