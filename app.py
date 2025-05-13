from flask import Flask, render_template, request, redirect, url_for
from watcher import load_json, save_json, check_all, IC_FILE, STATE_FILE, start_background_thread
import os

app = Flask(__name__)
os.makedirs("data", exist_ok=True)

@app.route("/", methods=["GET", "POST"])  # <- Tohle je důležité!
def index():
    if request.method == "POST":
        ic = request.form.get("ic")
        if ic:
            data = load_json(IC_FILE)
            ics = set(data.get("ics", []))
            ics.add(ic)
            save_json(IC_FILE, {"ics": list(ics)})
        return redirect(url_for("index"))

    ic_list = load_json(IC_FILE).get("ics", [])
    state = load_json(STATE_FILE)
    return render_template("index.html", ics=ic_list, state=state)

@app.route("/remove/<ic>")
def remove_ic(ic):
    data = load_json(IC_FILE)
    ics = set(data.get("ics", []))
    ics.discard(ic)
    save_json(IC_FILE, {"ics": list(ics)})
    return redirect(url_for("index"))

@app.route("/check")
def manual_check():
    new_events = check_all()
    return render_template("index.html",
                           ics=load_json(IC_FILE).get("ics", []),
                           state=load_json(STATE_FILE),
                           new_events=new_events)

if __name__ == "__main__":
    start_background_thread()
    app.run(debug=True)
