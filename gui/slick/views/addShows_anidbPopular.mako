<%inherit file="/layouts/main.mako"/>
<%!
    from sickbeard.helpers import anon_url
    import sickbeard
%>
<%block name="scripts">
    <script type="text/javascript" src="${srRoot}/js/qualityChooser.js?${sbPID}"></script>
% if enable_anime_options:
    <script type="text/javascript" src="${srRoot}/js/blackwhite.js?${sbPID}"></script>
% endif
</%block>
<%block name="content">
% if not header is UNDEFINED:
    <h1 class="header">${header}</h1>
% else:
    <h1 class="title">${title}</h1>
% endif

<div id="tabs">

	<fieldset class="component-group-list">
		<div class="field-pair">
			<label class="clearfix" for="content_configure_show_options">
				<span class="component-title">Configure Show Options</span>
				<span class="component-desc">
					<input type="checkbox" class="enabler" name="configure_show_options" id="configure_show_options" />
					<p>If you don't want to use the default show options, you can change them here! Leaving it as it is, the show will be added as an anime anyhow.</p>
				</span>
			</label>
		</div>
		<div id="content_configure_show_options">
			<div class="field-pair">

				<label class="clearfix" for="configure_show_options">
				<ul>
			        <li><a href="#tabs-1">Manage Directories</a></li>
			        <li><a href="#tabs-2">Customize Options</a></li>
			    </ul>
			    <div id="tabs-1" class="existingtabs">
			        <%include file="/inc_rootDirs.mako"/>
			        <br/>
			    </div>
			    <div id="tabs-2" class="existingtabs">
			        <%include file="/inc_addShowOptions.mako"/>
			    </div>
			    </label>

			</div>
		</div>	<!-- /content_configure_show_options //-->
	</fieldset>


    <span>Sort By:</span>
    <select id="showsort" class="form-control form-control-inline input-sm">
        <option value="name">Name</option>
        <option value="original">Original</option>
        <option value="votes">Votes</option>
        <option value="rating">% Rating</option>
        <option value="rating_votes" selected="true" >% Rating > Votes</option>
    </select>

    <span style="margin-left:12px">Sort Order:</span>
    <select id="showsortdirection" class="form-control form-control-inline input-sm">
        <option value="asc">Asc</option>
        <option value="desc" selected="true" >Desc</option>
    </select>
</div>

<br>
<div id="popularShows">
    <div id="container">
    % if not recommended_shows:
        <div class="trakt_show" style="width:100%; margin-top:20px">
            <p class="red-text">Fetching of AniDB Data failed. Are you online?
            <strong>Exception:</strong>
            <p>${imdb_exception}</p>
        </div>
    % else:
        % for cur_result in recommended_shows:

            % if cur_result.rating:
                <% cur_rating = cur_result.rating %>
            % endif
            
            % if cur_result.votes:
                <% cur_votes = cur_result.votes %>
            % endif

            <div class="show-row" data-callback_id="${cur_result.indexer_id}" data-name="${cur_result.title}" data-rating="${cur_rating}" data-votes="${cur_votes}">
                <div class="traktContainer">
                    <div class="trakt-image">
                        <a class="trakt-image" href="${anon_url(cur_result.image_href)}" target="_blank">
                            <img alt="" class="trakt-image" src="${srRoot}/cache/${cur_result.image_src}" height="273px" width="186px" />
                        </a>
                    </div>

                    <div class="show-title">
                        ${cur_result.title}
                    </div>

                    <div class="clearfix">
                        <p>${int(float(cur_rating)*10)}% <img src="${srRoot}/images/heart.png"></p>
                        <i>${cur_votes} votes</i>
                        <div class="traktShowTitleIcons">
	                        % if cur_result.show_in_list:
	                            <a href="${srRoot}/home/displayShow?show=${cur_result.indexer_id}" class="btn btn-xs">In List</a>
	                        % else:
	                            <a href="${srRoot}/addShows/addShowByID" class="btn btn-xs" data-isanime="1" data-indexer="TVDB" data-indexer_id="${cur_result.indexer_id}" data-show_name="${cur_result.title | u}" data-add-show>Add Show</a>
	                       	% endif
                    	</div>
                    </div>
                </div>
            </div>
        % endfor
    % endif
    </div>
</div>
<br>
</%block>
