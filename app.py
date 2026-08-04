from flask import Flask, jsonify
import requests
import time
import math

app = Flask(__name__)

# Popular Roblox game IDs
# We can expand this to 100 later
GAME_IDS = {
    "Grow a Garden": 126884695634066,
    "Brookhaven": 4924922222,
    "Blox Fruits": 2753915549,
    "Adopt Me": 920587237,
    "Murder Mystery 2": 142823291
}


def get_game_data():
    universe_ids = ",".join(str(x) for x in GAME_IDS.values())

    url = f"https://games.roblox.com/v1/games?universeIds={universe_ids}"

    response = requests.get(url)

    if response.status_code != 200:
        return []

    data = response.json()

    stocks = []

    for game in data["data"]:

        name = game["name"]
        players = game["playing"]

        # Convert players into stock price
        price = round(math.log(players + 1) * 100, 2)

        stocks.append({
            "name": name,
            "players": players,
            "price": price,
            "visits": game["visits"]
        })

    return stocks



@app.route("/")
def home():
    return "Roblox Stock API Running"



@app.route("/stocks")
def stocks():

    return jsonify({
        "updated": time.time(),
        "stocks": get_game_data()
    })



if __name__ == "__main__":
    app.run()