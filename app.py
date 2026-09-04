"""
Win Spares Document Management System - Main Flask Application Entry Point
"""
import os
from datetime import datetime
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'win-spares-quotation-secret-key-2026')

# Register Blueprints
from routes.dashboard_routes import dashboard_bp
from routes.quotation_routes import quotation_bp
from routes.invoice_routes import invoice_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(quotation_bp)
app.register_blueprint(invoice_bp)


@app.context_processor
def inject_globals():
    return {
        'now_year': datetime.now().year
    }


@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html'), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server Error: {error}")
    return render_template('base.html'), 500


if __name__ == '__main__':
    import socket

    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')

    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print("\n" + "=" * 58)
    print(" Win Spares Document Management System Running")
    print(f" • Local Computer Access: http://127.0.0.1:{port}")
    print(f" • Same Wi-Fi Network Access: http://{local_ip}:{port}")
    print("=" * 58 + "\n")

    app.run(host=host, port=port, debug=True)
