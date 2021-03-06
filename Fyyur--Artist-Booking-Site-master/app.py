#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='venue', lazy=True)

    

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show', backref='artist', lazy=True)



class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  areas = Venue.query.distinct('city', 'state').order_by('state').all()
  for area in areas:
      area.venues = Venue.query.filter_by(city=area.city, state=area.state)
  return render_template('pages/venues.html', areas=areas);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  data = []
  response = {}

  search_term = request.form.get('search_term')
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

  for venue in venues:
      v = {}
      v['id'] = venue.id
      v['name'] = venue.name
      data.append(v)

  response['count'] = len(data)
  response['data'] = data

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  shows = Show.query.filter_by(venue_id=venue_id).all()
  pastShows = []
  upcomingShows = []

  for show in shows:
      date = datetime.strptime(show.start_time,'%Y-%m-%d %H:%M:%S')

      if date < datetime.now():
        pastShows.append({
            "artist_id": Artist.query.filter_by(id=show.artist_id).first().id,
            "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
            "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
            "start_time": show.start_time
        })
      if date > datetime.now():
        upcomingShows.append({
            "artist_id": Artist.query.filter_by(id=show.artist_id).first().id,
            "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
            "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
            "start_time": show.start_time
        })

  data = {
      "id": venue.id,
      "name": venue.name,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "image_link": venue.image_link,
      "website": venue.website,
      "genres": venue.genres,
      "facebook_link": venue.facebook_link,
      "seeking_description": venue.seeking_description,
      "past_shows": pastShows,
      "past_shows_count": len(pastShows),
      "upcoming_shows": upcomingShows,
      "upcoming_shows_count": len(upcomingShows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  body = {}
  # print(request.form)
  # print(request.form.get('name'))
  # print(dict(request.form))
  try:
      # print(request.form['name'])
      # print(dict(request.form))
      # print(request.form.get('name'))
      venue = Venue(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        address = request.form['address'],
        phone = request.form['phone'],
        genres = request.form.getlist('genres'),
        facebook_link = request.form['facebook_link'],
        image_link = request.form['image_link'],
        website = request.form['website'],
        seeking_description = request.form['seeking_description']
      )

      db.session.add(venue)
      db.session.commit()

      body['name'] = request.form['name']
      body['city'] = request.form['city']
      body['state'] = request.form['state']
      body['address'] = request.form['address']
      body['phone'] = request.form['phone']
      body['genres'] = request.form.getlist('genres')
      body['facebook_link'] = request.form['facebook_link']
      body['image_link'] = request.form['image_link']
      body['website'] = request.form['website']
      body['seeking_description'] = request.form['seeking_description']
  except Exception as e:
      # print('\n\nFEHLERMELDUNG:\n{}\n'.format(e))
      # print(request.get_json())
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  if error:
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

      # abort(400)
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      return render_template('pages/home.html')
  else:
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
      return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  return render_template('pages/artists.html', artists=Artist.query.all())

@app.route('/artists/search', methods=['POST'])
def search_artists():
  data = []
  response = {}

  search_term = request.form.get('search_term')
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()

  for artist in artists:
      a = {}
      a['id'] = artist.id
      a['name'] = artist.name
      data.append(a)

  response['count'] = len(data)
  response['data'] = data

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  shows = Show.query.filter_by(artist_id=artist_id).all()
  pastShows = []
  upcomingShows = []

  for show in shows:
      date = datetime.strptime(show.start_time,'%Y-%m-%d %H:%M:%S')

      if date < datetime.now():
        pastShows.append({
            "venue_id": Venue.query.filter_by(id=show.venue_id).first().id,
            "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
            "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
            "start_time": show.start_time
        })
      if date > datetime.now():
        upcomingShows.append({
            "venue_id": Venue.query.filter_by(id=show.venue_id).first().id,
            "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
            "venue_image_link": Venue.query.filter_by(id=show.venue_id).first().image_link,
            "start_time": show.start_time
        })

  data = {
      "id": artist.id,
      "name": artist.name,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "image_link": artist.image_link,
      "website": artist.website,
      "genres": artist.genres,
      "facebook_link": artist.facebook_link,
      "seeking_description": artist.seeking_description,
      "past_shows": pastShows,
      "past_shows_count": len(pastShows),
      "upcoming_shows": upcomingShows,
      "upcoming_shows_count": len(upcomingShows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  body = {}

  try:
      artist = Artist(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        phone = request.form['phone'],
        image_link = request.form['image_link'],
        genres = request.form.getlist('genres'),
        website = request.form['website'],
        facebook_link = request.form['facebook_link'],
        # seeking_venue = request.form['seeking_venue'],
        seeking_description = request.form['seeking_description']
      )

      db.session.add(artist)
      db.session.commit()

      body['name'] = request.form['name']
      body['city'] = request.form['city']
      body['state'] = request.form['state']
      body['phone'] = request.form['phone']
      body['image_link'] = request.form['image_link']
      body['genres'] = request.form.getlist('genres')
      body['website'] = request.form['website']
      body['facebook_link'] = request.form['facebook_link']
      # body['seeking_venue'] = request.form['seeking_venue']
      body['seeking_description'] = request.form['seeking_description']
  except Exception as e:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      return render_template('pages/home.html')
  else:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
      return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  data = []
  for show in shows:
      show = {
          "venue_id": show.venue_id,
          "venue_name": db.session.query(Venue.name).filter_by(id=show.venue_id).first()[0],
          "artist_id": show.artist_id,
          "artist_name": db.session.query(Artist.name).filter_by(id=show.artist_id).first()[0],
          "artist_image_link": db.session.query(Artist.image_link).filter_by(id=show.artist_id).first()[0],
          "start_time": show.start_time
      }
      data.append(show)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  body = {}

  try:
      show = Show(
        artist_id = request.form['artist_id'],
        venue_id = request.form['venue_id'],
        start_time = request.form['start_time'],
      )

      db.session.add(show)
      db.session.commit()

      body['artist_id'] = request.form['artist_id']
      body['venue_id'] = request.form['venue_id']
      body['start_time'] = request.form['start_time']
  except Exception as e:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  if error:
      # on unsuccessful db insert, flash an error
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred. Show could not be listed.')
      return render_template('pages/home.html')
  else:
      # on successful db insert, flash success
      flash('Show was successfully listed!')
      return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
