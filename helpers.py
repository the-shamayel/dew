import os
from flask import session, jsonify
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        db_url = "postgresql://postgres:postgres@localhost:5432/postgres" # Default for local dev/testing
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    return conn

def login_required(f):
    @wraps(f)
    def lr(*args, **kwargs):
        if session.get("user_id") is None:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return lr

def apology(message, code=400):
    return jsonify({"error": message}), code

def tideman(event_id):
    conn = get_db_connection()
    cr = conn.cursor()

    # Get votes for the specific event
    cmd = "SELECT pref1, pref2, pref3 FROM votes WHERE event_id = %s"
    cr.execute(cmd, (event_id,))
    preferences = cr.fetchall()

    if not preferences:
        return None

    # Convert RealDictRow objects to tuples of values, handling potentially NULL preferences
    clean_preferences = []
    for pref in preferences:
        clean_pref = []
        if pref['pref1'] is not None:
            clean_pref.append(pref['pref1'])
        if pref['pref2'] is not None:
            clean_pref.append(pref['pref2'])
        if pref['pref3'] is not None:
            clean_pref.append(pref['pref3'])
        if clean_pref:
             clean_preferences.append(clean_pref)

    pairs = record_preferences(clean_preferences)
    if not pairs:
        return None

    locked_pairs = create_locked_pairs(pairs)
    winner_id = get_winner(locked_pairs)

    if winner_id is None:
        return None

    # Get winner's username
    kmd = "SELECT username FROM users WHERE id = %s"
    cr.execute(kmd, (winner_id,))
    winner = cr.fetchone()

    cr.close()
    conn.close()

    if winner:
        return winner['username']
    return None

def record_preferences(preferences):
    # Create a dictionary to store pairwise preferences
    pairs = {}
    for voter in preferences:
        n = len(voter)
        for i in range(n):
            for j in range(i + 1, n):
                pair = (voter[i], voter[j])
                pairs[pair] = pairs.get(pair, 0) + 1
    return pairs

def create_locked_pairs(pairs):
    # Create a list to store locked pairs
    locked_pairs = []
    # Sort pairs in descending order of strength
    sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
    for pair, strength in sorted_pairs:
        winner, loser = pair
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
    # Ensure all candidates mentioned in pairs are in indegrees
    candidates = set()
    for winner, loser in locked_pairs:
        candidates.add(winner)
        candidates.add(loser)

    indegrees = {candidate: 0 for candidate in candidates}
    # Update indegrees based on locked pairs
    for winner, loser in locked_pairs:
        indegrees[loser] += 1

    # Find the candidate with zero indegree (no incoming edges)
    winners = []
    for candidate, indegree in indegrees.items():
        if indegree == 0:
            winners.append(candidate)

    # For simplicity, returning the first winner if there's a tie,
    # though true Tideman should not have a cycle at the source
    if winners:
         return winners[0]
    return None
