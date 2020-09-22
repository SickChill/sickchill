<%inherit file="/layouts/main.mako"/>

<%block name="content">
    <h1 class="header">${header}</h1>
    <p>
        ${_("""A mako error has occurred.<br>
            If this happened during an update a simple page refresh may be the solution.<br>
            Mako errors that happen during updates may be a one time error if there were significant ui changes.""")}
        <br>
    </p>
    <hr>
    <a href="#mako-error" class="btn btn-default" data-toggle="collapse">${_('Show/Hide Error')}</a>
    <div id="mako-error" class="collapse">
        <br>
        <div class="align-center">
            <pre>
                Traceback (most recent call last):
                % for filename, line_number, function, line in backtrace.traceback:
                    File ${filename}:${line_number}, in ${function or '?'}:
                    % if line:
                        ${line | trim}
                    % endif
                % endfor
                ${backtrace.errorname}: ${backtrace.message}
            </pre>
        </div>
    </div>
</%block>
