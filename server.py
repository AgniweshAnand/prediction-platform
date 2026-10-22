import csv
import os
import random
import threading
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)

SOURCE_CSV = "sports_betting_predictive_analysis.csv"
CUSTOM_BETS_CSV = "custom_bets.csv"
FILTERED_CSV = "filtered.csv"

file_lock = threading.Lock()


def get_random_bid(min_val=10.5, max_val=500.5):
    return round(random.uniform(min_val, max_val), 1)


def calculate_payout(user_pick, actual_winner, bid_amount, home_team, home_odds, away_odds):
    is_win = user_pick.strip().lower() == actual_winner.strip().lower()
    odds = float(home_odds) if user_pick.strip().lower() == home_team.strip().lower() else float(away_odds)
    if is_win:
        payout = round(bid_amount * odds, 2)
        profit = round(payout - bid_amount, 2)
        status = "WON"
    else:
        payout = 0.0
        profit = round(-bid_amount, 2)
        status = "LOST"
    return status, payout, profit


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/match", methods=["GET"])
def get_match():
    """Returns the current match and raw bets from custom_bets.csv."""
    if not os.path.exists(CUSTOM_BETS_CSV):
        return jsonify({"success": False, "message": "custom_bets.csv not found"}), 404

    with file_lock:
        with open(CUSTOM_BETS_CSV, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

    if not rows:
        return jsonify({"success": False, "message": "No match bets found"}), 404

    match_meta = {
        "Match_ID": rows[0].get("Match_ID"),
        "Home_Team": rows[0].get("Home_Team"),
        "Away_Team": rows[0].get("Away_Team"),
        "Home_Team_Odds": rows[0].get("Home_Team_Odds"),
        "Away_Team_Odds": rows[0].get("Away_Team_Odds"),
        "Actual_Winner": rows[0].get("Actual_Winner"),
    }
    return jsonify({"success": True, "match": match_meta, "bets": rows})


@app.route("/api/bet", methods=["POST"])
def place_bet():
    """Receives user bet from web frontend and appends directly to custom_bets.csv."""
    data = request.json or {}
    user_pick = data.get("User_Pick")
    bid_amount = data.get("bid_amount")

    if not user_pick or not bid_amount:
        return jsonify({"success": False, "message": "Missing fields"}), 400

    with file_lock:
        rows = []
        with open(CUSTOM_BETS_CSV, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        if not rows:
            return jsonify({"success": False, "message": "Match data empty"}), 400

        new_bet = dict(rows[0])
        new_bet["s.no"] = len(rows) + 1
        new_bet["user_id"] = "user_me"
        new_bet["bid_amount"] = round(float(bid_amount), 1)
        if "User_Pick" in (fieldnames or []):
            new_bet["User_Pick"] = user_pick

        with open(CUSTOM_BETS_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(new_bet)

    return jsonify({"success": True, "bet": new_bet})


@app.route("/api/settle", methods=["POST"])
def settle_match():
    """Settles all bets in custom_bets.csv and writes the final calculations to filtered.csv."""
    with file_lock:
        if not os.path.exists(CUSTOM_BETS_CSV):
            return jsonify({"success": False, "message": "File not found"}), 404

        with open(CUSTOM_BETS_CSV, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        for col in ["User_Pick", "Result", "payout_amount", "net_profit"]:
            if col not in fieldnames:
                fieldnames.append(col)

        settled_rows = []
        for row in rows:
            home_team = row.get("Home_Team", "")
            away_team = row.get("Away_Team", "")
            actual_winner = row.get("Actual_Winner", "")
            home_odds = row.get("Home_Team_Odds", "1.0")
            away_odds = row.get("Away_Team_Odds", "1.0")
            bid = float(row.get("bid_amount", 0.0))

            user_pick = row.get("User_Pick") or random.choice([home_team, away_team])
            status, payout, profit = calculate_payout(
                user_pick, actual_winner, bid, home_team, home_odds, away_odds
            )

            settled = dict(row)
            settled["User_Pick"] = user_pick
            settled["Result"] = status
            settled["payout_amount"] = payout
            settled["net_profit"] = profit
            settled_rows.append(settled)

        with open(FILTERED_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(settled_rows)

    return jsonify({"success": True, "settled_count": len(settled_rows), "settlements": settled_rows})


if __name__ == "__main__":
    app.run(port=5000, debug=True)