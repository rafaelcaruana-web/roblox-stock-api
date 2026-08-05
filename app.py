
from flask import Flask, jsonify
import requests
import sqlite3
import time
import random
from datetime import datetime

app = Flask(__name__)

DATABASE = "stocks.db"


# =========================
# ROBLOX STOCK LIST
# =========================


GAMES = {
	"GAGR": {
		"name": "Grow a Garden",
		"id": 7436755782
	},

	"ADPT": {
		"name": "Adopt Me!",
		"id": 383310974
	},

	"MM2": {
		"name": "Murder Mystery 2",
		"id": 66654135
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

	"BEE": {
		"name": "Bee Swarm Simulator",
		"id": 1537690962
	},

	"PIGGY": {
		"name": "Piggy",
		"id": 4623386862
	},

	"MEEP": {
		"name": "MeepCity",
		"id": 370731277
	}
}




# =========================
# CACHE
# =========================

market_cache = []
last_update = 0
CACHE_TIME = 20


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
# PRICE SYSTEM
# =========================

def calculate_price(players):

	if players <= 0:
		return 1.00

	if players < 500:
		base = players / 50

	elif players < 5000:
		base = players / 40

	elif players < 50000:
		base = players / 60

	elif players < 200000:
		base = players / 120

	else:
		base = players / 400

	# Small market volatility
	volatility = random.uniform(0.97, 1.03)

	return round(base * volatility, 2)


# =========================
# ROBLOX API
# =========================

def get_games():
	ids = ",".join(str(game["id"]) for game in GAMES.values())

	url = f"https://games.roblox.com/v1/games?universeIds={ids}"

	try:
		response = requests.get(url, timeout=10)
		return response.json().get("data", [])
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
		visits = game.get("visits", 0)

		if players == 0 and visits < 1000000:
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
			"visits": visits,
			"price": price,
			"change": change
		}
		print(game["name"], players)

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
	global market_cache, last_update

	now = time.time()

	if not market_cache or now - last_update > CACHE_TIME:
		market_cache = create_market()
		last_update = now

	return jsonify({
		"updated": datetime.now().isoformat(),
		"count": len(market_cache),
		"stocks": market_cache
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

