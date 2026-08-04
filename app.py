from flask import Flask, jsonify
import requests

app = Flask(__name__)

def fetch_games():
    url = "https://games.roblox.com/v1/games/list?model.keyword=&model.sortToken=&model.maxRows=100"
    r = requests.get(url)
    data = r.json()

    games = []
    for game in data.get("games", []):
        games.append({
            "id": game["placeId"],
            "name": game["name"],
            "players": game.get("playerCount", 0)
        })

    return games

@app.route("/stocks")
def stocks():
    return jsonify(fetch_games())

@app.route("/")
def home():
    return "Roblox Stock API Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)