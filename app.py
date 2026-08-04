from flask import Flask, jsonify
import requests
import sqlite3
import time
import math
from datetime import datetime

app = Flask(__name__)

DATABASE = "stocks.db"


# ==========================
# DATABASE
# ==========================

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
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



# ==========================
# ROBLOX API
# ==========================

def get_top_games():

    url = (
        "https://games.roblox.com/v1/games/list"
        "?model.filter=TopPlayed"
        "&model.maxRows=100"
    )

    response = requests.get(url)

    print(response.text)


    if response.status_code != 200:
        return []


    data = response.json()

    games = []


    for game in data.get("games", []):

        games.append({
            "place_id": game["id"],
            "name": game["name"]
        })


    return games



def convert_to_universe(place_id):

    url = (
        f"https://apis.roblox.com/universes/v1/"
        f"places/{place_id}/universe"
    )

    response = requests.get(url)


    if response.status_code != 200:
        return None


    return response.json().get("universeId")



def get_game_stats(universe_ids):

    if not universe_ids:
        return []


    ids = ",".join(
        str(x) for x in universe_ids
    )


    url = (
        "https://games.roblox.com/v1/games"
        f"?universeIds={ids}"
    )


    response = requests.get(url)


    if response.status_code != 200:
        print(response.text)
        return []


    return response.json().get("data", [])



# ==========================
# STOCK SYSTEM
# ==========================

def calculate_price(players):

    return round(
        math.log(players + 10) * 100,
        2
    )



def get_previous_price(universe_id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()


    cursor.execute("""
    SELECT price
    FROM price_history

    WHERE universe_id=?

    ORDER BY timestamp DESC

    LIMIT 1
    """,
    (universe_id,))


    result = cursor.fetchone()

    conn.close()


    if result:
        return result[0]

    return None



def save_price(stock):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()


    cursor.execute("""
    INSERT INTO price_history
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




def generate_market():

    games = get_top_games()


    if not games:
        return []


    universe_ids = []


    for game in games:

        universe = convert_to_universe(
            game["place_id"]
        )


        if universe:
            universe_ids.append(universe)



    stats = get_game_stats(
        universe_ids
    )


    market = []


    for game in stats:

        players = game["playing"]

        price = calculate_price(
            players
        )


        old_price = get_previous_price(
            game["id"]
        )


        if old_price:

            change = round(
                ((price-old_price)/old_price)*100,
                2
            )

        else:
            change = 0



        stock = {

            "id": game["id"],

            "name": game["name"],

            "players": players,

            "visits": game["visits"],

            "price": price,

            "change": change

        }


        save_price(stock)

        market.append(stock)



    return market



# ==========================
# ROUTES
# ==========================

@app.route("/")
def home():

    return "Roblox Stock API Running"



@app.route("/stocks")
def stocks():

    return jsonify({

        "updated": datetime.now().isoformat(),

        "stocks": generate_market()

    })



@app.route("/history/<int:game_id>")
def history(game_id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()


    cursor.execute("""
    SELECT price,timestamp

    FROM price_history

    WHERE universe_id=?

    ORDER BY timestamp DESC

    LIMIT 100
    """,
    (game_id,))


    data = cursor.fetchall()

    conn.close()


    return jsonify(data)



init_db()


if __name__ == "__main__":
    app.run()