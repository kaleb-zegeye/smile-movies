import os
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Movie, User
from . import db
import requests

views = Blueprint('views', __name__)

TMDB_API_KEY = os.getenv('TMDB_API_KEY')

def get_recommendations(watched_movies, to_watch_movies):
    recommended_movies = []
    watched_movie_ids = {movie.tmdb_id for movie in watched_movies}
    to_watch_movie_ids = {movie.tmdb_id for movie in to_watch_movies}
    existing_movie_ids = watched_movie_ids.union(to_watch_movie_ids)

    # Fetch recommendations based on watched movies
    for movie in watched_movies:
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie.tmdb_id}/recommendations?api_key={TMDB_API_KEY}')
        if response.status_code == 200:
            data = response.json().get('results', [])
            recommended_movies.extend([m for m in data if m['id'] not in existing_movie_ids])

    # Fetch recommendations based on to-watch movies
    for movie in to_watch_movies:
        response = requests.get(f'https://api.themoviedb.org/3/movie/{movie.tmdb_id}/recommendations?api_key={TMDB_API_KEY}')
        if response.status_code == 200:
            data = response.json().get('results', [])
            recommended_movies.extend([m for m in data if m['id'] not in existing_movie_ids])

    # Remove duplicates and keep unique recommendations
    unique_recommendations = {movie['id']: movie for movie in recommended_movies}.values()

    # Ensure we have a large enough set of recommendations
    unique_recommendations = list(unique_recommendations)[:100]
    return unique_recommendations

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    watched_movies = Movie.query.filter_by(user_id=current_user.id, watched=True).all()
    to_watch_movies = Movie.query.filter_by(user_id=current_user.id, watched=False).all()
    recommended_movies = get_recommendations(watched_movies, to_watch_movies)

    return render_template("home.html", user=current_user, recommended_movies=recommended_movies)

@views.route('/add-movie', methods=['POST'])
@login_required
def add_movie():
    data = request.json
    movie_id = data.get('movie_id')
    title = data.get('title')
    cover_url = data.get('cover_url')
    watched = data.get('watched')

    if movie_id and title and cover_url is not None and watched is not None:
        existing_movie = Movie.query.filter_by(user_id=current_user.id, tmdb_id=movie_id).first()
        if existing_movie:
            return jsonify({'success': False, 'message': 'Movie already exists in your list.'})

        new_movie = Movie(tmdb_id=movie_id, title=title, cover_url=cover_url, watched=watched, user_id=current_user.id)
        db.session.add(new_movie)
        db.session.commit()

        # After adding the movie, fetch updated recommendations
        watched_movies = Movie.query.filter_by(user_id=current_user.id, watched=True).all()
        to_watch_movies = Movie.query.filter_by(user_id=current_user.id, watched=False).all()
        updated_recommendations = get_recommendations(watched_movies, to_watch_movies)

        return jsonify({'success': True, 'recommended_movies': updated_recommendations})

    return jsonify({'success': False})

@views.route('/delete-movie', methods=['POST'])
@login_required
def delete_movie():
    movie_id = request.json.get('movie_id')
    movie = Movie.query.get(movie_id)
    if movie and movie.user_id == current_user.id:
        db.session.delete(movie)
        db.session.commit()

        # After deleting the movie, fetch updated recommendations
        watched_movies = Movie.query.filter_by(user_id=current_user.id, watched=True).all()
        to_watch_movies = Movie.query.filter_by(user_id=current_user.id, watched=False).all()
        updated_recommendations = get_recommendations(watched_movies, to_watch_movies)

        return jsonify({'success': True, 'recommended_movies': updated_recommendations})
    return jsonify({'success': False})

@views.route('/watched')
@login_required
def watched():
    movies = Movie.query.filter_by(user_id=current_user.id, watched=True).all()
    return render_template("watched.html", movies=movies)

@views.route('/to-watch')
@login_required
def to_watch():
    movies = Movie.query.filter_by(user_id=current_user.id, watched=False).all()
    return render_template("to_watch.html", movies=movies)

@views.route('/movie/<int:movie_id>', methods=['GET'])
@login_required
def movie_details(movie_id):
    response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}')
    if response.status_code == 200:
        movie = response.json()
    else:
        movie = None
    return render_template("movie_details.html", movie=movie)

@views.route('/search-movie', methods=['POST'])
@login_required
def search_movie():
    query = request.json.get('query')
    if not query:
        return jsonify([])

    response = requests.get(f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}')
    if response.status_code == 200:
        movies = response.json().get('results', [])
        return jsonify(movies)
    else:
        return jsonify([])
