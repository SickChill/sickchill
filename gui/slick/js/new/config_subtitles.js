$(document).ready(function() {
    $("#subtitles_languages").tokenInput(
            [${",\r\n".join("{id: \"" + lang.opensubtitles + "\", name: \"" + lang.name + "\"}" for lang in subtitles.subtitleLanguageFilter())}],
            {
                method: "POST",
                hintText: "Write to search a language and select it",
                preventDuplicates: true,
                prePopulate: [${",\r\n".join("{id: \"" + subtitles.fromietf(lang).opensubtitles + "\", name: \"" + subtitles.fromietf(lang).name + "\"}" for lang in subtitles.wantedLanguages()) if subtitles.wantedLanguages() else ''}]
            }
        );
});
$('#config-components').tabs();
$('#subtitles_dir').fileBrowser({ title: 'Select Subtitles Download Directory' });
