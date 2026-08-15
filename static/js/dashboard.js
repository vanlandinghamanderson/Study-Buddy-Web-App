$(function () {
    $('.collapsible-header').on('click', function () {
        var $header = $(this);
        $header.toggleClass('collapsed');
        $($header.data('target')).toggleClass('collapsed');
    });
});