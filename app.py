"""Movie Ticket Booking web app — Flask routes.

Data and booking logic live in models.py; markup lives in templates/ and
static/style.css. This module only wires HTTP requests to that logic.

Run:  pip install flask  &&  python app.py
Then open http://127.0.0.1:5050
"""
from flask import Flask, render_template, request, redirect, url_for, abort

import models

app = Flask(__name__)


def get_movie_or_404(movie_id, showtime):
    movie = models.MOVIES.get(movie_id)
    if not movie or showtime not in movie["showtimes"]:
        abort(404)
    return movie


@app.route("/")
def index():
    genres = sorted({movie["genre"] for movie in models.MOVIES.values()})
    return render_template("index.html", movies=models.MOVIES, genres=genres,
                            seats_remaining=models.seats_remaining,
                            low_seats_threshold=models.LOW_SEATS_THRESHOLD)


@app.route("/movie/<int:movie_id>/<showtime>")
def select_seats(movie_id, showtime):
    movie = get_movie_or_404(movie_id, showtime)
    booked = models.booked_seats_for(movie_id, showtime)
    return render_template(
        "seats.html", movie=movie, showtime=showtime,
        rows=models.ROWS, seats_per_row=models.SEATS_PER_ROW, booked=booked,
        price=models.SEAT_PRICE, movie_id=movie_id,
        left=models.seats_remaining(movie_id, showtime), total=models.TOTAL_SEATS,
    )


@app.route("/movie/<int:movie_id>/<showtime>/book", methods=["POST"])
def book(movie_id, showtime):
    movie = get_movie_or_404(movie_id, showtime)

    seats = [s for s in request.form.get("seats", "").split(",") if s]
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()

    if not seats or not name or not email:
        return "Missing seats, name or email. Go back and try again.", 400

    try:
        booking_id = models.create_booking(
            movie_id=movie_id, movie_title=movie["title"], showtime=showtime,
            seats=seats, name=name, email=email,
        )
    except models.SeatUnavailableError:
        return "Sorry, one or more of those seats were just booked. Go back and pick again.", 409

    return redirect(url_for("confirmation", booking_id=booking_id))


@app.route("/confirmation/<booking_id>")
def confirmation(booking_id):
    booking = models.BOOKINGS.get(booking_id)
    if not booking:
        abort(404)
    return render_template("confirmation.html", booking_id=booking_id, booking=booking)


@app.route("/my-bookings")
def my_bookings():
    email = request.args.get("email", "").strip()
    matches = models.find_bookings_by_email(email) if email else None
    return render_template("my_bookings.html", email=email, matches=matches)


@app.route("/booking/<booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    email = request.form.get("email", "")
    models.cancel_booking(booking_id)
    return redirect(url_for("my_bookings", email=email))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
