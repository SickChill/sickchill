<%inherit file="/layouts/main.mako"/>
<%!
    from sickbeard.helpers import anon_url
    import sickbeard
%>
<%block name="metas">
<meta data-var="sickbeard.SORT_ARTICLE" data-content="${sickbeard.SORT_ARTICLE}">
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="tabs">
    <span>Sort By:</span>
    <select id="showsort" class="form-control form-control-inline input-sm">
        <option value="name">Name</option>
        <option value="original" selected="selected">Original</option>
        <option value="votes">Votes</option>
        <option value="rating">% Rating</option>
        <option value="rating_votes">% Rating > Votes</option>
    </select>

    <span style="margin-left:12px">Sort Order:</span>
    <select id="showsortdirection" class="form-control form-control-inline input-sm">
        <option value="asc" selected="selected">Asc</option>
        <option value="desc">Desc</option>
    </select>
</div>

${imdb_lists}
<br>
<div id="imdbShows">
    <div id="container">

    </div>
</div>
<br>
</%block>
