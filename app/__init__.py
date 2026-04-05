import os
from flask import Flask, send_from_directory


def create_app():
    app = Flask(__name__, static_folder=None)

    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

    # Register API blueprints
    from app.routes.stock import bp as stock_bp
    from app.routes.grid import bp as grid_bp
    from app.routes.backtest import bp as backtest_bp
    from app.routes.monitor import bp as monitor_bp

    app.register_blueprint(stock_bp)
    app.register_blueprint(grid_bp)
    app.register_blueprint(backtest_bp)
    app.register_blueprint(monitor_bp)

    # Serve frontend static files
    @app.route("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/backtest")
    def backtest_page():
        return send_from_directory(frontend_dir, "backtest.html")

    @app.route("/monitor")
    def monitor_page():
        return send_from_directory(frontend_dir, "monitor.html")

    @app.route("/css/<path:filename>")
    def css_files(filename):
        return send_from_directory(os.path.join(frontend_dir, "css"), filename)

    @app.route("/js/<path:filename>")
    def js_files(filename):
        return send_from_directory(os.path.join(frontend_dir, "js"), filename)

    return app
