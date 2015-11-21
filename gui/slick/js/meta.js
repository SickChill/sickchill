function metaToBool(pyVar){
    var meta = $('meta[data-var="' + pyVar + '"]').data('content');
    if(meta === undefined){
        console.log(pyVar + ' is empty, did you forget to add this to main.mako?');
        return meta;
    } else {
        meta = (isNaN(meta) ? meta.toLowerCase() : meta.toString());
        return !(meta === 'false' || meta === 'none' || meta === '0');
    }
}

function getMeta(pyVar){
    return $('meta[data-var="' + pyVar + '"]').data('content');
}

function isMeta(pyVar, result){
    var reg = new RegExp(result.length > 1 ? result.join('|') : result);
    return (reg).test($('meta[data-var="' + pyVar + '"]').data('content'));
}
