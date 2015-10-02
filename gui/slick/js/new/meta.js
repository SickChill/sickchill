function metaToBool(pyVar){
    var meta = $('meta[data-var="' + pyVar + '"]').data('content');
    meta = (isNaN(meta) ? meta.toLowerCase() : meta.toString());
    return !(meta === 'false' || meta === 'none' || meta === '0');
}
