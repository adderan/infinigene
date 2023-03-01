import intelliwaterai.infinitydb.access as idb
from queries import get_sequence
from flask import Flask, render_template, request, url_for

server = idb.InfinityDBAccessor("https://24.6.93.122:37411/infinitydb/data", db="boilerbay/genomics", user="ai", password="ai")
server.is_verification_enabled = False
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

