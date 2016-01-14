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
	<span>Select List:</span>
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

<br>
<div id="imdbShows">
    <div id="container">

    </div>
</div>
<br>
</%block>
