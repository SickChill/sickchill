function metaToBool(pyVar){
    var meta = $('meta[data-var="' + pyVar + '"]').data('content');
    meta = (isNaN(meta) ? meta.toLowerCase() : meta.toString());
    return !(meta === 'false' || meta === 'none' || meta === '0');
}

function getMeta(pyVar){
    return $('meta[data-var="' + pyVar + '"]').data('content');
}
