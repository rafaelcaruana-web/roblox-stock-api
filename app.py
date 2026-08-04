from flask import Flask, jsonify
import requests
import sqlite3
import time
import math
from datetime import datetime

app = Flask(__name__)

DATABASE = "stocks.db"


# =========================
# ROBLOX GAMES
# =========================

GAMES = {
    "Grow a Garden": 7436755782,
    "Adopt Me!": 383310974,
    "Murder Mystery 2": 66654135,
    "Blox Fruits": 2753915549,
    "Brookhaven": 4924922222,
    "Pet Simulator 99": 8737899170,
    "Doors": 4282985734,
    "Tower of Hell": 1962086868,
    "Jailbreak": 606849621,
    "Arsenal": 286090429
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
    (
        universe_id,
        name,
        players,
        price,
        timestamp
    )

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
    SELECT price
    FROM history

    WHERE universe_id=?

    ORDER BY timestamp DESC

    LIMIT 1 OFFSET 1
    """,
    (game_id,))


    result = cursor.fetchone()

    conn.close()


    if result:
        return result[0]

    return None




# =========================
# STOCK PRICE
# =========================

def calculate_price(players):

    if players <= 0:
        return 0


    return round(
        math.log(players + 10) * 100,
        2
    )




# =========================
# ROBLOX DATA
# =========================

def get_games():

    ids = ",".join(
        str(x)
        for x in GAMES.values()
    )


    url = (
        "https://games.roblox.com/v1/games"
        f"?universeIds={ids}"
    )


    response = requests.get(url)


    if response.status_code != 200:

        print(response.text)

        return []


    return response.json().get("data",[])




# =========================
# MARKET
# =========================

def create_market():

    games = get_games()

    market = []


    for game in games:

        players = game.get(
            "playing",
            0
        )

        visits = game.get(
            "visits",
            0
        )


        # Remove fake/dead places
        if players == 0 and visits < 1000000:
            continue



        price = calculate_price(
            players
        )


        old = previous_price(
            game["id"]
        )


        if old and old > 0:

            change = round(
                ((price-old)/old)*100,
                2
            )

        else:

            change = 0



        stock = {

            "id": game["id"],

            "name": game["name"],

            "players": players,

            "visits": visits,

            "price": price,

            "change": change

        }


        save_history(stock)

        market.append(stock)



    # Highest players first
    market.sort(
        key=lambda x: x["players"],
        reverse=True
    )


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

        "updated":
        datetime.now().isoformat(),

        "stocks":
        create_market()

    })



@app.route("/history/<int:id>")
def history(id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()


    cursor.execute("""
    SELECT price,timestamp

    FROM history

    WHERE universe_id=?

    ORDER BY timestamp DESC

    LIMIT 100
    """,
    (id,))


    data = cursor.fetchall()

    conn.close()


    return jsonify(data)



init_db()


if __name__ == "__main__":

    app.run()