from flask import Flask, jsonify
import requests
import sqlite3
import time
import math
import threading
from datetime import datetime


app = Flask(__name__)


DATABASE = "stocks.db"


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
    }

}



# Stores latest market
market_cache = []



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

        price REAL,

        players INTEGER,

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
        price,
        players,
        timestamp
    )

    VALUES (?,?,?,?,?)
    """,

    (
        stock["id"],
        stock["name"],
        stock["price"],
        stock["players"],
        int(time.time())
    ))


    conn.commit()
    conn.close()




# =========================
# PRICE
# =========================

def calculate_price(players):

    if players <= 0:
        return 0


    return round(
        math.log(players + 10) * 100,
        2
    )




# =========================
# ROBLOX API
# =========================

def get_games():

    ids = ",".join(
        str(x["id"])
        for x in GAMES.values()
    )


    url = (
        "https://games.roblox.com/v1/games"
        "?universeIds=" + ids
    )


    try:

        response = requests.get(
            url,
            timeout=5
        )


        return response.json().get(
            "data",
            []
        )


    except Exception as e:

        print(e)

        return []




# =========================
# UPDATE MARKET
# =========================

def update_market():

    global market_cache


    while True:

        print("Updating stocks...")


        games = get_games()


        new_market = []



        for game in games:


            players = game.get(
                "playing",
                0
            )


            visits = game.get(
                "visits",
                0
            )


            if players == 0 and visits < 1000000:
                continue



            symbol = "UNKNOWN"


            for ticker,data in GAMES.items():

                if data["id"] == game["id"]:

                    symbol = ticker



            stock = {

                "symbol": symbol,

                "name": game["name"],

                "id": game["id"],

                "players": players,

                "visits": visits,

                "price": calculate_price(players),

                "change": 0

            }


            save_history(stock)


            new_market.append(stock)



        new_market.sort(
            key=lambda x:x["players"],
            reverse=True
        )


        market_cache = new_market


        print(
            "Stocks updated:",
            len(market_cache)
        )


        # UPDATE EVERY 10 SECONDS

        time.sleep(10)





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
        market_cache

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




# =========================
# START
# =========================

init_db()


threading.Thread(
    target=update_market,
    daemon=True
).start()



if __name__ == "__main__":

    app.run()