from flask import Flask, jsonify
import requests
import sqlite3
import time
import math
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
# PRICE SYSTEM
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
        str(game["id"])
        for game in GAMES.values()
    )


    url = (
        "https://games.roblox.com/v1/games"
        "?universeIds="
        + ids
    )


    try:

        response = requests.get(
            url,
            timeout=10
        )


        return response.json().get(
            "data",
            []
        )


    except Exception as e:

        print("Roblox error:", e)

        return []





# =========================
# CREATE MARKET
# =========================

def create_market():

    global market_cache
    global last_update


    # Use cache if still fresh

    if market_cache and time.time() - last_update < CACHE_TIME:

        return market_cache



    print("Updating stocks...")


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


        # Remove dead games

        if players == 0 and visits < 1000000:

            continue



        symbol = "UNKNOWN"



        for ticker,info in GAMES.items():

            if info["id"] == game["id"]:

                symbol = ticker




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

            "symbol": symbol,

            "name": game["name"],

            "id": game["id"],

            "players": players,

            "visits": visits,

            "price": price,

            "change": change

        }



        save_history(stock)


        market.append(stock)



    market.sort(
        key=lambda x:x["players"],
        reverse=True
    )



    market_cache = market

    last_update = time.time()


    print(
        "Stocks updated:",
        len(market_cache)
    )


    return market_cache





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