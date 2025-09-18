# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import date
from typing import (
    Any, Generator, List,
)
from uuid import uuid4

import elasticsearch
from elasticsearch.exceptions import NotFoundError, ApiError
from elasticsearch.helpers import parallel_bulk
from elasticsearch_dsl.connections import Connections, connections
from elasticsearch_dsl.document import Document
from elasticsearch_dsl.index import Index
from pyhocon import ConfigTree

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.task.base_task import Task
from databuilder.task.search.document_mappings import RESOURCE_TO_MAPPING, SearchableResource
from databuilder.transformer.base_transformer import NoopTransformer, Transformer
from databuilder.utils.closer import Closer

LOGGER = logging.getLogger(__name__)


class SearchMetadatatoElasticasearchTask(Task):

    ENTITY_TYPE = 'doc_type'
    ELASTICSEARCH_CLIENT_CONFIG_KEY = 'client'
    MAPPING_CLASS = 'document_mapping'
    ELASTICSEARCH_ALIAS_CONFIG_KEY = 'alias'
    ELASTICSEARCH_NEW_INDEX = 'new_index'
    ELASTICSEARCH_PUBLISHER_BATCH_SIZE = 'batch_size'
    ELASTICSEARCH_TIMEOUT_SEC = 'es_timeout_sec'
    DATE = 'date'

    today = date.today().strftime("%Y%m%d")

    def __init__(self,
                 extractor: Extractor,
                 transformer: Transformer = NoopTransformer()) -> None:
        self.extractor = extractor
        self.transformer = transformer

        self._closer = Closer()
        self._closer.register(self.extractor.close)
        self._closer.register(self.transformer.close)

    def init(self, conf: ConfigTree) -> None:
        # initialize extractor with configurarion
        self.extractor.init(Scoped.get_scoped_conf(conf, self.extractor.get_scope()))
        # initialize transformer with configuration
        self.transformer.init(Scoped.get_scoped_conf(conf, self.transformer.get_scope()))

        # task configuration
        conf = Scoped.get_scoped_conf(conf, self.get_scope())
        self.date = conf.get_string(SearchMetadatatoElasticasearchTask.DATE, self.today)
        self.entity = conf.get_string(SearchMetadatatoElasticasearchTask.ENTITY_TYPE).lower()
        self.elasticsearch_client = conf.get(
            SearchMetadatatoElasticasearchTask.ELASTICSEARCH_CLIENT_CONFIG_KEY
        )
        self.elasticsearch_alias = conf.get(
            SearchMetadatatoElasticasearchTask.ELASTICSEARCH_ALIAS_CONFIG_KEY
        )
        self.elasticsearch_new_index = conf.get(
            SearchMetadatatoElasticasearchTask.ELASTICSEARCH_NEW_INDEX,
            self.create_new_index_name())
        self.document_mapping = conf.get(SearchMetadatatoElasticasearchTask.MAPPING_CLASS,
                                         RESOURCE_TO_MAPPING[self.entity])

        if not issubclass(self.document_mapping, SearchableResource):
            msg = "Provided document_mapping should be instance" \
                f" of SearchableResource not {type(self.document_mapping)}"
            LOGGER.error(msg)
            raise TypeError(msg)

        self.elasticsearch_batch_size = conf.get(
            SearchMetadatatoElasticasearchTask.ELASTICSEARCH_PUBLISHER_BATCH_SIZE, 100
        )
        self.elasticsearch_timeout_sec = conf.get(
            SearchMetadatatoElasticasearchTask.ELASTICSEARCH_TIMEOUT_SEC, 120
        )

    def create_new_index_name(self) -> str:
        hex_string = uuid4().hex
        return f"{self.elasticsearch_alias}_{self.date}_{hex_string}"

    def to_document(self, metadata: Any) -> Document:
        return self.document_mapping(_index=self.elasticsearch_new_index,
                                     **metadata)

    def generate_documents(self, record: Any) -> Generator:
        # iterate through records
        while record:
            record = self.transformer.transform(record)
            if not record:
                # Move on if the transformer filtered the record out
                record = self.extractor.extract()
                continue

            if hasattr(record, "items"):
                metadata = dict(record.items())
            else:
                metadata = dict(record)
            metadata.setdefault('resource_type', self.entity)

            document = self.to_document(metadata=metadata)

            if 'key' in metadata:
                document.meta.id = metadata["key"]

            yield document.to_dict(True)

            record = self.extractor.extract()

    def _get_old_index(self, connection: Connections) -> List[str]:
        """
        Retrieve all indices that currently have {elasticsearch_alias} alias
        :return: list of elasticsearch indices
        """
        try:
            indices = connection.indices.get_alias(name=self.elasticsearch_alias).keys()
            return indices
        except NotFoundError:
            LOGGER.warning("Received index not found error from Elasticsearch. " +
                        "The index doesn't exist for a newly created ES. It's OK on first run.")
            # return empty list on exception
            return []

    def _delete_old_index(self, connection: Connections, document_index: Index) -> None:
        alias_updates = []
        previous_index = self._get_old_index(connection=connection)
        for previous_index_name in previous_index:
            if previous_index_name != document_index._name:
                LOGGER.info(f"Deleting old index {previous_index_name}")
                alias_updates.append({"remove_index": {"index": previous_index_name}})
        alias_updates.append({"add": {
            "index": self.elasticsearch_new_index,
            "alias": self.elasticsearch_alias}})
        connection.indices.update_aliases(body={"actions": alias_updates})

    def _update_alias_and_delete_old_index(self, connection: Connections, document_index: Index) -> None:
        # STEP 1: Get the index currently associated with the alias (before updating it)
        try:
            alias_info = connection.indices.get_alias(name=self.elasticsearch_alias)
            old_index = list(alias_info.keys())[0]  # assuming one-to-one mapping
        except elasticsearch.exceptions.NotFoundError:
            old_index = None

        # STEP 2: Move alias to new index
        alias_actions = []
        if old_index and old_index != self.elasticsearch_new_index:
            alias_actions.append({
                "remove": {"index": old_index, "alias": self.elasticsearch_alias}
            })
        alias_actions.append({
            "add": {"index": self.elasticsearch_new_index, "alias": self.elasticsearch_alias}
        })

        LOGGER.info(f"Updating alias {self.elasticsearch_alias} to point to {self.elasticsearch_new_index}")
        connection.indices.update_aliases(body={"actions": alias_actions})

        # STEP 3: Delete only the previously aliased index, if it still exists and is not locked
        if old_index and old_index != self.elasticsearch_new_index:
            try:
                settings = self.elasticsearch_client.indices.get_settings(index=old_index)
                index_settings = settings.get(old_index, {}).get('settings', {}).get('index', {})
                is_read_only = index_settings.get('blocks', {}).get('read_only', 'false') == 'true'
                if is_read_only:
                    LOGGER.info(f"Attempting to delete old index: {old_index}")
                    connection.indices.delete(index=old_index)
                    LOGGER.info(f"Successfully deleted old index: {old_index}")
                else:
                    LOGGER.info(f"Delete lock set on index {old_index}...skipping")
            except elasticsearch.exceptions.AuthorizationException as e:
                if "cluster_block_exception" in str(e):
                    LOGGER.warning(f"Delete blocked by index.blocks.delete on {old_index}")
                else:
                    raise

    def _delete_unaliased_indices(self):
        try:
            all_indices = self.elasticsearch_client.indices.get(index=f"{self.elasticsearch_alias}*")
        except NotFoundError:
            LOGGER.info("No indices found with that prefix.")
            return

        for index_name in all_indices:
            try:
                alias_info = self.elasticsearch_client.indices.get_alias(index=index_name)
                if alias_info.get(index_name, {}).get("aliases"):
                    LOGGER.info(f"Skipping index {index_name}: has alias.")
                    continue
            except NotFoundError:
                # If the index doesn't exist anymore
                continue

            try:
                LOGGER.info(f"Deleting index: {index_name}")
                self.elasticsearch_client.indices.delete(index=index_name)
            except ApiError as e:
                LOGGER.warning(f"Failed to delete {index_name}: {e.info}")

    def run(self) -> None:
        LOGGER.info('Running search metadata to Elasticsearch task')
        try:
            # extract records from metadata store
            record = self.extractor.extract()

            # create connection
            connections.add_connection(alias='default', conn=self.elasticsearch_client)
            connection = connections.get_connection()

            # health check ES
            health = connection.cluster.health()
            status = health["status"]
            if status not in ("green", "yellow"):
                msg = f"Elasticsearch healthcheck failed: {status}"
                LOGGER.error(msg)
                raise Exception(msg)

            # create index
            LOGGER.info(f"Creating ES index {self.elasticsearch_new_index}")
            index = Index(name=self.elasticsearch_new_index, using=self.elasticsearch_client)
            index.document(self.document_mapping)

            # allow for longer ngram length
            index.settings(max_shingle_diff=10)

            index.create()

            # publish search metadata to ES
            cnt = 0
            for success, info in parallel_bulk(connection,
                                               self.generate_documents(record=record),
                                               raise_on_error=False,
                                               chunk_size=self.elasticsearch_batch_size,
                                               request_timeout=self.elasticsearch_timeout_sec):
                if not success:
                    LOGGER.warning(f"There was an error while indexing a document to ES: {info}")
                else:
                    cnt += 1
                if cnt == self.elasticsearch_batch_size:
                    LOGGER.info(f'Published {str(cnt*self.elasticsearch_batch_size)} records to ES')

            # delete old index
            self._update_alias_and_delete_old_index(connection=connection,
                                                    document_index=index)

            self._delete_unaliased_indices()
            LOGGER.info("Elasticsearch Indexing completed")
        finally:
            self._closer.close()

    def get_scope(self) -> str:
        return 'task.search_metadata_to_elasticsearch'
