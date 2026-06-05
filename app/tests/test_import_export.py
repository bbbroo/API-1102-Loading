from app.backend.database.models import Base
from app.backend.database.seed import seed_if_empty
from app.backend.database.session import engine, SessionLocal
from app.backend.exports.csv import render_csv
from app.backend.exports.json_package import render_json
from app.backend.exports.pdf import render_pdf
from app.backend.services.import_export_service import project_package


def test_project_export_renderers():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
        package = project_package(db, 1)
        assert render_json(package).startswith(b"{")
        assert b"Stress Check" in render_csv(package)
        pdf = render_pdf(package)
        assert pdf.startswith(b"%PDF")
        assert b"HDR" in pdf
    finally:
        db.close()
