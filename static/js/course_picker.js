$(function () {
    $('.course-picker-row').each(function () {
        var $row = $(this);
        var $department = $row.find('#course_department');
        var $code = $row.find('#course_code');
        var $name = $row.find('#course_name');
        var $courseId = $row.find('#course_id');

        function optionsHtml(placeholder, items, labelKey) {
            var html = '<option value="">' + placeholder + '</option>';
            items.forEach(function (c) {
                html += '<option value="' + c.id + '">' + c[labelKey] + '</option>';
            });
            return html;
        }

        function resetSelect($select, placeholder) {
            $select.html('<option value="">' + placeholder + '</option>').prop('disabled', true);
        }

        function notifyChange(courseId) {
            $row.trigger('coursepicker:change', [courseId || '']);
        }

        function updateSelectedCourse(courseId) {
            $courseId.val(courseId || '');
            $('#find-buddy-submit').prop('disabled', !courseId);
            notifyChange(courseId || '');
        }

        $department.on('change', function () {
            var department = $(this).val();
            $courseId.val('');
            $('#find-buddy-submit').prop('disabled', true);
            resetSelect($code, 'Code...');
            resetSelect($name, 'Name...');
            notifyChange('');
            if (!department) return;

            $.getJSON('/course.json', { subject: department }, function (courses) {
                $code.html(optionsHtml('Code...', courses, 'code')).prop('disabled', false);
                $name.html(optionsHtml('Name...', courses, 'name')).prop('disabled', false);
            });
        });

        $code.on('change', function () {
            var courseId = $(this).val();
            $name.val(courseId || '');
            updateSelectedCourse(courseId);
        });

        $name.on('change', function () {
            var courseId = $(this).val();
            $code.val(courseId || '');
            updateSelectedCourse(courseId);
        });
    });
});