import log from '../log';

const getMeta = pyVar => {
    return $('meta[data-var="' + pyVar + '"]').data('content');
};

const metaToBool = pyVar => {
    let meta = $('meta[data-var="' + pyVar + '"]').data('content');
    if (meta === undefined) {
        log.info(pyVar + ' is empty, did you forget to add this to main.mako?');
        return meta;
    }
    meta = (isNaN(meta) ? meta.toLowerCase() : meta.toString());
    return !(meta === 'false' || meta === 'none' || meta === '0');
};

const isMeta = (pyVar, result) => {
    const reg = new RegExp(result.length > 1 ? result.join('|') : result);
    return (reg).test($('meta[data-var="' + pyVar + '"]').data('content'));
};

const notifyModal = message => {
    $('#site-notification-modal .modal-body').html(message);
    $('#site-notification-modal').modal();
};

export {
    getMeta,
    metaToBool,
    isMeta,
    notifyModal
};
