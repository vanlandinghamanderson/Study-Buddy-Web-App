$(function() {
    $('.course-picker-row').on('coursepicker:change', function (e, courseId) {
        $('#find-group-submit').prop('disabled', !courseId);
    });
});