<%inherit file="/layouts/main.mako"/>
<%!
    from sickbeard.helpers import anon_url
    import sickbeard
%>
<%block name="scripts">
<script type="text/javascript" src="${srRoot}/js/rootDirs.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/plotTooltip.js?${sbPID}"></script>
<script type="text/javascript" src="${srRoot}/js/qualityChooser.js?${sbPID}"></script>
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
					<p>If you don't want to use the default show options, you can change them here!</p>
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
    
    <span style="margin-left:12px">Select List:</span>
    <select id="showlist" class="form-control form-control-inline input-sm">
    <option value="popular">IMDB Popular</option>
    
    % if imdb_lists:
   		% for i, userlists in enumerate(imdb_lists):
   		% if imdb_lists.has_key(userlists):
	   		<option disabled>_________</option>
	   			% for x, value in enumerate(imdb_lists[userlists]):
	   				
	   				% for index, key in enumerate(value):
	   					<option value="${value[key]}">${key}</option>
	   				% endfor
	   				
	   			% endfor
	   	% endif
		% endfor
   	% endif	
    </select>
</div>

<% imdb_tt = [show.imdbid for show in sickbeard.showList if show.imdbid] %>

<br>
<div id="imdbShows">
    <div id="container">
    % if not imdb_shows:
    	% if imdb_exception:
        <div class="trakt_show" style="width:100%; margin-top:20px">
            <p class="red-text">Fetching of IMDB Data failed.</p>
            <strong>Exception:</strong>
            <p>${imdb_exception}</p>
        </div>
        % else:
        <div class="trakt_show" style="width:100%; margin-top:20px">
            <p class="red-text">Fetching of IMDB Data...</p></div>
        % endif
    % else:
        % for cur_result in imdb_shows:

            % if 'rating' in cur_result and cur_result['rating']:
                <% cur_rating = cur_result['rating'] %>
                <% cur_votes = cur_result['votes'] %>
            % else:
                <% cur_rating = '0' %>
                <% cur_votes = '0' %>
            % endif

            <div class="show-row" data-callback_id="${cur_result['imdb_tt']}" data-name="${cur_result['name']}" data-rating="${cur_rating}" data-votes="${cur_votes}">
                <div class="traktContainer">
                    <div class="trakt-image">
                        <a class="trakt-image" href="${anon_url(cur_result['imdb_url'])}" target="_blank"><img alt="" class="trakt-image" src="${srRoot}/cache/${cur_result['image_path']}" /></a>
                    </div>

                    <div class="show-title">
                        ${(cur_result['name'], '<span>&nbsp;</span>')['' == cur_result['name']]}
                    </div>

                    <div class="clearfix">
                        <p>${int(float(cur_rating)*10)}% <img src="${srRoot}/images/heart.png"></p>
                        <i>${cur_votes} votes</i>
                        <div class="traktShowTitleIcons">
                            % if cur_result['imdb_tt'] in imdb_tt:
                            <% indexer_id = [show.indexerid for show in sickbeard.showList if show.imdbid == cur_result['imdb_tt']][0] %>
                            <a href="${srRoot}/home/displayShow?show=${indexer_id}" class="btn btn-xs">In List</a>
                            % else:
                            <a href="${srRoot}/addShows/addShowByID" class="btn btn-xs" data-indexer="IMDB" data-indexer_id="${cur_result['imdb_tt']}" data-show_name="${cur_result['name'] | u}" data-add-show>Add Show</a>
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
