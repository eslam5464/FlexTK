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
        """
        Initialize the Firestore class
        :param service_account: The Firebase service account
        """
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
        """
        Get the default Firebase app
        :return: The default Firebase app
        :raises ValueError: If the default Firebase app is not initialized
        """
        if self._default_app is None:
            logger.error(msg="Firebase app not initialized")
            raise ValueError("Firebase app not initialized")

        return self._default_app

    @property
    def firestore_client(self) -> Client:
        """
        Get the Firestore client
        :return: The Firestore client
        :raises ValueError: If the Firestore client is not initialized
        """
        if self._firestore_db is None:
            logger.error(msg="Firestore client not initialized")
            raise ValueError("Firestore client not initialized")

        return self._firestore_db

    def fetch_all_documents(self, collection_name: str) -> list[dict[str, Any]]:
        """
        Fetch all documents from a collection
        :param collection_name: The name of the collection
        :return: A list of documents
        :raises Exception: If there is an error fetching the documents
        """
        try:
            collection_ref = self._firestore_db.collection(collection_name)
            docs = collection_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as ex:
            logger.error(msg="Error fetching documents from collection", extra={"exception": ex})
            raise ex

    def add_document(self, collection_name: str, document_id: str, data: dict) -> None:
        """
        Add a document to a collection
        :param collection_name: Name of the collection to add the document to
        :param document_id: ID of the document
        :param data: Data to add to the document
        :raises Exception: If there is an error adding the document
        """
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

    def update_document(self, collection_name: str, document_id: str, data: dict) -> None:
        """
        Update a document in a collection
        :param collection_name: Name of the collection
        :param document_id: ID of the document
        :param data: Data to update
        :raises Exception: If there is an error updating the document
        """
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

    def remove_document(self, collection_name: str, document_id: str) -> None:
        """
        Remove a document from a collection
        :param collection_name: Name of the collection
        :param document_id: ID of the document
        :raises Exception: If there is an error removing the document
        """
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

    def get_document(self, collection_name: str, document_id: str) -> dict[str, Any] | None:
        """
        Get a document from a collection
        :param collection_name: Name of the collection
        :param document_id: ID of the document to get
        :return: The document data or None if the document does not exist
        :raises Exception: If there is an error getting the document
        """
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
