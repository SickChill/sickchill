<div id="blackwhitelist">
    <input type="hidden" name="whitelist" id="whitelist"/>
    <input type="hidden" name="blacklist" id="blacklist"/>

    <b>Fansub Groups:</b>
        <div >
            ${_("""<p>Select your preferred fansub groups from the <b>Available Groups</b> and add them to the <b>Whitelist</b>. Add groups to the <b>Blacklist</b> to ignore them.</p>
            <p>The <b>Whitelist</b> is checked <i>before</i> the <b>Blacklist</b>.</p>
            <p>Groups are shown as <b>Name</b> | <b>Rating</b> | <b>Number of subbed episodes</b>.</p>
            <p>You may also add any fansub group not listed to either list manually.</p>
            <p>When doing this please note that you can only use groups listed on anidb for this anime.
            <br>If a group is not listed on anidb but subbed this anime, please correct anidb's data.</p>""")}
        </div>
        <div class="bwlWrapper" id="Anime">
        <div class="blackwhitelist all">
            <div class="blackwhitelist anidb">
                <div class="blackwhitelist white">
                    <span><h4>${_('Whitelist')}</h4></span>
                    <select id="white" multiple="multiple" size="12">
                        % for keyword in whitelist:
                            <option value="${keyword}">${keyword}</option>
                        % endfor
                    </select>
                    <br>
                    <input class="btn" id="removeW" value="${_('Remove')}" type="button"/>
                </div>
                <div class="blackwhitelist pool">
                    <span><h4>${_('Available Groups')}</h4></span>
                    <select id="pool" multiple="multiple" size="12">
                    % for group in groups:
                        % if group not in whitelist and group['name'] not in blacklist:
                            <option value="${group['name']}">${group['name']} | ${group['rating']} | ${group['range']}</option>
                        % endif
                    % endfor
                    </select>
                    <br>
                    <input class="btn" id="addW" value="${_('Add to Whitelist')}" type="button"/>
                    <input class="btn" id="addB" value="${_('Add to Blacklist')}" type="button"/>
                </div>
                <div class="blackwhitelist black">
                    <span><h4>${_('Blacklist')}</h4></span>
                    <select id="black" multiple="multiple" size="12">
                        % for keyword in blacklist:
                            <option value="${keyword}">${keyword}</option>
                        % endfor
                    </select>
                    <br>
                    <input class="btn" id="removeB" value="${_('Remove')}" type="button"/>
                </div>
            </div>
            <br style="clear:both">
            <div class="blackwhitelist manual">
                <input type="text" id="addToPoolText" class="form-control form-control-inline input-sm input250" autocapitalize="off" />
                <input class="btn btn-inline" type="button" value="${_('Add to Whitelist')}" id="addToWhite">
                <input class="btn btn-inline" type="button" value="${_('Add to Blacklist')}" id="addToBlack">
            </div>
        </div>
        <br style="clear:both">
    </div>
</div>
