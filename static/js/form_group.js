$(function () {
    $('.course-picker-row').on('coursepicker:change', function (e, courseId) {
        $('#form-group-submit').prop('disabled', !courseId);
    });
});