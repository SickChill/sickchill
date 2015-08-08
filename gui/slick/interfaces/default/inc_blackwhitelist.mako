<div id="blackwhitelist">
    <input type="hidden" name="whitelist" id="whitelist"/>
    <input type="hidden" name="blacklist" id="blacklist"/>

    <b>Fansub Groups:</b>
        <div >
            <p>Select your preferred fansub groups from the <b>Available Groups</b> and add them to the <b>Whitelist</b>. Add groups to the <b>Blacklist</b> to ignore them.</p>
            <p>The <b>Whitelist</b> is checked <i>before</i> the <b>Blacklist</b>.</p>
            <p>Groups are shown as <b>Name</b> | <b>Rating</b> | <b>Number of subbed episodes</b>.</p>
            <p>You may also add any fansub group not listed to either list manually.</p>
        </div>
        <div class="bwlWrapper" id="Anime">
        <div class="blackwhitelist all">
            <div class="blackwhitelist anidb">
                <div class="blackwhitelist white">
                    <span><h4>Whitelist</h4></span>
                    <select id="white" multiple="multiple" size="12">
                        % for keyword in whitelist:
                            <option value="${keyword}">${keyword}</option>
                        % endfor
                    </select>
                    <br/>
                    <input class="btn" id="removeW" value="Remove" type="button"/>
                </div>
                <div class="blackwhitelist pool">
                    <span><h4>Available Groups</h4></span>
                    <select id="pool" multiple="multiple" size="12">
                    % for group in groups:
                        % if group not in whitelist and group['name'] not in blacklist:
                            <option value="${group['name']}">${group['name']} | ${group['rating']} | ${group['range']}</option>
                        % endif
                    % endfor
                    </select>
                    <br/>
                    <input class="btn" id="addW" value="Add to Whitelist" type="button"/>
                    <input class="btn" id="addB" value="Add to Blacklist" type="button"/>
                </div>
                <div class="blackwhitelist black">
                    <span><h4>Blacklist</h4></span>
                    <select id="black" multiple="multiple" size="12">
                        % for keyword in blacklist:
                            <option value="${keyword}">${keyword}</option>
                        % endfor
                    </select>
                    <br/>
                    <input class="btn" id="removeB" value="Remove" type="button"/>
                </div>
            </div>
            <br style="clear:both" />
            <div class="blackwhitelist manual">
                <input type="text" id="addToPoolText" class="form-control form-control-inline input-sm input250" />
                <input class="btn btn-inline" type="button" value="Add to Whitelist" id="addToWhite">
                <input class="btn btn-inline" type="button" value="Add to Blacklist" id="addToBlack">
            </div>
        </div>
        <br style="clear:both" />
    </div>
</div>
