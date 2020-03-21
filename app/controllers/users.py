from flask import Blueprint, render_template

users_bp = Blueprint('users_bp', __name__,
                     template_folder='templates',
                     url_prefix='/users')

@users_bp.route('/<user>')
def list_user(user):
    print("The user searched for is: {}".format(user))
    # mocking out the data since the db isn't ready yet
    data = {
        "user": user
    }

    # if you import your neo4_db stuff here you could do
    # user_info = db.lookup_user(user)
    # data = {
    #     "user_info": user_info
    # }

    return render_template('user.html', **data)

@users_bp.route('/')
def list_users():
    # really you'd make a call to the db to get all users
    # users = db.all_users()

    # just mocking it out since the db isn't ready
    users = ['stroopC', 'data_day_life', 'crepeG', 'tunaprimo']
    data = {
        "users": users
    }
    return render_template('users.html', **data)
