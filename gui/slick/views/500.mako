<%inherit file="/layouts/main.mako"/>

<%block name="content">
<h1 class="header">${header}</h1>
<p>
${_("""A mako error has occured.<br>
If this happened during an update a simple page refresh may be the solution.<br>
Mako errors that happen during updates may be a one time error if there were significant ui changes.""")}
<br>
</p>
<hr>
<a href="#mako-error" class="btn btn-default" data-toggle="collapse">_('Show/Hide Error')</a>
<div id="mako-error" class="collapse">
<br>
<div class="align-center">
<pre>
<% filename, lineno, function, line = backtrace.traceback[-1] %>
File ${filename}:${lineno}, in ${function}:
% if line:
${line}
% endif
${str(backtrace.error.__class__.__name__)}: ${backtrace.error}
</pre>
</div>
</div>
</%block>
