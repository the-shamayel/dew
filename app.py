import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor

from flask import Flask, request, jsonify, session, send_from_directory
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, apology, tideman, get_db_connection

app = Flask(__name__, static_folder='client/dist', static_url_path='/')
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def afreq(response):
    response.headers["Pragma"] = "no-cache"
    response.headers["Cache-control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    return response

@app.route("/api/register", methods=["POST"])
def register():
    """Register user"""
    data = request.get_json()
    name = data.get("username")
    password = data.get("password")
    confirm = data.get("confirmation")

    if not name or not password or not confirm:
        return apology("Must provide username, password, and confirmation", 400)
    if password != confirm:
        return apology("Passwords do not match", 400)

    hash = generate_password_hash(password)
    
    conn = get_db_connection()
    cr = conn.cursor()

    cr.execute("SELECT * FROM users WHERE username = %s", (name,))
    rw = cr.fetchone()

    if not rw:
        try:
            cr.execute("INSERT INTO users (username, hash) VALUES (%s, %s) RETURNING id", (name, hash))
            new_user = cr.fetchone()
            conn.commit()

            session["logged_in"] = True
            session["user_id"] = new_user["id"]
            session["events"] = ""
            return jsonify({"message": "Successfully registered", "user": {"id": new_user["id"], "username": name}}), 201
        except Exception as e:
            conn.rollback()
            return apology("Something went wrong during registration", 500)
        finally:
            cr.close()
            conn.close()
    else:
        cr.close()
        conn.close()
        return apology("Username already taken", 409)

@app.route("/api/login", methods=["POST"])
def login():
    """Log user in"""
    session.clear()
    data = request.get_json()

    nm = data.get("username")
    password = data.get("password")

    if not nm:
        return apology("Must provide username", 400)
    elif not password:
        return apology("Must provide password", 400)

    conn = get_db_connection()
    cr = conn.cursor()

    cr.execute("SELECT * FROM users WHERE username = %s", (nm,))
    rw = cr.fetchone()
    cr.close()
    conn.close()

    if not rw:
        return apology("User not found", 403)
    if not check_password_hash(rw["hash"], password):
        return apology("Passwords don't match", 403)
        
    session["user_id"] = rw["id"]
    session["events"] = ""
    return jsonify({"message": "Successfully logged in", "user": {"id": rw["id"], "username": nm}}), 200

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@app.route("/api/me", methods=["GET"])
@login_required
def get_current_user():
    user_id = session.get("user_id")
    conn = get_db_connection()
    cr = conn.cursor()
    cr.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
    user = cr.fetchone()
    cr.close()
    conn.close()

    if user:
        return jsonify({"user": {"id": user["id"], "username": user["username"]}}), 200
    return apology("User not found", 404)

@app.route("/api/events", methods=["GET"])
def get_events():
    conn = get_db_connection()
    cr = conn.cursor()
    cr.execute("SELECT id, name, TO_CHAR(date, 'YYYY-MM-DD') as date FROM events")
    events_list = cr.fetchall()
    cr.close()
    conn.close()
    return jsonify({"events": events_list}), 200

@app.route("/api/events", methods=["POST"])
@login_required
def create_event():
    data = request.get_json()
    en = data.get("eventName")
    ps = data.get("password")

    if not en or not ps:
        return apology("Must provide eventName and password", 400)

    hash = generate_password_hash(ps)
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    conn = get_db_connection()
    cr = conn.cursor()
    try:
        cr.execute("INSERT INTO events (name, hash, date) VALUES (%s, %s, %s) RETURNING id", (en, hash, date))
        new_event = cr.fetchone()
        conn.commit()
        return jsonify({"message": "Event created", "event": {"id": new_event["id"], "name": en, "date": date}}), 201
    except Exception as e:
        conn.rollback()
        return apology("Event name likely already exists", 409)
    finally:
        cr.close()
        conn.close()

@app.route("/api/dew/<int:event_id>/join", methods=["POST"])
@login_required
def join_event(event_id):
    data = request.get_json()
    ps = data.get("password")
    uid = session["user_id"]

    if not ps:
        return apology("Must provide event password", 400)

    conn = get_db_connection()
    cr = conn.cursor()

    cr.execute("SELECT hash FROM events WHERE id = %s", (event_id,))
    ev = cr.fetchone()

    if not ev:
        cr.close()
        conn.close()
        return apology("Event not found", 404)

    if check_password_hash(ev["hash"], ps):
        try:
            cr.execute("INSERT INTO event_participants (event_id, user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (event_id, uid))
            conn.commit()
            session["events"] = str(event_id)
            return jsonify({"message": "Successfully joined event"}), 200
        except Exception as e:
            conn.rollback()
            return apology("Failed to join event", 500)
        finally:
            cr.close()
            conn.close()
    else:
        cr.close()
        conn.close()
        return apology("Passwords don't match", 403)

@app.route("/api/dew/<int:event_id>", methods=["GET"])
@login_required
def get_event_details(event_id):
    if session.get("events") != str(event_id):
        return apology("Not joined to this event", 403)

    conn = get_db_connection()
    cr = conn.cursor()

    cr.execute("SELECT name FROM events WHERE id = %s", (event_id,))
    ev = cr.fetchone()
    if not ev:
        cr.close()
        conn.close()
        return apology("Event not found", 404)
        
    cr.execute("""
        SELECT u.id, u.username
        FROM event_participants ep
        JOIN users u ON ep.user_id = u.id
        WHERE ep.event_id = %s
    """, (event_id,))
    participants = cr.fetchall()

    cr.execute("SELECT * FROM votes WHERE event_id = %s AND user_id = %s", (event_id, session["user_id"]))
    has_voted = cr.fetchone() is not None

    cr.close()
    conn.close()

    return jsonify({
        "event": {"id": event_id, "name": ev["name"]},
        "participants": participants,
        "has_voted": has_voted
    }), 200

@app.route("/api/dew/<int:event_id>/vote", methods=["POST"])
@login_required
def vote(event_id):
    if session.get("events") != str(event_id):
        return apology("Not joined to this event", 403)

    data = request.get_json()
    prf1 = data.get("select1")
    prf2 = data.get("select2")
    prf3 = data.get("select3")

    if not all([prf1, prf2, prf3]):
        return apology("Must provide 3 preferences", 400)

    if prf1 == prf2 or prf2 == prf3 or prf3 == prf1:
        return apology("Select distinct candidates", 400)

    uid = session["user_id"]

    conn = get_db_connection()
    cr = conn.cursor()
    
    try:
        cr.execute("""
            INSERT INTO votes (event_id, user_id, pref1, pref2, pref3)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (event_id, user_id)
            DO UPDATE SET pref1 = EXCLUDED.pref1, pref2 = EXCLUDED.pref2, pref3 = EXCLUDED.pref3
        """, (event_id, uid, prf1, prf2, prf3))
        conn.commit()
        return jsonify({"message": "Successfully voted"}), 200
    except Exception as e:
        conn.rollback()
        return apology("Failed to cast vote", 500)
    finally:
        cr.close()
        conn.close()

@app.route("/api/result/<int:event_id>", methods=["GET"])
@login_required
def get_result(event_id):
    conn = get_db_connection()
    cr = conn.cursor()
    cr.execute("SELECT name FROM events WHERE id = %s", (event_id,))
    ev = cr.fetchone()
    cr.close()
    conn.close()

    if not ev:
        return apology("Event not found", 404)

    winner = tideman(event_id)
    return jsonify({
        "event_name": ev["name"],
        "winner": winner
    }), 200

# Catch-all route to serve the React app
@app.route("/", defaults={'path': ''})
@app.route("/<path:path>")
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
