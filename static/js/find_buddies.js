$(function () {
    $('.course-picker-row').on('coursepicker:change', function(e, courseId) {
        $('#find-buddy-submit').prop('disabled', !courseId);
        $('#course-buddies').empty();
        $('#find-buddy-msg').text('');
    })
})