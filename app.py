from flask import Flask, jsonify
import requests
import sqlite3
import time
import math
from datetime import datetime

app = Flask(__name__)


DATABASE = "stocks.db"


# -------------------------
# DATABASE SETUP
# -------------------------

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



# -------------------------
# ROBLOX API
# -------------------------

def get_top_games():

    url = (
        "https://games.roblox.com/v1/games/list"
        "?model.filter=TopPlayed"
        "&model.limit=100"
    )


    response = requests.get(url)


    if response.status_code != 200:
        return []


    data = response.json()

    games = []


    for game in data.get("games", []):

        games.append({
            "id": game["id"],
            "name": game["name"]
        })


    return games



def get_game_stats(ids):

    ids = ",".join(
        str(i) for i in ids
    )


    url = (
        "https://games.roblox.com/v1/games"
        f"?universeIds={ids}"
    )


    response = requests.get(url)


    if response.status_code != 200:
        return []


    return response.json()["data"]




# -------------------------
# STOCK SYSTEM
# -------------------------

def calculate_price(players):

    # prevents tiny games having $0
    return round(
        math.log(players + 10) * 100,
        2
    )



def save_price(game):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO price_history
        (universe_id,name,players,price,timestamp)

        VALUES (?,?,?,?,?)
        """,

        (
            game["id"],
            game["name"],
            game["players"],
            game["price"],
            int(time.time())
        )
    )


    conn.commit()
    conn.close()




def get_previous_price(universe_id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT price
        FROM price_history

        WHERE universe_id=?

        ORDER BY timestamp DESC

        LIMIT 1 OFFSET 1
        """,

        (universe_id,)
    )


    result = cursor.fetchone()

    conn.close()


    if result:
        return result[0]

    return None




# -------------------------
# CREATE MARKET
# -------------------------

def generate_market():

    games = get_top_games()


    if not games:
        return []


    ids = [
        game["id"]
        for game in games
    ]


    stats = get_game_stats(ids)


    market = []


    for game in stats:


        players = game["playing"]


        price = calculate_price(
            players
        )


        previous = get_previous_price(
            game["id"]
        )


        if previous:

            change = round(
                ((price - previous) / previous) * 100,
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




# -------------------------
# ROUTES
# -------------------------


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


    cursor.execute(
        """
        SELECT price,timestamp

        FROM price_history

        WHERE universe_id=?

        ORDER BY timestamp DESC

        LIMIT 100
        """,

        (game_id,)
    )


    data = cursor.fetchall()

    conn.close()


    return jsonify(data)




# START

init_db()


if __name__ == "__main__":

    app.run()