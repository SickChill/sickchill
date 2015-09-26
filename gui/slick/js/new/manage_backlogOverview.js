$(document).ready(function(){
    $('#pickShow').change(function(){
        var id = $(this).val();
        if (id) {
            $('html,body').animate({scrollTop: $('#show-' + id).offset().top -25},'slow');
        }
    });
});
