<%inherit file="/layouts/main.mako"/>
<%!
    import os.path
    import urllib
    import sickbeard
%>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="addShowPortal">
    <a href="${srRoot}/addShows/newShow/" id="btnNewShow" class="btn btn-large">
        <div class="button"><div class="icon-addnewshow"></div></div>
        <div class="buttontext">
            <h3>Add New Show</h3>
            <p>For shows that you haven't downloaded yet, this option finds a show on theTVDB.com, creates a directory for it's episodes, and adds it to SickRage.</p>
        </div>
    </a>

    <br><br>
    <a href="${srRoot}/addShows/trendingShows/?traktList=anticipated" id="btnNewShow" class="btn btn-large">
        <div class="button"><div class="icon-addtrendingshow"></div></div>
        <div class="buttontext">
            <h3>Add From Trakt Lists</h3>
            <p>For shows that you haven't downloaded yet, this option lets you choose from a show from one of the Trakt lists to add to SickRage .</p>
        </div>
    </a>

    <br><br>

    <a href="${srRoot}/addShows/popularShows/" id="btnNewShow" class="btn btn-large">
        <div class="button"><div class="icon-addrecommendedshow"></div></div>
        <div class="buttontext">
            <h3>Add From IMDB's Popular Shows</h3>
            <p>View IMDB's list of the most popular shows. This feature uses IMDB's MOVIEMeter algorithm to identify popular TV Series.</p>
        </div>
    </a>

    <br><br>

    <a href="${srRoot}/addShows/existingShows/" id="btnExistingShow" class="btn btn-large">
        <div class="button"><div class="icon-addexistingshow"></div></div>
        <div class="buttontext">
            <h3>Add Existing Shows</h3>
            <p>Use this option to add shows that already have a folder created on your hard drive. SickRage will scan your existing metadata/episodes and add the show accordingly.</p>
        </div>
    </a>

</div>
</%block>
