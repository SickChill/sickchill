const getMeta = pyVar => {
    return $('meta[data-var="' + pyVar + '"]').data('content');
};

export default getMeta;
