from flask import session, redirect, render_template
from functools import wraps
from jsonify import convert

import sqlite3

def login_required(f):
    @wraps(f)
    def lr(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return lr

def apology(message, code=400):
    def escape(s):
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top = code, bottom = escape(message)), code

def tideman(var):
    db = sqlite3.connect("db.db", check_same_thread = False)
    cr = db.cursor()
    cmd = f"SELECT * FROM {var}"
    preferences = cr.execute(cmd)
    pairs = record_preferences(preferences)
    locked_pairs = create_locked_pairs(pairs)
    winners = get_winner(locked_pairs)
    kmd = f"SELECT username FROM users WHERE id = {winners[0]}"
    wr = cr.execute(kmd)
    winner = wr.fetchone()
    return winner[0]

def record_preferences(preferences):
    # Create a dictionary to store pairwise preferences
    pairs = {}
    for voter in preferences:
        for i in range(1, 2):
            for j in range(i + 1, 3):
                pair = (voter[i], voter[j])
                pairs[pair] = pairs.get(pair, 0) + 1
    return pairs

def create_locked_pairs(pairs):
    # Create a list to store locked pairs
    locked_pairs = []
    # Sort pairs in descending order of strength
    sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
    for winner, loser in sorted_pairs:
        if not has_cycle(locked_pairs, winner, loser):
            locked_pairs.append((winner, loser))
    return locked_pairs

def has_cycle(locked_pairs, winner, loser):
    # Check for cycles using recursion
    visited = set()
    return has_path(locked_pairs, loser, winner, visited)

def has_path(locked_pairs, start, end, visited):
    if start == end:
        return True
    visited.add(start)
    for pair in locked_pairs:
        if pair[0] == start and pair[1] not in visited:
            if has_path(locked_pairs, pair[1], end, visited.copy()):
                return True
    return False

def get_winner(locked_pairs):
    # Create a dictionary to store indegrees (number of incoming edges)
    indegrees = {candidate: 0 for pair in locked_pairs for candidate in pair}
    # Update indegrees based on locked pairs
    for winner, loser in locked_pairs:
        indegrees[loser] += 1
    # Find the candidate with zero indegree (no incoming edges)
    for candidate, indegree in indegrees.items():
        if indegree == 0:
            return candidate
