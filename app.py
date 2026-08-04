from flask import Flask, jsonify
import requests
import time
import math

app = Flask(__name__)


# Roblox Universe IDs
GAME_IDS = {
    "Grow a Garden": 7436755782,
    "Adopt Me": 383310974,
    "Murder Mystery 2": 66654135,
    "Blox Fruits": 2753915549,
    "Brookhaven": 4924922222,
    "Pet Simulator 99": 8737899170,
    "Doors": 4282985734,
    "Tower of Hell": 1962086868,
    "Jailbreak": 606849621,
    "Arsenal": 286090429
}

# Stores previous player counts
previous_players = {}


def calculate_price(players):
    """
    Converts player count into stock price
    """
    return round(math.log(players + 1) * 100, 2)


def calculate_change(name, players):
    """
    Calculates percentage player change
    """
    old_players = previous_players.get(name, players)

    if old_players == 0:
        change = 0
    else:
        change = ((players - old_players) / old_players) * 100

    previous_players[name] = players

    return round(change, 2)



def get_game_data():

    universe_ids = ",".join(
        str(id) for id in GAME_IDS.values()
    )

    url = (
        "https://games.roblox.com/v1/games"
        f"?universeIds={universe_ids}"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return []


    data = response.json()

    stocks = []


    for game in data["data"]:

        name = game["name"]
        players = game["playing"]

        price = calculate_price(players)
        change = calculate_change(name, players)


        if players > 0 or game["visits"] > 1000000:
            stocks.append({
            "name": name,
            "players": players,
            "price": price,
            "change": change,
        "   visits": game["visits"]
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