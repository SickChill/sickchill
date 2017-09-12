/* JQuery Form to Form Wizard (Initial: Oct 1st, 2010)
*  This notice must stay intact for usage
*  Author: Dynamic Drive at http://www.dynamicdrive.com/
*  Visit http://www.dynamicdrive.com/ for full source code
*/

const formtowizard = function(options) {
    this.setting = jQuery.extend({
        persistsection: false,
        revealfx: ['slide', 500],
        oninit: function() {},
        onpagechangestart: function() {}
    }, options);
    this.currentsection = -1;
    this.init(this.setting);
};

formtowizard.prototype = {
    createfieldsets: function($theform, arr) { // Reserved function for future version (dynamically wraps form elements with a fieldset element)
        $theform.find('fieldset.sectionwrap').removeClass('sectionwrap'); // Make sure no fieldsets carry 'sectionwrap' before proceeding
        let $startelement = $theform.find(':first-child'); // Reference first element inside form
        for (let i = 0; i < arr.length; i++) { // Loop thru "break" elements
            const $fieldsetelements = $startelement.nextUntil('#' + arr[i].breakafter + ', *[name=' + arr[i].breakafter + ']').andSelf(); // Reference all elements from start element to break element (nextUntil() is jQuery 1.4 function)
            $fieldsetelements.add($fieldsetelements.next()).wrapAll('<fieldset class="sectionwrap" />'); // Wrap these elements with fieldset element
            $startelement = $theform.find('fieldset.sectionwrap').eq(i).prepend('<legend class="legendStep">' + arr[i].legend + '</legend>').next(); // Increment startelement to begin at the end of the just inserted fieldset element
        }
    },
    loadsection: function(rawi, bypasshooks) {
        const thiswizard = this;
        // Doload Boolean checks to see whether to load next section (true if bypasshooks param is true or onpagechangestart() event handler doesn't return false)
        let doload = bypasshooks || this.setting.onpagechangestart(jQuery, this.currentsection, this.sections.$sections.eq(this.currentsection));
        doload = doload !== false; // Unless doload is explicitly false, set to true
        if (!bypasshooks && this.setting.validate) {
            const outcome = this.validate(this.currentsection);
            if (outcome === false) {
                doload = false;
            }
        }
        // Get index of next section to show
        let i = (rawi === 'prev') ? this.currentsection - 1 : (rawi === 'next') ? this.currentsection + 1 : parseInt(rawi, 10);
        i = (i < 0) ? this.sections.count - 1 : (i > this.sections.count - 1) ? 0 : i; // Make sure i doesn't exceed min/max limit
        if (i < this.sections.count && doload) { // If next section to show isn't the same as the current section shown
            this.$thesteps.eq(this.currentsection).addClass('disabledstep').end().eq(i).removeClass('disabledstep'); // Dull current "step" text then highlight next "step" text
            if (this.setting.revealfx[0] === 'slide') {
                this.sections.$sections.css('visibility', 'visible');
                this.sections.$outerwrapper.stop().animate({height: this.sections.$sections.eq(i).outerHeight()}, this.setting.revealfx[1]); // Animate fieldset wrapper's height to accomodate next section's height
                this.sections.$innerwrapper.stop().animate({left: -i * this.maxfieldsetwidth}, this.setting.revealfx[1], function() { // Slide next section into view
                    thiswizard.sections.$sections.each(function(thissec) {
                        // Hide fieldset sections currently not in veiw, so tabbing doesn't go to elements within them (and mess up layout)
                        if (thissec !== i) {
                            thiswizard.sections.$sections.eq(thissec).css('visibility', 'hidden');
                        }
                    });
                });
            } else if (this.setting.revealfx[0] === 'fade') { // If fx is "fade"
                this.sections.$sections.eq(this.currentsection).hide().end().eq(i).fadeIn(this.setting.revealfx[1], function() {
                    // Fix IE clearType problem
                    if (document.all && this.style && this.style.removeAttribute) {
                        this.style.removeAttribute('filter');
                    }
                });
            } else {
                this.sections.$sections.eq(this.currentsection).hide().end().eq(i).show();
            }
            this.paginatediv.$status.text('Page ' + (i + 1) + ' of ' + this.sections.count); // Update current page status text
            this.paginatediv.$navlinks.css('visibility', 'visible');
            if (i === 0) { // Hide "prev" link
                this.paginatediv.$navlinks.eq(0).css('visibility', 'hidden');
            } else if (i === this.sections.count - 1) { // Hide "next" link
                this.paginatediv.$navlinks.eq(1).css('visibility', 'hidden');
            }
            if (this.setting.persistsection) {
                formtowizard.routines.setCookie(this.setting.formid + '_persist', i);
            } // Enable persistence?
            this.currentsection = i;
            if (i === 0) {
                setTimeout($('#nameToSearch').focus, 250);
            }
        }
    },
    addvalidatefields: function() {
        const $ = jQuery;
        const setting = this.setting;
        const theform = this.$theform.get(0);
        let validatefields = [];
        // Array of form element ids to validate
        validatefields = setting.validate;
        for (let i = 0; i < validatefields.length; i++) {
            // Reference form element
            const el = theform.elements[validatefields[i]];
            if (el) {
                // Find fieldset.sectionwrap this form element belongs to
                const $section = $(el).parents('fieldset.sectionwrap:eq(0)');

                // If element is within a fieldset.sectionwrap element
                if ($section.length === 1) {
                    // Cache this element inside corresponding section
                    $section.data('elements').push(el);
                }
            }
        }
    },
    validate: function(section) {
        // Reference elements within this section that should be validated
        const elements = this.sections.$sections.eq(section).data('elements');
        const invalidtext = [_('Please fill out the following fields:\n')];
        let validated = true;
        function invalidate(el) {
            validated = false;
            invalidtext.push('- ' + (el.id || el.name));
        }
        for (let i = 0; i < elements.length; i++) {
            if (/(text)/.test(elements[i].type) && elements[i].value === '') { // Text and textarea elements
                invalidate(elements[i]);
            } else if (/(select)/.test(elements[i].type) && (elements[i].selectedIndex === -1 || elements[i].options[elements[i].selectedIndex].text === '')) { // Select elements
                invalidate(elements[i]);
            } else if (elements[i].type === undefined && elements[i].length > 0) { // Radio and checkbox elements
                let onechecked = false;
                for (let r = 0; r < elements[i].length; r++) {
                    if (elements[i][r].checked === true) {
                        onechecked = true;
                        break;
                    }
                }
                if (!onechecked) {
                    invalidate(elements[i][0]);
                }
            }
        }
        if (!validated) {
            alert(invalidtext.join('\n')); // eslint-disable-line no-alert
        }
        return validated;
    },
    init: function(setting) {
        const thiswizard = this;

        jQuery(function($) {
            let $theform = $('#' + setting.formid);

            // If form with specified ID doesn't exist, try name attribute instead
            if ($theform.length === 0) {
                $theform = $('form[name=' + setting.formid + ']');
            }
            if (setting.manualfieldsets && setting.manualfieldsets.length > 0) {
                thiswizard.createfieldsets($theform, setting.manualfieldsets);
            }
            const $stepsguide = $('<div class="stepsguide" />'); // Create Steps Container to house the "steps" text
            const $sections = $theform.find('fieldset.sectionwrap').hide(); // Find all fieldset elements within form and hide them initially
            let $sectionsWrapper = null;
            let $sectionsWrapperInner = null;
            if (setting.revealfx[0] === 'slide') { // Create outer DIV that will house all the fieldset.sectionwrap elements
                $sectionsWrapper = $('<div style="position:relative;overflow:hidden;"></div>').insertBefore($sections.eq(0)); // Add DIV above the first fieldset.sectionwrap element
                $sectionsWrapperInner = $('<div style="position:absolute;left:0;top:0;"></div>'); // Create inner DIV of $sectionswrapper that will scroll to reveal a fieldset element
            }
            let maxfieldsetwidth = $sections.eq(0).outerWidth(); // Variable to get width of widest fieldset.sectionwrap
            $sections.slice(1).each(function() { // Loop through $sections (starting from 2nd one)
                maxfieldsetwidth = Math.max($(this).outerWidth(), maxfieldsetwidth);
            });
            maxfieldsetwidth += 2; // Add 2px to final width to reveal fieldset border (if not removed via CSS)
            thiswizard.maxfieldsetwidth = maxfieldsetwidth;
            $sections.each(function(i) { // Loop through $sections again
                const $section = $(this);
                if (setting.revealfx[0] === 'slide') {
                    $section.data('page', i).css({position: 'absolute', top: 0, left: maxfieldsetwidth * i}).appendTo($sectionsWrapperInner); // Set fieldset position to "absolute" and move it to inside sectionswrapper_inner DIV
                }
                $section.data('elements', []); // Empty array to contain elements within this section that should be validated for data (applicable only if validate option is defined)
                // create each "step" DIV and add it to main Steps Container:
                const $thestep = $('<div class="step disabledstep" />').data('section', i).html('Step ' + (i + 1) + '<div class="smalltext">' + $section.find('legend:eq(0)').text() + '<p></p></div>').appendTo($stepsguide);
                $thestep.on('click', function() { // Assign behavior to each step div
                    thiswizard.loadsection($(this).data('section'));
                });
            });
            if (setting.revealfx[0] === 'slide') {
                $sectionsWrapper.width(maxfieldsetwidth); // Set fieldset wrapper to width of widest fieldset
                $sectionsWrapper.append($sectionsWrapperInner); // Add $sectionswrapper_inner as a child of $sectionswrapper
            }
            $theform.prepend($stepsguide); // Add $thesteps div to the beginning of the form
            // $stepsguide.insertBefore($sectionswrapper) //add Steps Container before sectionswrapper container
            const $thesteps = $stepsguide.find('div.step');
            // Create pagination DIV and add it to end of form:
            const $paginatediv = $('<div class="formpaginate" style="overflow:hidden;"><span class="prev" style="float:left">Prev</span> <span class="status">Step 1 of </span> <span class="next" style="float:right">Next</span></div>');
            $theform.append($paginatediv);
            thiswizard.$theform = $theform;
            if (setting.revealfx[0] === 'slide') {
                // Remember various parts of section container
                thiswizard.sections = {
                    $outerwrapper: $sectionsWrapper,
                    $innerwrapper: $sectionsWrapperInner,
                    $sections: $sections,
                    count: $sections.length
                };
                thiswizard.sections.$sections.show();
            } else {
                // Remember various parts of section container
                thiswizard.sections = {
                    $sections: $sections,
                    count: $sections.length
                };
            }

            // Remember this ref
            thiswizard.$thesteps = $thesteps;

            // Remember various parts of pagination DIV
            thiswizard.paginatediv = {
                $main: $paginatediv,
                $navlinks: $paginatediv.find('span.prev, span.next'),
                $status: $paginatediv.find('span.status')
            };

            // Assign behavior to pagination buttons
            thiswizard.paginatediv.$main.on('click', function(event) {
                if (/(prev)|(next)/.test(event.target.className)) {
                    thiswizard.loadsection(event.target.className);
                }
            });
            const sectionId = (setting.persistsection) ? formtowizard.routines.getCookie(setting.formid + '_persist') : 0;
            thiswizard.loadsection(sectionId || 0, true); // Show the first section
            thiswizard.setting.oninit($, sectionId, $sections.eq(sectionId)); // Call oninit event handler
            if (setting.validate) { // If validate array defined
                thiswizard.addvalidatefields(); // Seek out and cache form elements that should be validated
                thiswizard.$theform.submit(function() {
                    let returnval = true;
                    for (let i = 0; i < thiswizard.sections.count; i++) {
                        if (!thiswizard.validate(i)) {
                            thiswizard.loadsection(i, true);
                            returnval = false;
                            break;
                        }
                    }
                    return returnval; // Allow or disallow form submission
                });
            }
        });
    }
};

formtowizard.routines = {
    getCookie: function(Name) {
        // Construct RE to search for target name/value pair
        const re = new RegExp(Name + '=[^;]+', 'i');

        // If cookie found return it's value
        if (document.cookie.match(re)) {
            return document.cookie.match(re)[0].split('=')[1];
        }
        return null;
    },
    setCookie: function(name, value) {
        document.cookie = name + '=' + value + ';path=/';
    }
};
