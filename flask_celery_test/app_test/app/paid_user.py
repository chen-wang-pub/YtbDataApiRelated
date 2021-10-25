from flask import Blueprint, request, current_app, Response, json, render_template, flash, redirect, url_for
from app.forms import LoginForm

paid_user = Blueprint("paid_user", __name__)


@paid_user.route("/index")
def index():
    user = {'username': 'vip'}
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
    return render_template('index.html', title='Welcome', user=user, posts=posts)


@paid_user.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(form.username.data, form.remember_me.data))
        return redirect(url_for('paid_user.index'))
    return render_template('login.html', title='Sign In', form=form)