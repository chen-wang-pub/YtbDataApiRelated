import requests
import os
from flask import Blueprint, request, current_app, Response, json, render_template, flash, redirect, url_for, jsonify, send_file, after_this_request
from app.forms import LoginForm, RegistrationForm, DownloadRequestForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User
from app.factory import db
from app.tasks import extract_spotify_playlist, search_for_ytb_items_from_spotify_list, extract_ytb_channel_videos, check_queued_list, extracted_data_processor
from app.const import update_url, read_url, write_url, delete_url, TEMP_DIR_LOC
from app.utils.db_document_related import refresh_status
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


@paid_user.route('/spotify_list')
def spotify_playlist():
    spotify_playlist_id = request.args.get('id', default='0dRizWkhzplGjqvULihR72', type=str)
    chain = (extract_spotify_playlist.s(spotify_playlist_id) | search_for_ytb_items_from_spotify_list.s() | extracted_data_processor.s() | check_queued_list.s()).apply_async()

    return Response(response=json.dumps({"uuid": chain.id}),
                    status=200,
                    mimetype='application/json')


@paid_user.route('/ytb_channel')
def ytb_channel_videos():
    ytb_channel_id = request.args.get('id', default='/UCTjkEBD5wXS6VkmmjnLIFcg', type=str)
    task = (extract_ytb_channel_videos.s(ytb_channel_id) | extracted_data_processor.s() | check_queued_list.s()).apply_async()#extract_ytb_channel_videos.apply_async(args=[ytb_channel_id])
    return Response(response=json.dumps({"uuid": task.id}),
                    status=200,
                    mimetype='application/json')


@paid_user.route('/retrieve_file/<item_id>')
def retrieve_file(item_id):
    current_app.logger.info('uuid from route is {}'.format(item_id))

    read_payload = {'read_filter': {'item_id': item_id}}
    response = requests.post(url=read_url, data=json.dumps(read_payload),
                                         headers={'content-type': 'application/json'})
    doc_list = response.json()['response']
    if len(doc_list) < 1:
        return Response(response=json.dumps({"error": "No record found for {}".format(item_id)}),
                        status=200,
                        mimetype='application/json')
    doc = doc_list[0]

    if doc['status'] == 'error':
        return Response(response=json.dumps({"error": "Please queue request for {} again".format(item_id)}),
                        status=200,
                        mimetype='application/json')
    elif doc['status'] == 'queued':
        return Response(response=json.dumps({"error": "Please try download {} later".format(item_id)}),
                        status=200,
                        mimetype='application/json')
    elif doc['status'] == 'downloading':
        return Response(response=json.dumps({"error": "Please try download {} later".format(item_id)}),
                        status=200,
                        mimetype='application/json')
    elif doc['status'] == 'ready':
        file_name = '{}.mp3'.format(doc['title'])
        item_dir = os.path.join(TEMP_DIR_LOC, item_id)
        item_path = os.path.join(item_dir, file_name)
        if os.path.isfile(item_path):
            refresh_status(read_payload, read_url, update_url)  # Refresh the timer so that it extends the total time whenever someone queued it
            """data = {'update_filter': {'item_id': item_id},
                    'update_aggregation': [{'$set': {'status': 'transferring'}}]}
            response = requests.put(url=update_url, data=json.dumps(data),
                                    headers={'content-type': 'application/json'})
            response_dict = json.loads(response.content)
            current_app.logger.debug('update status is {} for item {} when transferring'.format(
                response_dict['update_status'], item_id))"""
            response = send_file(item_path, as_attachment=True, download_name=file_name)
            @after_this_request
            def add_close_action(response):
                current_app.logger.info('Item {} transferred successfully'.format(item_id))
                """data = {'update_filter': {'item_id': item_id},
                            'update_aggregation': [{'$set': {'status': 'ready'}}]}
                requests.put(url=update_url, data=json.dumps(data),
                                            headers={'content-type': 'application/json'})"""
                return response

            return response
        else:
            current_app.logger.error('file not found for {} when transferring item'.format(item_id))
            return Response(response=json.dumps({"error": "file not found for {} when transferring item".format(item_id)}),
                            status=200,
                            mimetype='application/json')
    return Response(response=json.dumps({"error": "Unknow error when processing request for {}".format(item_id)}),
                    status=200,
                    mimetype='application/json')

