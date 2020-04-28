<%inherit file="/layouts/main.mako"/>
<%block name="content">
<div id="addShowPortal">
    <div class="row">
        <div class="col-md-12">
            % if not header is UNDEFINED:
                <h1 class="header">${header}</h1>
            % else:
                <h1 class="title">${title}</h1>
            % endif
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <a href="${static_url("addShows/newShow/", include_version=False)}" id="btnNewShow" class="btn btn-large">
                <div class="button"><div class="add-list-icon-addnewshow"></div></div>
                <div class="buttontext">
                    <h3>${_('Add New Show')}</h3>
                    <p>${_('For shows that you haven\'t downloaded yet, this option finds a show on theTVDB.com, creates a directory for its episodes, and adds it to SickChill.')}</p>
                </div>
            </a>
        </div>
    </div>
    <br/>
    <div class="row">
        <div class="col-md-12">
            <a href="${static_url("addShows/trendingShows/?traktList=anticipated", include_version=False)}" id="btnNewShow" class="btn btn-large">
                <div class="button"><div class="add-list-icon-addtrakt"></div></div>
                <div class="buttontext">
                    <h3>${_('Add From Trakt Lists')}</h3>
                    <p>${_('For shows that you haven\'t downloaded yet, this option lets you choose from a show from one of the Trakt lists to add to SickChill.')}</p>
                </div>
            </a>
        </div>
    </div>
    <br/>
    <div class="row">
        <div class="col-md-12">
            <a href="${static_url("addShows/popularShows/", include_version=False)}" id="btnNewShow" class="btn btn-large">
                <div class="button"><div class="add-list-icon-addimdb"></div></div>
                <div class="buttontext">
                    <h3>${_('Add From IMDB\'s Popular Shows')}</h3>
                    <p>${_('View IMDB\'s list of the most popular shows. This feature uses IMDB\'s MOVIEMeter algorithm to identify popular TV Series.')}</p>
                </div>
            </a>
        </div>
    </div>
    <br/>
    <div class="row">
        <div class="col-md-12">
            <a href="${static_url("addShows/favoriteShows/", include_version=False)}" id="btnNewShow" class="btn btn-large btn-block">
                <div class="button"><div class="add-list-icon-addtvdb"></div></div>
                <div class="buttontext">
                    <h3>${_('Add From TVDB\'s Favorited Shows')}</h3>
                    <p>${_('View the list of shows you have marked as favorite on theTVDB.')}</p>
                </div>
            </a>
        </div>
    </div>
    <br/>
    <div class="row">
        <div class="col-md-12">
            <a href="${static_url("addShows/existingShows/", include_version=False)}" id="btnExistingShow" class="btn btn-large">
                <div class="button"><div class="add-list-icon-addexistingshow"></div></div>
                <div class="buttontext">
                    <h3>${_('Add Existing Shows')}</h3>
                    <p>${_('Use this option to add shows that already have a folder created on your hard drive. SickChill will scan your existing metadata/episodes and add the show accordingly.')}</p>
                </div>
            </a>
        </div>
    </div>
</div>
</%block>
