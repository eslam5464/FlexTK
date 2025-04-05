import logging
from dataclasses import dataclass, field
from typing import Any

import firebase_admin
from firebase_admin import App, credentials, firestore
from firebase_admin.credentials import Certificate
from google.cloud.firestore_v1 import Client
from lib.schemas.firebase import FirebaseServiceAccount

logger = logging.getLogger(__name__)


@dataclass
class Firestore:
    _default_app: App | None = field(init=False, default=None)
    _app_certificate: Certificate | None = field(init=False, default=None)
    _firestore_db: Client | None = field(init=False, default=None)

    def __init__(self, service_account: FirebaseServiceAccount):
        try:
            firebase_admin.get_app()
            self._firestore_db = firestore.client(self._default_app)
            app_exists = True
        except ValueError:
            app_exists = False

        try:
            if app_exists is False:
                self._app_certificate = credentials.Certificate(service_account.model_dump())
                self._default_app = firebase_admin.initialize_app(
                    credential=self._app_certificate,
                )
                self._firestore_db = firestore.client(self._default_app)
        except IOError as err:
            logger.critical(
                msg="Error initializing Firestore app, certificate file not found",
                extra={"exception": err},
            )
            raise err
        except ValueError as err:
            logger.critical(msg="Error initializing Firestore app", extra={"exception": err})
            raise err
        except Exception as ex:
            logger.critical(msg="Error initializing Firestore app, unknown error", extra={"exception": ex})
            raise ex

    @property
    def app(self) -> App:
        if self._default_app is None:
            logger.error(msg="Firebase app not initialized")
            raise ValueError("Firebase app not initialized")

        return self._default_app

    @property
    def firestore_client(self) -> Client:
        if self._firestore_db is None:
            logger.error(msg="Firestore client not initialized")
            raise ValueError("Firestore client not initialized")

        return self._firestore_db

    def fetch_all_documents(self, collection_name: str) -> list[dict[str, Any]]:
        try:
            collection_ref = self._firestore_db.collection(collection_name)
            docs = collection_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as ex:
            logger.error(msg="Error fetching documents from collection", extra={"exception": ex})
            raise ex

    def add_document(self, collection_name: str, document_id: str, data: dict):
        try:
            doc_ref = self._firestore_db.collection(collection_name).document(document_id)
            doc_ref.set(data)
            logger.debug(
                msg=f"Document added to collection {collection_name} with ID {document_id}",
                extra={"document_data": data},
            )
        except Exception as ex:
            logger.error(msg="Error adding document to collection", extra={"exception": ex})
            raise ex

    def update_document(self, collection_name: str, document_id: str, data: dict):
        try:
            doc_ref = self._firestore_db.collection(collection_name).document(document_id)
            doc_ref.update(data)
            logger.debug(
                msg=f"Document updated in collection {collection_name} with ID {document_id}",
                extra={"document_data": data},
            )
        except Exception as ex:
            logger.error(
                msg=f"Error updating document in collection {collection_name}",
                extra={"exception": ex},
            )
            raise ex

    def remove_document(self, collection_name: str, document_id: str):
        try:
            doc_ref = self._firestore_db.collection(collection_name).document(document_id)
            doc_ref.delete()
            logger.debug(
                msg=f"Document removed from collection {collection_name} with ID {document_id}",
            )
        except Exception as ex:
            logger.error(
                msg=f"Error removing document from collection {collection_name} with ID {document_id}",
                extra={"exception": ex},
            )
            raise ex

    def get_document(self, collection_name: str, document_id: str):
        try:
            doc_ref = self._firestore_db.collection(collection_name).document(document_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            else:
                return None
        except Exception as ex:
            logger.error(
                msg=f"Error getting document from collection {collection_name}",
                extra={"exception": ex},
            )
            raise ex
