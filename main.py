from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////app/data.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/daulat/Fynd/fynd_imdb/data.db'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    popularity = db.Column(db.Float)
    director = db.Column(db.String(100))
    genre = db.Column(db.Text())
    imdb_score = db.Column(db.Float)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(email=data['email']).first()
        except:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):

    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'}), 401

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['email'] = user.email
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)

    return jsonify({'users' : output})

@app.route('/user/<email>', methods=['GET'])
@token_required
def get_one_user(current_user, email):

    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'}), 401

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    user_data = {}
    user_data['email'] = user.email
    user_data['name'] = user.name
    user_data['password'] = user.password
    user_data['admin'] = user.admin

    return jsonify({'user' : user_data})

@app.route('/user', methods=['POST'])
@token_required
def create_user(current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'}), 401
    data = request.get_json()

    user = User.query.filter_by(email=data["email"]).first()
    if user:
        return jsonify({'message': 'User is already exits!'})


    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(email=data["email"], name=data['name'], password=hashed_password, admin=data['admin'])
    db.session.add(new_user)
    # db.create_all()
    db.session.commit()

    return jsonify({'message' : 'New user created!'})

@app.route('/user/<email>', methods=['PUT'])
@token_required
def promote_user(current_user, email):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'}), 401

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    user.admin = True
    db.session.commit()

    return jsonify({'message' : 'The user has been promoted!'})

@app.route('/user/<email>', methods=['DELETE'])
@token_required
def delete_user(current_user, email):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'}), 401

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message' : 'The user has been deleted!'})

@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(email=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'email' : user.email, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

        return jsonify({'token' : token.decode("utf-8")})

    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

@app.route('/movies', methods=['GET'])
@token_required
def get_all_movies(current_user):
    movies = Movie.query.all()

    output = []

    for movie in movies:
        movie_data = {}
        movie_data['name'] = movie.name
        movie_data['99popularity'] = movie.popularity
        movie_data['director'] = movie.director
        movie_data['genre'] = movie.genre.split(",")
        movie_data['imdb_score'] = movie.imdb_score
        output.append(movie_data)

    return jsonify({'movie_data' : output})

'''
Search the movie here 
'''
@app.route('/search-movie/<movie>', methods=['GET'])
@token_required
def get_one_movie(current_user, movie):
    # Movie.__table__.create(db.engine)
    search = "%{}%".format(movie)
    movies = Movie.query.filter(Movie.name.like(search)).all()

    if not movies:
        return jsonify({'message' : 'No Movie found!'})
    movie_data_list = []
    for movie in movies:
        movie_data = {}
        movie_data['name'] = movie.name
        movie_data['99popularity'] = movie.popularity
        movie_data['director'] = movie.director
        movie_data['genre'] = movie.genre.split(",")
        movie_data['imdb_score'] = movie.imdb_score
        movie_data_list.append(movie_data)

    return jsonify(movie_data_list)

@app.route('/movie', methods=['POST'])
@token_required
def add_movie(current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'}), 401
    list_data = request.get_json()
    if not isinstance(list_data, list):
        list_data = [list_data]
    for data in list_data:
        new_movie = Movie(name=data["name"], popularity=data['99popularity'], director=data["director"],
                          genre=",".join(data), imdb_score=data["imdb_score"])
        db.session.add(new_movie)
    db.session.commit()

    return jsonify({'message' : "Movie Added!"})

@app.route('/movie/<movie_name>', methods=['PUT'])
@token_required
def edit_movie(current_user, movie_name):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'}), 401

    data = request.get_json()
    movie = Movie.query.filter_by(name=movie_name).first()

    if not movie:
        return jsonify({'message' : 'No movie found!'})

    movie.name = data["name"]
    movie.popularity = data["99popularity"]
    movie.director = data["director"]
    movie.genre = ",".join(data["genre"])
    movie.imdb_score = data["imdb_score"]

    db.session.commit()

    return jsonify({'message' : 'Movie item has been updated!'})

@app.route('/movie/<movie_name>', methods=['DELETE'])
@token_required
def delete_movie(current_user, movie_name):
    if not current_user.admin:
        return jsonify({'message' : 'Cannot perform that function!'}), 401

    movie = Movie.query.filter_by(name=movie_name).first()

    if not movie:
        return jsonify({'message' : 'No movie found!'})

    db.session.delete(movie)
    db.session.commit()

    return jsonify({'message' : 'Movie deleted!'})

if __name__ == '__main__':
    app.run(debug=True)