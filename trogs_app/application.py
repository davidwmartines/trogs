
import views
from flask import Flask

application = Flask(__name__)

def favicon():
    return application.send_static_file('favicon.ico')

application.add_url_rule('/', view_func=views.home)
application.add_url_rule('/artist/<id>', view_func=views.artist)
application.add_url_rule('/album/<id>', view_func=views.album)
application.add_url_rule('/track/<id>', view_func=views.track)
application.add_url_rule('/favicon.ico', view_func=favicon)

# run the app.
if __name__ == "__main__":
    application.run()
