$(document).ready(function() {
    $("#subtitles_languages").tokenInput([$('meta[data-var="subtitles.subtitleLanguageFilter"]').data('content')], {
        method: "POST",
        hintText: "Write to search a language and select it",
        preventDuplicates: true,
        prePopulate: [$('meta[data-var="prePopulate"]').data('content')]
    });
});
$('#config-components').tabs();
$('#subtitles_dir').fileBrowser({ title: 'Select Subtitles Download Directory' });
