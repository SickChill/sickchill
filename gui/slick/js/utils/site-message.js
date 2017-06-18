import $ from 'jquery';

import config from '../config';

class SiteMessage {
    constructor(level, tag, message) {
        this.level = level || 'danger';
        this.tag = tag || '';
        this.message = message || '';

        this.$messages = $('#site-messages');
    }

    init() {
        const {level, tag, message} = this;
        $.post(config.srRoot + '/ui/set_site_message', {level, tag, message}, siteMessages => siteMessages.forEach(this.addMessage));

        this.$messages.on('click', '.site-message-dismiss', (index, element) => {
            element.hide();
            const id = $(element).parent().data('id');
            $.post(config.srRoot + '/ui/dismiss-site-message', {index: id});
        });
    }

    getMessages() {
        $.get(config.srRoot + '/ui/get_site_message', siteMessages => siteMessages.forEach(this.addMessage));
    }

    addMessage(opts) {
        const {id, level, message} = opts;
        if (this.$messages.find(`[data-id=${id}]`)) {
            this.$messages.find(`[data-id=${id}] span`).html(message);
        } else {
            this.$messages.append(`
                <div data-id="${id}" class="alert alert-${level} upgrade-notification hidden-print" role="alert">
                    <span>${message}</span><span class="glyphicon glyphicon-check site-message-dismiss pull-right"/>
                </div>
            `);
        }
    }
}

export default SiteMessage;
