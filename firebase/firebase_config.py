"""
Firebase Configuration and Admin SDK initialization.
Supports live Firebase credentials (serviceAccountKey.json) with a high-fidelity
in-memory / JSON file fallback for seamless local operation out-of-the-box.
"""
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("firebase_config")

_db_instance = None
_is_mock_mode = False


class LocalJSONFirestore:
    """
    High-fidelity file-backed mock for Firestore collections.
    Used when serviceAccountKey.json is not configured yet, ensuring
    the app is 100% testable out-of-the-box.
    """
    def __init__(self, data_dir: str = "data_store"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        logger.info(f"LocalJSONFirestore initialized storing data in {self.data_dir.absolute()}")

    def _collection_file(self, col_name: str) -> Path:
        return self.data_dir / f"{col_name}.json"

    def _read_col(self, col_name: str) -> dict:
        f = self._collection_file(col_name)
        if not f.exists():
            return {}
        try:
            with open(f, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error reading collection {col_name}: {e}")
            return {}

    def _write_col(self, col_name: str, data: dict):
        f = self._collection_file(col_name)
        with open(f, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, default=str)

    class DocRef:
        def __init__(self, col, doc_id):
            self.col = col
            self.id = doc_id

        def get(self):
            col_data = self.col._read_col(self.col.name)
            doc_data = col_data.get(self.id)
            return self.col.DocSnapshot(self.id, doc_data)

        def set(self, data, merge=False):
            col_data = self.col._read_col(self.col.name)
            if merge and self.id in col_data:
                col_data[self.id].update(data)
            else:
                col_data[self.id] = data
            self.col._write_col(self.col.name, col_data)
            return True

        def delete(self):
            col_data = self.col._read_col(self.col.name)
            if self.id in col_data:
                del col_data[self.id]
                self.col._write_col(self.col.name, col_data)

    class DocSnapshot:
        def __init__(self, doc_id, data):
            self.id = doc_id
            self._data = data

        @property
        def exists(self):
            return self._data is not None

        def to_dict(self):
            return self._data or {}

    class CollectionRef:
        def __init__(self, db, name):
            self.db = db
            self.name = name
            self.DocSnapshot = db.DocSnapshot

        def document(self, doc_id=None):
            if not doc_id:
                import uuid
                doc_id = str(uuid.uuid4())
            return self.db.DocRef(self, doc_id)

        def get(self):
            col_data = self._read_col(self.name)
            return [self.db.DocSnapshot(k, v) for k, v in col_data.items()]

        def stream(self):
            return self.get()

        def _read_col(self, col_name):
            return self.db._read_col(col_name)

        def _write_col(self, col_name, data):
            self.db._write_col(col_name, data)

    def collection(self, col_name: str):
        return self.CollectionRef(self, col_name)

    def transaction(self):
        # Fallback dummy transaction context manager
        class DummyTx:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        return DummyTx()


def get_firestore_db():
    """Returns Firestore DB client (Firebase Admin SDK or Local JSON fallback)."""
    global _db_instance, _is_mock_mode
    if _db_instance is not None:
        return _db_instance, _is_mock_mode

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")

    if os.path.exists(cred_path):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            _db_instance = firestore.client()
            _is_mock_mode = False
            logger.info("Connected to live Firebase Firestore via Admin SDK.")
            return _db_instance, _is_mock_mode
        except Exception as e:
            logger.warning(f"Failed to initialize Firebase Admin SDK from {cred_path}: {e}. Falling back to LocalJSONFirestore.")

    _db_instance = LocalJSONFirestore()
    _is_mock_mode = True
    logger.info("Using LocalJSONFirestore fallback for local testing.")
    return _db_instance, _is_mock_mode
