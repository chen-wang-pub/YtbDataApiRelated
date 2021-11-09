from flask import Blueprint, request, current_app, Response, json, render_template, flash, redirect, url_for, jsonify
from app.forms import LoginForm, RegistrationForm, DownloadRequestForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User
from app.factory import db
from app.tasks import extract_spotify_playlist, search_for_ytb_items_from_spotify_list

paid_user = Blueprint("paid_user", __name__)


def placeholder_linkprocessing(data):
    if data:
        return 'data: {} has been processed by placeholder function'.format(data)
    else:
        return 'data is empty'


@paid_user.route("/index")
@login_required
def index():
    #user = {'username': 'vip'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Welcome', posts=posts)


@paid_user.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('paid_user.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('paid_user.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        #flash('Login requested for user {}, remember_me={}'.format(form.username.data, form.remember_me.data))
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('paid_user.index')
        #return redirect(url_for('paid_user.index'))
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@paid_user.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('paid_user.index'))


@paid_user.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('paid_user.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('paid_user.login'))
    return render_template('register.html', title='Register', form=form)


@paid_user.route('/download', methods=['GET'])
def download():
    form = DownloadRequestForm()
    return render_template('download.html', title='Download', form=form)


@paid_user.route('/processdownload', methods=['POST'])
def processdownload():
    form = DownloadRequestForm()
    if form.validate_on_submit():
        ytbvideo = form.ytbvideo.data
        ytblist = form.ytblist.data
        spotifylist = form.spotifylist.data
        to_return = 'ytbvideo:{} \nytblist:{} \nspotifylist:{}'.format(placeholder_linkprocessing(ytbvideo),
                                                                       placeholder_linkprocessing(ytblist),
                                                                       placeholder_linkprocessing(spotifylist))
        return jsonify({"text": to_return})
    else:
        return jsonify({"error": form.errors})


@paid_user.route('/test')
def test_celery_task():
    chain = (extract_spotify_playlist.s('0dRizWkhzplGjqvULihR72') | search_for_ytb_items_from_spotify_list.s()).apply_async()
    return Response(response=json.dumps({"uuid": chain.id}),
                    status=200,
                    mimetype='application/json')