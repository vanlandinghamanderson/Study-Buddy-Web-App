from main import app


def test_find_buddies_redirects_for_stale_session():
    client = app.test_client()
    with client.session_transaction() as session:
        session['student_id'] = 999999

    response = client.get('/find_buddies')

    assert response.status_code == 302
    assert response.headers['Location'] == '/login'
