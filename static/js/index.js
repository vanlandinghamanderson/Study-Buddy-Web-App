$('#register-btn').click(function() {
    var first_name = $('#first_name').val()
    var last_name = $('#last_name').val()
    var degree = $('#degree').val()
    var major = $('#major').val()
    var username = $('#username').val()
    var password = $('#password').val()

    if (!first_name || !last_name || !degree || !major || !username || !password) {
        alert('Please enter all fields...', 'error');
        return;
    }

    $.ajax({
        url: '/register',
        method: 'POST',
        data: { first_name: first_name, last_name: last_name,
            degree_id: degree, major_id: major, username: username,
            password: password
        },
        success: function(response) {
            if(response.status == 'success') {
                showFlash('Account created! Redirecting...', 'success');
                setTimeout(function() {
                    window.location.href = '/dashboard';
                }, 1500);
            } else {
                showFlash(response.message, 'error');
            }
        }
    });
});

function showFlash(message, type) {
    $('#flash-message')
    .text(message)
    .removeClass('hide success error')
    .addClass(type);
}
