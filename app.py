
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
	},

	"PIGGY": {
		"name": "Piggy",
		"id": 4623386862
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

	# Small market movement
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

		print("Roblox returned:", [g["name"] for g in data])

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

	# Real Roblox games
	for game in games:
		players = game.get("playing", 0)

		if players < 50:
			continue

		price = calculate_price(players)
		old = previous_price(game["id"])

		if old and old > 0:
			change = round(((price - old) / old) * 100, 2)
		else:
			change = round(random.uniform(-3, 3), 2)

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


	# Extra market stocks (always available)
	extras = [
		("BROOK", "Brookhaven RP", 185.42, 2.14),
		("JAIL", "Jailbreak", 58.76, -1.33),
		("TSH", "Tower of Hell", 24.91, 0.87),
		("ARS", "Arsenal", 41.55, -0.52),
		("MEEP", "MeepCity", 12.34, 4.21),
		("PIGGY", "Piggy", 18.67, -2.05),
		("BEE", "Bee Swarm Simulator", 33.22, 1.44)
	]

	for symbol, name, base_price, base_change in extras:

		price = round(base_price * random.uniform(0.97, 1.03), 2)
		change = round(base_change + random.uniform(-0.8, 0.8), 2)

		market.append({
			"symbol": symbol,
			"name": name,
			"id": 900000000 + len(market),
			"players": random.randint(500, 50000),
			"visits": random.randint(1000000, 5000000000),
			"price": price,
			"change": change
		})


	market.sort(key=lambda x: x["price"], reverse=True)
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
		"count": len(create_market()),
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

