import os
from flask import Flask
from config import Config
from models import db
from sqlalchemy import event
from sqlalchemy.engine import Engine

# ── WAL mode for SQLite ──
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance folder
    os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)

    db.init_app(app)

    # ── Register Blueprints ──
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.master import master_bp
    from routes.stok import stok_bp
    from routes.pembelian import pembelian_bp
    from routes.resep import resep_bp
    from routes.kasir import kasir_bp
    from routes.laporan import laporan_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(stok_bp)
    app.register_blueprint(pembelian_bp)
    app.register_blueprint(resep_bp)
    app.register_blueprint(kasir_bp)
    app.register_blueprint(laporan_bp)

    # ── Template filters ──
    from datetime import date as dt_date
    BULAN_IND = {1:'Januari',2:'Februari',3:'Maret',4:'April',5:'Mei',6:'Juni',
                 7:'Juli',8:'Agustus',9:'September',10:'Oktober',11:'November',12:'Desember'}
    @app.template_filter('format_tgl')
    def format_tgl(d):
        if not d: return ''
        if hasattr(d, 'strftime'):
            return f"{d.day} {BULAN_IND.get(d.month,'')} {d.year}"
        return str(d)

    @app.template_filter('format_rp')
    def format_rp(v):
        try: return f"Rp {v:,.0f}"
        except: return f"Rp 0"

    # ── Context processor ──
    from flask import session
    from models import Obat as ObatModel

    @app.context_processor
    def inject_globals():
        user = None
        if session.get('user_id'):
            from models import User
            user = User.query.get(session['user_id'])
        return {
            'app_name': app.config.get('APP_NAME', 'Apotik'),
            'current_user': user,
            'Obat': ObatModel
        }

    # ── Create tables + seed ──
    with app.app_context():
        db.create_all()
        from seed_data import seed_all
        seed_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5004, debug=True)
