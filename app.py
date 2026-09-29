"""Movie Ticket Booking web app — single-file Flask demo.

Run:  pip install flask  &&  python app.py
Then open http://127.0.0.1:5000
"""
import uuid
from datetime import datetime

from flask import Flask, render_template_string, request, redirect, url_for, abort

app = Flask(__name__)

ROWS = ["A", "B", "C", "D", "E"]
SEATS_PER_ROW = 8
SEAT_PRICE = 350

# In-memory "database"
MOVIES = {
    1: {"title": "Galaxy Raiders", "genre": "Sci-Fi", "duration": "2h 15m",
        "showtimes": ["11:00 AM", "2:30 PM", "6:00 PM", "9:15 PM"], "poster": "🚀"},
    2: {"title": "The Last Detective", "genre": "Thriller", "duration": "1h 58m",
        "showtimes": ["12:00 PM", "3:15 PM", "7:00 PM"], "poster": "🕵️"},
    3: {"title": "Love in Autumn", "genre": "Romance", "duration": "1h 45m",
        "showtimes": ["1:00 PM", "4:30 PM", "8:00 PM"], "poster": "🍁"},
    4: {"title": "Dragon's Peak", "genre": "Fantasy/Adventure", "duration": "2h 30m",
        "showtimes": ["10:30 AM", "2:00 PM", "5:30 PM", "9:00 PM"], "poster": "🐉"},
}

# booked seats keyed by (movie_id, showtime) -> set of seat labels, e.g. "A1"
BOOKED_SEATS = {}
# confirmed bookings keyed by booking_id
BOOKINGS = {}


def all_seats():
    return [f"{r}{n}" for r in ROWS for n in range(1, SEATS_PER_ROW + 1)]


BASE_STYLE = """
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #14141c; color: #eee; margin: 0; }
  header { background: #1f1f2e; padding: 16px 24px; }
  header a { color: #fff; text-decoration: none; font-size: 20px; font-weight: bold; }
  .container { max-width: 900px; margin: 0 auto; padding: 24px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
  .card { background: #232336; border-radius: 10px; padding: 16px; transition: transform .15s; }
  .card:hover { transform: translateY(-4px); }
  .poster { font-size: 48px; text-align: center; }
  .card h3 { margin: 8px 0 4px; }
  .meta { color: #aaa; font-size: 13px; margin-bottom: 10px; }
  .btn { display: inline-block; background: #e63946; color: #fff; padding: 8px 14px;
         border-radius: 6px; text-decoration: none; font-size: 14px; border: none; cursor: pointer; }
  .btn:hover { background: #c72d3a; }
  .showtimes a { margin: 3px 4px 0 0; }
  .seat-map { display: inline-block; margin: 20px 0; }
  .row { display: flex; align-items: center; margin-bottom: 6px; }
  .row-label { width: 20px; color: #888; }
  .seat { width: 30px; height: 30px; margin: 2px; border-radius: 4px 4px 0 0;
          display: flex; align-items: center; justify-content: center; font-size: 11px;
          cursor: pointer; user-select: none; background: #3a3a52; }
  .seat.booked { background: #555; color: #888; cursor: not-allowed; }
  .seat.selected { background: #e63946; }
  .screen { background: #444; height: 8px; border-radius: 50%; margin: 0 20px 24px 40px; }
  .legend span { display: inline-block; width: 14px; height: 14px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }
  form.booking-form { background: #232336; padding: 16px; border-radius: 10px; margin-top: 16px; }
  input[type=text], input[type=email] { width: 100%; padding: 8px; margin: 6px 0 12px;
        border-radius: 6px; border: 1px solid #444; background: #14141c; color: #eee; }
  .summary { background: #1f1f2e; padding: 14px; border-radius: 8px; margin-bottom: 16px; }
  .ticket { background: #232336; padding: 24px; border-radius: 10px; text-align: center; }
  .ticket h2 { color: #4caf50; }
</style>
"""


@app.route("/")
def index():
    cards = ""
    for mid, m in MOVIES.items():
        showtimes_html = "".join(
            f'<a class="btn" href="{url_for("select_seats", movie_id=mid, showtime=st)}">{st}</a> '
            for st in m["showtimes"]
        )
        cards += f"""
        <div class="card">
          <div class="poster">{m['poster']}</div>
          <h3>{m['title']}</h3>
          <div class="meta">{m['genre']} • {m['duration']}</div>
          <div class="showtimes">{showtimes_html}</div>
        </div>"""
    return render_template_string(BASE_STYLE + """
    <header><a href="/">🎬 CineBook</a></header>
    <div class="container">
      <h2>Now Showing</h2>
      <div class="grid">{{ cards|safe }}</div>
    </div>
    """, cards=cards)


