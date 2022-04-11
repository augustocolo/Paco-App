from flask import Flask, request, render_template
from flask_assets import Bundle, Environment

app = Flask(__name__)

# Create assets environment
assets = Environment(app)
assets.url = app.static_url_path

# Bundle JS files
js = Bundle(
    "assets/node_modules/jquery/dist/jquery.min.js",
    "assets/node_modules/@popperjs/core/dist/umd/popper.min.js",
    "assets/node_modules/bootstrap/dist/js/bootstrap.min.js",
    filters="jsmin",
    output="js/generated.js"
)
assets.register("js_all", js)

# Bundle Scss files
scss = Bundle(
    "assets/main.scss",  # 1. will read this scss file and generate a css file based on it
    filters="libsass",   # 2. using this filter: https://webassets.readthedocs.io/en/latest/builtin_filters.html#libsass
    output="css/scss-generated.css"  # 3. and output the generated .css file in the static/css folder
)
assets.register("scss_all", scss)  # 4. register the generated css file, to be used in Jinja templates (see base.html)


@app.route('/')
def index():
    return render_template("landing_user.html")


if __name__ == '__main__':
    app.run()