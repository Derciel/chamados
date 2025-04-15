from flask import Blueprint, render_template

spotify_bp = Blueprint('spotify_bp', __name__)

@spotify_bp.route('/spotify')
def spotify():
    return render_template('spotify.html')
