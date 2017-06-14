const isMeta = (pyVar, result) => {
    const reg = new RegExp(result.length > 1 ? result.join('|') : result);
    return (reg).test($('meta[data-var="' + pyVar + '"]').data('content'));
};

export default isMeta;
