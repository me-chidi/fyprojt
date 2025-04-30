from myapp import create_app, turbo, db
from myapp.models import Nodes
from threading import Thread
import pyduino as pyd
from time import sleep
from flask import render_template


app = create_app()


def updater_thread():
    with app.app_context():
        while True:
            sleep(1.5)
            try:
                turbo.push(turbo.update(render_template("stat-table.html"), "table"))
            except Exception as e:
                print(f"❌ TurboFlask push failed: {e}")


# api.context_processor provides only
# to templates rendered with the api route
@app.context_processor
def inject_nodes():
    nodes = Nodes.query.all()
    return {"nodes": nodes}


# By default the working threads are tied to the main process.
# This is extra safety for when FLASK_DEBUG=1, since two processes are started in debug mode.
# Note: FLASK_DEBUG=1 breaks the websocket for turbo streams.
if app.config["MAIN_PROC"]:
    try:
        pyduino_thread = Thread(target=pyd.start_pyduino, args=(db, Nodes, app), daemon=True)
        pyduino_thread.start()
        upthread = Thread(target=updater_thread, daemon=True)
        upthread.start()
    except Exception as e:
        print(f"An error occurred!: {e}")


# start ngrok
def start_ngrok():
    from pyngrok import ngrok

    url = ngrok.connect(5000)
    print(url)


if app.config["START_NGROK"]:
    start_ngrok()
