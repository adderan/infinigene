import argparse
import intelliwaterai.infinitydb.access as idb
from queries import get_sequence
from flask import Flask, render_template, request, url_for

server = None
app = Flask(__name__)

@app.route("/", methods=["POST", "GET"])
def home():
    chromosome = "chr1"
    start = 3000000
    end = 3000100
    if request.method == "POST":
        chromosome, start_end = request.form["coordinates"].split(":")
        start, end = start_end.split("-")
        print(chromosome, start, end)
        start = int(start)
        end = int(end)
        if abs(end - start) > 100:
            end = start + 100
        print(request.form['coordinates'])

    seq = get_sequence(server, genome="grch38", chromosome=chromosome, start=start, end=end)
    seq = "\t".join(seq)
    return render_template("genome_browser.html", seq=seq)

@app.route("/sequence/<genome>/<chromosome>/<int:start>/<int:end>")
def getSequence(genome, chromosome, start, end):
    seq = get_sequence(server, genome=genome, chromosome=chromosome, start=start, end=end)
    return seq


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=str, default="https://localhost:37411/infinitydb/data")
    parser.add_argument("--db", type=str, default="boilerbay/genomics")
    parser.add_argument("--user", type=str, default="ai")
    parser.add_argument("--password", type=str, default="ai")
    args = parser.parse_args()

    server = idb.InfinityDBAccessor(server_url=args.server, db=args.db, user=args.user, password=args.password)
    server.is_verification_enabled = False

    app.run()

