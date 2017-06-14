import log from '../log';

const metaToBool = pyVar => {
    let meta = $('meta[data-var="' + pyVar + '"]').data('content');
    if (meta === undefined) {
        log.info(pyVar + ' is empty, did you forget to add this to main.mako?');
        return meta;
    }
    meta = (isNaN(meta) ? meta.toLowerCase() : meta.toString());
    return !(meta === 'false' || meta === 'none' || meta === '0');
};

export default metaToBool;
