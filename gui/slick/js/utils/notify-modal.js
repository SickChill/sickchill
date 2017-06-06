const notifyModal = message => {
    $('#site-notification-modal .modal-body').html(message);
    $('#site-notification-modal').modal();
};

export default notifyModal;
