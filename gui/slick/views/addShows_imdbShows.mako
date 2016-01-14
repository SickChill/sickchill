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
	<ul>
        <li><a href="#tabs-1">Manage Directories</a></li>
        <li><a href="#tabs-2">Customize Options</a></li>
    </ul>
    <div id="tabs-1" class="existingtabs">
        <%include file="/inc_rootDirs.mako"/>
    </div>
    <div id="tabs-2" class="existingtabs">
        <%include file="/inc_addShowOptions.mako"/>
    </div>
    <br>

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
    
   		% for i, userlists in enumerate(imdb_lists):
   		<option disabled>_________</option>
   			% for x, value in enumerate(imdb_lists[userlists]):
   				
   				% for index, key in enumerate(value):
   					<option value="${value[key]}">${key}</option>
   				% endfor
   				
   			% endfor
		% endfor
   		
    </select>
</div>

<% imdb_tt = [show.imdbid for show in sickbeard.showList if show.imdbid] %>

<br>
<div id="imdbShows">
    <div id="container">
    % if not imdb_shows:
    	% if imdb_exception:
        <div class="trakt_show" style="width:100%; margin-top:20px">
            <p class="red-text">Fetching of IMDB Data failed. Are you online?
            <strong>Exception:</strong>
            <p>${imdb_exception}</p>
        </div>
        % else:
        <div class="trakt_show" style="width:100%; margin-top:20px">
            <p class="red-text">Fetching of IMDB Data...</p></div>
        % endif
    % else:
        % for cur_result in imdb_shows:
            % if cur_result['imdb_tt'] in imdb_tt:
                <% continue %>
            % endif

            % if 'rating' in cur_result and cur_result['rating']:
                <% cur_rating = cur_result['rating'] %>
                <% cur_votes = cur_result['votes'] %>
            % else:
                <% cur_rating = '0' %>
                <% cur_votes = '0' %>
            % endif

            <div class="trakt_show" data-name="${cur_result['name']}" data-rating="${cur_rating}" data-votes="${cur_votes}">
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
                            <a href="${srRoot}/addShows/addShowByID?indexer_id=${cur_result['imdb_tt']}&amp;show_name=${cur_result['name'] | u}&amp;indexer=IMDB" class="btn btn-xs" data-no-redirect>Add Show</a>
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
