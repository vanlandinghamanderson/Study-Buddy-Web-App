$(function () {
    $('.collapsible-header').on('click', function () {
        var $header = $(this);
        $header.toggleClass('collapsed');
        $($header.data('target')).toggleClass('collapsed');
    });

    var $modal = $('#confirm-modal');
    var pendingForm = null;

    $('.confirm-form').on('submit', function (e) {
        e.preventDefault();
        pendingForm = this;
        $('#confirm-modal-text').text($(this).data('confirm-text') || 'Are you sure?');
        $modal.addClass('open');
    });

    $('#confirm-modal-yes').on('click', function() {
        $modal.removeClass('open');
        if (pendingForm) {
            pendingForm.submit();
            pendingForm = null;
        }
    });

    $('#confirm-modal-no').on('click', function() {
        $modal.removeClass('open');
        pendingForm = null;
    });
});