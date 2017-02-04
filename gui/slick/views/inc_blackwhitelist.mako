<div id="blackwhitelist">
    <input type="hidden" name="whitelist" id="whitelist"/>
    <input type="hidden" name="blacklist" id="blacklist"/>

    <div class="row">
        <div class="col-md-12">
            <b>Fansub Groups:</b>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            ${_("""<p>Select your preferred fansub groups from the <b>Available Groups</b> and add them to the <b>Whitelist</b>. Add groups to the <b>Blacklist</b> to ignore them.</p>
            <p>The <b>Whitelist</b> is checked <i>before</i> the <b>Blacklist</b>.</p>
            <p>Groups are shown as <b>Name</b> | <b>Rating</b> | <b>Number of subbed episodes</b>.</p>
            <p>You may also add any fansub group not listed to either list manually.</p>
            <p>When doing this please note that you can only use groups listed on anidb for this anime.
            <br>If a group is not listed on anidb but subbed this anime, please correct anidb's data.</p>""")}
        </div>
    </div>
    <div class="row fansub-picker">
        <div class="col-md-12">
            <div class="row">
                <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
                    <div class="row">
                        <div class="col-md-12">
                            <h4>${_('Whitelist')}</h4>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <select id="white" multiple="multiple" size="12" title="white">
                                % for keyword in whitelist:
                                    <option value="${keyword}">${keyword}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" id="removeW" value="${_('Remove')}" type="button"/>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
                    <div class="row">
                        <div class="col-md-12">
                            <h4>${_('Available Groups')}</h4>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <select id="pool" multiple="multiple" size="12" title="pool">
                                % for group in groups:
                                    % if group['name'] not in whitelist and group['name'] not in blacklist:
                                        <option value="${group['name']}">${group['name']} | ${group['rating']} | ${group['range']}</option>
                                    % endif
                                % endfor
                            </select>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" id="addW" value="${_('Add to Whitelist')}" type="button"/>
                            <input class="btn" id="addB" value="${_('Add to Blacklist')}" type="button"/>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4 col-md-4 col-sm-4 col-xs-12">
                    <div class="row">
                        <div class="col-md-12">
                            <h4>${_('Blacklist')}</h4>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <select id="black" multiple="multiple" size="12" title="black">
                                % for keyword in blacklist:
                                    <option value="${keyword}">${keyword}</option>
                                % endfor
                            </select>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">
                            <input class="btn" id="removeB" value="${_('Remove')}" type="button"/>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="row" style="padding-top:10px;">
        <div class="col-md-12">
            <div class="row">
                <div class="col-md-12">
                    <h4>${_('Custom Group')}</h4>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <input type="text" id="addToPoolText" class="form-control input-sm form-control-inline" autocapitalize="off"  title="addToPoolText"/>
                    <input class="btn" type="button" value="${_('Add to Whitelist')}" id="addToWhite">
                    <input class="btn" type="button" value="${_('Add to Blacklist')}" id="addToBlack">
                </div>
            </div>
        </div>
    </div>
</div>
