from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError
from bson import ObjectId
from typing import Any, Dict, List, Optional, Union
from config.config import db_settings
from .base_database import DatabaseAdapter

class MongoAdapter(DatabaseAdapter):
    """
    MongoAdapter provides an implementation of the DatabaseAdapter interface
    for interacting with a MongoDB database using pymongo. It supports
    standard CRUD operations, queries with filtering, sorting, pagination,
    aggregation, indexing, and bulk operations.
    """

    def __init__(self):
        """
        Initializes the MongoDB adapter with empty client and db attributes.
        """
        self.client = None
        self.db = None

    def connect(self) -> None:
        """
        Establishes a connection to the MongoDB instance using the credentials
        and settings provided in the environment configuration.
        """
        connection_string = (
            f"mongodb://{db_settings.mongo_user}:{db_settings.mongo_password}"
            f"@{db_settings.mongo_host}:{db_settings.mongo_port}/"
            f"{db_settings.mongo_db}?authSource=admin"
        )
        self.client = MongoClient(connection_string)
        self.db = self.client[db_settings.mongo_db]

    def disconnect(self) -> None:
        """
        Closes the connection to the MongoDB instance if open.
        """
        if self.client:
            self.client.close()

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Executes a MongoDB query passed as a JSON string or dictionary.

        :param query: MongoDB query as JSON string or dictionary.
        :param params: Must include 'collection' name.
        :return: List of matching documents.
        """
        import json
        try:
            if isinstance(query, str):
                query_dict = json.loads(query)
            else:
                query_dict = query

            collection = self.db[params['collection']] if params and 'collection' in params else None
            if not collection:
                raise ValueError("Collection name must be specified in params")

            return self.find_many(params['collection'], query_dict)
        except json.JSONDecodeError:
            raise ValueError("Invalid query format")

    def insert(self, table: str, data: Dict[str, Any]) -> Any:
        """
        Inserts a single document and returns its ID.
        """
        return self._insert_document(table, data)

    def update(self, table: str, id: Any, data: Dict[str, Any]) -> bool:
        """
        Updates a document by its ID.

        :return: True if modified, False otherwise.
        """
        return self._update_document(table, id, data)

    def delete(self, table: str, id: Any) -> bool:
        """
        Deletes a document by its ID.

        :return: True if deleted, False otherwise.
        """
        return self._delete_document(table, id)

    def get_by_id(self, table: str, id: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieves a document by its ID.
        """
        return self._get_document_by_id(table, id)

    def get_all(self, table: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all documents from a collection, optionally filtered.

        :param table: Collection name.
        :param filters: Filter conditions as a dictionary.
        :return: List of documents.
        """
        return self.find_many(table, filters or {})

    # MongoDB-specific methods
    def _insert_document(self, collection: str, document: Dict[str, Any]) -> str:
        """
        Inserts a document into the specified collection.

        :return: The inserted document ID as a string.
        """
        col = self.db[collection]
        result = col.insert_one(document)
        return str(result.inserted_id)

    def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Inserts multiple documents and returns their IDs.
        """
        col = self.db[collection]
        result = col.insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    def _update_document(self, collection: str, document_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Updates a document by its ID.

        :return: True if the document was modified.
        """
        col = self.db[collection]
        result = col.update_one({"_id": ObjectId(document_id)}, {"$set": update_data})
        return result.modified_count > 0

    def update_many(self, collection: str, filter_query: Dict, update_data: Dict[str, Any]) -> int:
        """
        Updates multiple documents matching the filter.

        :return: Count of modified documents.
        """
        col = self.db[collection]
        result = col.update_many(filter_query, {"$set": update_data})
        return result.modified_count

    def _delete_document(self, collection: str, document_id: str) -> bool:
        """
        Deletes a document by its ID.

        :return: True if the document was deleted.
        """
        col = self.db[collection]
        result = col.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count > 0

    def delete_many(self, collection: str, filter_query: Dict) -> int:
        """
        Deletes multiple documents matching the filter.

        :return: Count of deleted documents.
        """
        col = self.db[collection]
        result = col.delete_many(filter_query)
        return result.deleted_count

    def _get_document_by_id(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a document by its ID.
        """
        col = self.db[collection]
        document = col.find_one({"_id": ObjectId(document_id)})
        return self._convert_objectid(document) if document else None

    def find_one(self, collection: str, filter_query: Dict) -> Optional[Dict[str, Any]]:
        """
        Finds a single document matching the filter.
        """
        col = self.db[collection]
        document = col.find_one(filter_query)
        return self._convert_objectid(document) if document else None

    def find_many(
        self, 
        collection: str, 
        filter_query: Dict = {}, 
        projection: Dict = None,
        sort: Dict = None,
        limit: int = 10,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Finds multiple documents with optional filtering, projection, and sorting.

        :param collection: Name of the collection.
        :param filter_query: Query filter.
        :param projection: Fields to include/exclude.
        :param sort: Dictionary of field: direction (1=ASC, -1=DESC).
        :param limit: Max number of documents to return.
        :param skip: Number of documents to skip.
        :return: List of documents.
        """
        col = self.db[collection]
        cursor = col.find(filter_query, projection)

        if sort:
            sort_list = [(field, ASCENDING if direction == 1 else DESCENDING) for field, direction in sort.items()]
            cursor = cursor.sort(sort_list)

        if skip > 0:
            cursor = cursor.skip(skip)

        if limit > 0:
            cursor = cursor.limit(limit)

        return [self._convert_objectid(doc) for doc in cursor]

    def aggregate(self, collection: str, pipeline: List[Dict]) -> List[Dict[str, Any]]:
        """
        Executes an aggregation pipeline.

        :return: List of aggregated documents.
        """
        col = self.db[collection]
        result = col.aggregate(pipeline)
        return [self._convert_objectid(doc) for doc in result]

    def count_documents(self, collection: str, filter_query: Dict = {}) -> int:
        """
        Counts the number of documents matching the filter.
        """
        col = self.db[collection]
        return col.count_documents(filter_query)

    def create_index(self, collection: str, field: str, unique: bool = False) -> str:
        """
        Creates an index on a field.

        :return: The name of the created index.
        """
        col = self.db[collection]
        return col.create_index([(field, ASCENDING)], unique=unique)

    def create_text_index(self, collection: str, fields: List[str]) -> str:
        """
        Creates a text index for full-text search.

        :param fields: List of fields to include in the text index.
        :return: Index name.
        """
        col = self.db[collection]
        index_fields = [(field, "text") for field in fields]
        return col.create_index(index_fields)

    def drop_index(self, collection: str, index_name: str) -> bool:
        """
        Drops an index by name.

        :return: True if successful, False otherwise.
        """
        col = self.db[collection]
        try:
            col.drop_index(index_name)
            return True
        except PyMongoError:
            return False

    def collection_exists(self, collection: str) -> bool:
        """
        Checks if a collection exists in the database.
        """
        return collection in self.db.list_collection_names()

    def create_collection(self, collection: str, options: Dict = None) -> bool:
        """
        Creates a new collection with optional options.

        :return: True if created, False if already exists or error occurred.
        """
        try:
            self.db.create_collection(collection, **(options or {}))
            return True
        except PyMongoError:
            return False

    def drop_collection(self, collection: str) -> bool:
        """
        Drops a collection.

        :return: True if dropped successfully.
        """
        try:
            self.db.drop_collection(collection)
            return True
        except PyMongoError:
            return False

    def bulk_write(self, collection: str, operations: List[Dict]) -> int:
        """
        Performs multiple write operations in bulk.

        Supported operations: insert, update, delete.

        :return: Total number of affected documents.
        """
        col = self.db[collection]
        from pymongo import InsertOne, UpdateOne, DeleteOne

        converted_ops = []
        for op in operations:
            if op['operation'] == 'insert':
                converted_ops.append(InsertOne(op['document']))
            elif op['operation'] == 'update':
                filter = op.get('filter', {})
                update = op.get('update', {})
                converted_ops.append(UpdateOne(filter, update))
            elif op['operation'] == 'delete':
                converted_ops.append(DeleteOne(op['filter']))

        result = col.bulk_write(converted_ops)
        return result.modified_count + result.inserted_count + result.deleted_count

    def _convert_objectid(self, document: Dict) -> Dict:
        """
        Converts the ObjectId of a document to string for serialization.
        """
        if '_id' in document:
            document['_id'] = str(document['_id'])
        return document
