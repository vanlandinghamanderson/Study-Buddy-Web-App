$(function () {
    $('.toggle-password').on('click', function () {
        var target = $('#' + $(this).data('target'));
        var isHidden = target.attr('type') === 'password';
        
        target.attr('type', isHidden ? "text" : 'password');
        $(this).text(isHidden ? 'Hide' : 'Show');
    });
});