@app.route("/movie/<int:movie_id>/<showtime>")
def select_seats(movie_id, showtime):
    movie = MOVIES.get(movie_id)
    if not movie or showtime not in movie["showtimes"]:
        abort(404)

    booked = BOOKED_SEATS.get((movie_id, showtime), set())
    rows_html = ""
    for r in ROWS:
        seats_html = ""
        for n in range(1, SEATS_PER_ROW + 1):
            label = f"{r}{n}"
            cls = "seat booked" if label in booked else "seat"
            seats_html += f'<div class="{cls}" data-seat="{label}" onclick="toggleSeat(this)">{label}</div>'
        rows_html += f'<div class="row"><div class="row-label">{r}</div>{seats_html}</div>'

    return render_template_string(BASE_STYLE + """
    <header><a href="/">🎬 CineBook</a></header>
    <div class="container">
      <h2>{{ movie.title }} — {{ showtime }}</h2>
      <p class="meta">Price per seat: Rs. {{ price }}</p>
      <div class="screen"></div>
      <div class="seat-map">{{ rows_html|safe }}</div>
      <div class="legend">
        <span style="background:#3a3a52"></span>Available &nbsp;
        <span style="background:#e63946"></span>Selected &nbsp;
        <span style="background:#555"></span>Booked
      </div>

      <form class="booking-form" method="POST" action="{{ url_for('book', movie_id=movie_id, showtime=showtime) }}">
        <div class="summary">Selected seats: <span id="seatList">none</span> —
          Total: Rs. <span id="total">0</span></div>
        <input type="hidden" name="seats" id="seatsInput">
        <label>Full name</label>
        <input type="text" name="name" required>
        <label>Email</label>
        <input type="email" name="email" required>
        <button class="btn" type="submit">Confirm Booking</button>
      </form>
    </div>

    <script>
      const price = {{ price }};
      let selected = [];
      function toggleSeat(el) {
        if (el.classList.contains('booked')) return;
        const seat = el.dataset.seat;
        if (el.classList.toggle('selected')) {
          selected.push(seat);
        } else {
          selected = selected.filter(s => s !== seat);
        }
        document.getElementById('seatList').textContent = selected.length ? selected.join(', ') : 'none';
        document.getElementById('total').textContent = selected.length * price;
        document.getElementById('seatsInput').value = selected.join(',');
      }
    </script>
    """, movie=movie, showtime=showtime, rows_html=rows_html, price=SEAT_PRICE,
         movie_id=movie_id)


@app.route("/movie/<int:movie_id>/<showtime>/book", methods=["POST"])
def book(movie_id, showtime):
    movie = MOVIES.get(movie_id)
    if not movie or showtime not in movie["showtimes"]:
        abort(404)

    seats = [s for s in request.form.get("seats", "").split(",") if s]
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()

    if not seats or not name or not email:
        return "Missing seats, name or email. Go back and try again.", 400

    booked = BOOKED_SEATS.setdefault((movie_id, showtime), set())
    if any(s in booked for s in seats):
        return "Sorry, one or more of those seats were just booked. Go back and pick again.", 409

    booked.update(seats)
    booking_id = str(uuid.uuid4())[:8].upper()
    BOOKINGS[booking_id] = {
        "movie": movie["title"], "showtime": showtime, "seats": seats,
        "name": name, "email": email, "total": len(seats) * SEAT_PRICE,
        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    return redirect(url_for("confirmation", booking_id=booking_id))


@app.route("/confirmation/<booking_id>")
def confirmation(booking_id):
    booking = BOOKINGS.get(booking_id)
    if not booking:
        abort(404)
    return render_template_string(BASE_STYLE + """
    <header><a href="/">🎬 CineBook</a></header>
    <div class="container">
      <div class="ticket">
        <h2>✅ Booking Confirmed</h2>
        <p>Booking ID: <b>{{ booking_id }}</b></p>
        <p>{{ b.movie }} — {{ b.showtime }}</p>
        <p>Seats: {{ b.seats|join(', ') }}</p>
        <p>Total paid: Rs. {{ b.total }}</p>
        <p>{{ b.name }} • {{ b.email }}</p>
        <p class="meta">Booked at {{ b.booked_at }}</p>
        <a class="btn" href="/">Book another movie</a>
      </div>
    </div>
    """, booking_id=booking_id, b=booking)


if __name__ == "__main__":
    app.run(debug=True)
