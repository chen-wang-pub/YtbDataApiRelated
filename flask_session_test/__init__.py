from flask import Flask, render_template_string, request, session, redirect, url_for
"""
The workflow os this client-side session server should be

1. When new user comes, assign it a random str as identifier. For any further request from the user, the identifier is needed
2. The user can queue either ytb items, or ytber's playlsit, or spotify list for download
3. After queue succeeded or failed, the client side script will check with server if any files are ready for download in a 30 - 60 sec intervals.
4. Keep checking until all queued request from client reached a result. then delete the session


however, this should not be the best approach. please check for https://testdriven.io/blog/flask-server-side-sessions/
for server side session.
"""

# Create the Flask application
app = Flask(__name__)

# Details on the Secret Key: https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY
# NOTE: The secret key is used to cryptographically-sign the cookies used for storing
#       the session data.
app.secret_key = 'BAD_SECRET_KEY'


@app.route('/set_email', methods=['GET', 'POST'])
def set_email():
    if request.method == 'POST':
        # Save the form data to the session object
        session['email'] = request.form['email_address']
        return redirect(url_for('get_email'))

    return """
        <form method="post">
            <label for="email">Enter your email address:</label>
            <input type="email" id="email" name="email_address" required />
            <button type="submit">Submit</button
        </form>
        """


@app.route('/get_email')
def get_email():
    return render_template_string("""
            {% if session['email'] %}
                <h1>Welcome {{ session['email'] }}!</h1>
            {% else %}
                <h1>Welcome! Please enter your email <a href="{{ url_for('set_email') }}">here.</a></h1>
            {% endif %}
        """)


@app.route('/delete_email')
def delete_email():
    # Clear the email stored in the session object
    session.pop('email', default=None)
    return '<h1>Session deleted!</h1>'


if __name__ == '__main__':
    app.run()