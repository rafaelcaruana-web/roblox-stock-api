
from flask import Flask, jsonify
import requests
import sqlite3
import time
import random
from datetime import datetime

app = Flask(__name__)

DATABASE = "stocks.db"


# =========================
# WORKING ROBLOX STOCKS
# =========================

GAMES = {
	"MM2": {
		"name": "Murder Mystery 2",
		"id": 66654135
	},

	"ADPT": {
		"name": "Adopt Me!",
		"id": 383310974
	},

	"GAGR": {
		"name": "Grow a Garden",
		"id": 7436755782
	},

	"BROOK": {
		"name": "Brookhaven RP",
		"id": 4924922222
	},

	"ARS": {
		"name": "Arsenal",
		"id": 286090429
	},

	"TSH": {
		"name": "Tower of Hell",
		"id": 1962086868
	},

	"JAIL": {
		"name": "Jailbreak",
		"id": 606849621
	},

	"MEEP": {
		"name": "MeepCity",
		"id": 370731277
	}
}


# =========================
# DATABASE
# =========================

def init_db():
	conn = sqlite3.connect(DATABASE)
	cursor = conn.cursor()

	cursor.execute("""
	CREATE TABLE IF NOT EXISTS history (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		universe_id INTEGER,
		name TEXT,
		players INTEGER,
		price REAL,
		timestamp INTEGER
	)
	""")

	conn.commit()
	conn.close()


def save_history(stock):
	conn = sqlite3.connect(DATABASE)
	cursor = conn.cursor()

	cursor.execute("""
	INSERT INTO history
	(universe_id, name, players, price, timestamp)
	VALUES (?,?,?,?,?)
	""",
	(
		stock["id"],
		stock["name"],
		stock["players"],
		stock["price"],
		int(time.time())
	))

	conn.commit()
	conn.close()


def previous_price(game_id):
	conn = sqlite3.connect(DATABASE)
	cursor = conn.cursor()

	cursor.execute("""
	SELECT price FROM history
	WHERE universe_id=?
	ORDER BY timestamp DESC
	LIMIT 1 OFFSET 1
	""", (game_id,))

	result = cursor.fetchone()
	conn.close()

	return result[0] if result else None


# =========================
# BETTER PRICE SYSTEM
# =========================

def calculate_price(players):
	if players <= 0:
		return 1.00

	if players < 1000:
		base = players / 20
	elif players < 10000:
		base = players / 40
	elif players < 100000:
		base = players / 80
	else:
		base = players / 400

	# Small random market movement
	base *= random.uniform(0.98, 1.02)

	return round(base, 2)


# =========================
# ROBLOX API
# =========================

def get_games():
	ids = ",".join(str(g["id"]) for g in GAMES.values())

	url = f"https://games.roblox.com/v1/games?universeIds={ids}"

	try:
		response = requests.get(url, timeout=10)
		data = response.json().get("data", [])

		print(f"Fetched {len(data)} games from Roblox")
		return data

	except Exception as e:
		print("Roblox API error:", e)
		return []


# =========================
# CREATE MARKET
# =========================

def create_market():
	games = get_games()
	market = []

	for game in games:
		players = game.get("playing", 0)

		# Skip completely dead games
		if players == 0:
			continue

		price = calculate_price(players)
		old = previous_price(game["id"])

		if old and old > 0:
			change = round(((price - old) / old) * 100, 2)
		else:
			change = 0

		symbol = "UNK"
		for ticker, info in GAMES.items():
			if info["id"] == game["id"]:
				symbol = ticker

		stock = {
			"symbol": symbol,
			"name": game["name"],
			"id": game["id"],
			"players": players,
			"visits": game.get("visits", 0),
			"price": price,
			"change": change
		}

		save_history(stock)
		market.append(stock)

	market.sort(key=lambda x: x["players"], reverse=True)
	return market


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
	return "Roblox Stock API Running"


@app.route("/stocks")
def stocks():
	return jsonify({
		"updated": datetime.now().isoformat(),
		"stocks": create_market()
	})


@app.route("/history/<int:game_id>")
def history(game_id):
	conn = sqlite3.connect(DATABASE)
	cursor = conn.cursor()

	cursor.execute("""
	SELECT price, timestamp
	FROM history
	WHERE universe_id=?
	ORDER BY timestamp DESC
	LIMIT 50
	""", (game_id,))

	rows = cursor.fetchall()
	conn.close()

	return jsonify(rows[::-1])


# =========================
# START
# =========================

init_db()


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000)

