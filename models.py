"""In-memory data store and booking logic for the movie ticket booking app.

Keeps all movie/seat/booking data and the rules for mutating it (creating a
booking, cancelling one, checking availability) separate from the Flask
routes, which only handle HTTP request/response concerns.
"""
import uuid
from datetime import datetime

ROWS = ["A", "B", "C", "D", "E"]
SEATS_PER_ROW = 8
TOTAL_SEATS = len(ROWS) * SEATS_PER_ROW
SEAT_PRICE = 12.50
# Showtimes at or below this many free seats are flagged as "X left" on the listing page.
LOW_SEATS_THRESHOLD = 8

# Poster art comes from Lorem Picsum (free, no key needed); a CSS duotone tint
# per genre keeps the mismatched photos feeling like one poster set.
MOVIES = {
    1: {"title": "Galaxy Raiders", "genre": "Sci-Fi", "duration": "2h 15m",
        "showtimes": ["11:00 AM", "2:30 PM", "6:00 PM", "9:15 PM"],
        "poster": "1015", "tint": "rgba(56,132,255,.45)"},
    2: {"title": "The Last Detective", "genre": "Thriller", "duration": "1h 58m",
        "showtimes": ["12:00 PM", "3:15 PM", "7:00 PM"],
        "poster": "1025", "tint": "rgba(220,38,38,.45)"},
    3: {"title": "Love in Autumn", "genre": "Romance", "duration": "1h 45m",
        "showtimes": ["1:00 PM", "4:30 PM", "8:00 PM"],
        "poster": "1035", "tint": "rgba(236,72,153,.40)"},
    4: {"title": "Dragon's Peak", "genre": "Fantasy", "duration": "2h 30m",
        "showtimes": ["10:30 AM", "2:00 PM", "5:30 PM", "9:00 PM"],
        "poster": "1043", "tint": "rgba(34,197,94,.40)"},
    5: {"title": "Midnight Howl", "genre": "Horror", "duration": "1h 42m",
        "showtimes": ["9:30 PM", "11:45 PM"],
        "poster": "1050", "tint": "rgba(126,34,206,.45)"},
    6: {"title": "Office Chaos", "genre": "Comedy", "duration": "1h 50m",
        "showtimes": ["11:30 AM", "2:15 PM", "5:00 PM"],
        "poster": "1060", "tint": "rgba(245,158,11,.40)"},
}

# booked seats keyed by (movie_id, showtime) -> set of seat labels, e.g. "A1"
BOOKED_SEATS = {}
# confirmed bookings keyed by booking_id
BOOKINGS = {}


class SeatUnavailableError(Exception):
    """Raised when one or more requested seats are already booked."""


def booked_seats_for(movie_id, showtime):
    """Return the set of seat labels already booked for a showtime."""
    return BOOKED_SEATS.get((movie_id, showtime), set())


def seats_remaining(movie_id, showtime):
    return TOTAL_SEATS - len(booked_seats_for(movie_id, showtime))


def create_booking(movie_id, movie_title, showtime, seats, name, email):
    """Reserve the given seats and record a new booking. Raises
    SeatUnavailableError if any seat was booked in the meantime."""
    booked = BOOKED_SEATS.setdefault((movie_id, showtime), set())
    if any(s in booked for s in seats):
        raise SeatUnavailableError()

    booked.update(seats)
    booking_id = str(uuid.uuid4())[:8].upper()
    BOOKINGS[booking_id] = {
        "movie_id": movie_id, "movie": movie_title, "showtime": showtime, "seats": seats,
        "name": name, "email": email, "total": len(seats) * SEAT_PRICE,
        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    return booking_id


def find_bookings_by_email(email):
    return [
        (booking_id, booking) for booking_id, booking in BOOKINGS.items()
        if booking["email"].lower() == email.lower()
    ]


def cancel_booking(booking_id):
    """Remove a booking and free its seats. Returns the removed booking, or
    None if no booking existed with that id."""
    booking = BOOKINGS.pop(booking_id, None)
    if booking:
        key = (booking["movie_id"], booking["showtime"])
        BOOKED_SEATS.get(key, set()).difference_update(booking["seats"])
    return booking
