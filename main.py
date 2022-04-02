import json

from flask import Flask, render_template, request
import pla

app = Flask(__name__)

config = json.load(open("config.json"))

@app.route("/")
def home():
    return render_template('fromseed.html')

@app.route('/check-mmoseed', methods=['POST'])
def get_from_seed():
   results = pla.check_from_seed(request.json['seed'],
                                 request.json['rolls'],
                                 request.json['frencounter'],
                                 request.json['brencounter'],
                                 request.json['isbonus'],
                                 request.json['frspawns'],
                                 request.json['brspawns'])
   return { "mmo_spawns": results }

if __name__ == '__main__':
    app.run(host="192.168.0.29", port=8100, debug=True)
