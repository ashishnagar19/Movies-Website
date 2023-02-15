from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import requests
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///top-10-movies-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
movies_api_key = os.environ.get('API_KEY')

with app.app_context():
    class Movies(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), unique=True, nullable=False)
        rating = db.Column(db.Float, nullable=False)
        year = db.Column(db.Integer, nullable=False)
        description = db.Column(db.String(1000), nullable=False)
        ranking = db.Column(db.Integer, nullable=False)
        review = db.Column(db.String(1000), nullable=False)
        img_url = db.Column(db.String(1000), nullable=False)
    db.create_all()

    @app.route("/")
    def home():
        all_movies = db.session.query(Movies).order_by(Movies.rating).all()
        for i in range(len(all_movies)):
            # This line gives each movie a new ranking reversed from their order in all_movies
            all_movies[i].ranking = len(all_movies) - i
        db.session.commit()
        return render_template("index.html", movies=all_movies)

    class AddMovieForm(FlaskForm):
        movie_name = StringField("Movie Title")
        submit = SubmitField("Done")
    @app.route("/add", methods=['GET', 'POST'])
    def add():
        form = AddMovieForm()
        if form.validate_on_submit():
            movie_title = form.movie_name.data
            response = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={movies_api_key}&query={movie_title}")
            data = response.json()["results"]
            return render_template("select.html", options=data)

        return render_template("add.html", form=form)


#
    class RateMovieForm(FlaskForm):
        rating = StringField("Your Rating Out of 10 e.g. 7.5")
        review = StringField("Your Review")
        submit = SubmitField("Done")

    @app.route("/edit", methods=['GET', 'POST'])
    def edit():
        form = RateMovieForm()
        movie_id = request.args.get("id")
        movie = db.session.query(Movies).get(movie_id)
        if form.validate_on_submit():
            movie.rating = float(form.rating.data)
            movie.review = form.review.data
            db.session.commit()
            return redirect(url_for('home'))
        return render_template("edit.html", movie=movie, form=form)

    @app.route("/delete")
    def delete():
        movie_id = request.args.get('id')

        # DELETE A RECORD BY ID
        movie_to_delete = db.session.query(Movies).get(movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
        return redirect(url_for('home'))

    @app.route("/find")
    def find_movie():
        movie_api_id = request.args.get('id')
        if movie_api_id:
            response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_api_id}?api_key={movies_api_key}")
            data = response.json()
            new_movie = Movies(
                title=data["original_title"],
                rating=8,
                year=data["release_date"].split("-")[0],
                description=data["overview"],
                ranking=8,
                review="NONE",
                img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}"

            )
            db.session.add(new_movie)
            db.session.commit()
            return redirect(url_for('edit', id=new_movie.id))



if __name__ == '__main__':
    app.run(debug=True)
