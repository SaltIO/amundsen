import logging
import os
import sys
import uuid

from pyhocon import ConfigFactory, ConfigTree
from sqlalchemy.ext.declarative import declarative_base

from databuilder.extractor.es_last_updated_extractor import EsLastUpdatedExtractor
from databuilder.extractor.neo4j_search_data_extractor import Neo4jSearchDataExtractor
from databuilder.job.job import DefaultJob
from databuilder.loader.file_system_neo4j_csv_loader import FsNeo4jCSVLoader
from databuilder.publisher.neo4j_csv_publisher import Neo4jCsvPublisher
from databuilder.task.task import DefaultTask
from databuilder.transformer.base_transformer import ChainedTransformer, NoopTransformer
from databuilder.transformer.dict_to_model import MODEL_CLASS, DictToModel
from databuilder.transformer.generic_transformer import (
    CALLBACK_FUNCTION, FIELD_NAME, GenericTransformer,
)

neo_host = os.getenv('CREDENTIALS_NEO4J_PROXY_HOST', 'localhost')
neo_port = os.getenv('CREDENTIALS_NEO4J_PROXY_PORT', 7687)

Base = declarative_base()

NEO4J_ENDPOINT = f'bolt://{neo_host}:{neo_port}'

neo4j_endpoint = NEO4J_ENDPOINT

neo4j_user = 'neo4j'
neo4j_password = 'test'

LOGGER = logging.getLogger(__name__)

from typing import (
    Any, Dict, Iterator, List, Union,
)

from pyhocon import ConfigTree
from simple_salesforce import Salesforce

from databuilder.extractor.base_extractor import Extractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata


class CustomSalesForceExtractor(Extractor):
    """
    Extracts SalesForce objects
    """

    # CONFIG KEYS
    CLUSTER_KEY = 'cluster_key'
    SCHEMA_KEY = 'schema_key'
    DATABASE_KEY = 'database_key'
    OBJECT_NAMES_KEY = "object_names"
    USERNAME_KEY = "username"
    PASSWORD_KEY = "password"
    SECURITY_TOKEN_KEY = "security_token"

    def init(self, conf: ConfigTree) -> None:

        self._cluster: str = conf.get_string(CustomSalesForceExtractor.CLUSTER_KEY, "gold")
        self._database: str = conf.get_string(CustomSalesForceExtractor.DATABASE_KEY)
        self._schema: str = conf.get_string(CustomSalesForceExtractor.SCHEMA_KEY)
        self._object_names: List[str] = conf.get_list(CustomSalesForceExtractor.OBJECT_NAMES_KEY, [])

        self._client: Salesforce = Salesforce(
            username=conf.get_string(CustomSalesForceExtractor.USERNAME_KEY),
            password=conf.get_string(CustomSalesForceExtractor.PASSWORD_KEY),
            security_token=conf.get_string(CustomSalesForceExtractor.SECURITY_TOKEN_KEY),
        )

        self._extract_iter: Union[None, Iterator] = None

    def extract(self) -> Union[TableMetadata, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Extract the TableMetaData for each SalesForce Object
        :return:
        """

        # Filter the sobjects if `OBJECT_NAMES_KEY` is set otherwise return all
        sobjects = [
            sobject
            for sobject in self._client.describe()["sobjects"]
            if (len(self._object_names) == 0 or sobject["name"] in self._object_names)
        ]

        for i, sobject in enumerate(sobjects):
            object_name = sobject["name"]
            logging.info(
                f"({i+1}/{len(sobjects)}) Extracting SalesForce object ({object_name})"
            )
            data = self._client.restful(path=f"sobjects/{object_name}/describe")
            yield self._extract_table_metadata(object_name=object_name, data=data)

            if 'urls' in data:
                if 'listviews' in data['urls']:
                    listviews = self._client.restful(path=f"sobjects/{object_name}/listviews")
                    for i, vname in enumerate(listviews['listviews']):
                        print(
                            f"Extracting SalesForce list view ({vname['developerName']})"
                        )
                        try:
                            vdata = self._client.restful(path=f"sobjects/{object_name}/listviews/{vname['id']}/describe")
                            yield self._extract_view_metadata(object_name=vname['developerName'], data=vdata)
                        except:
                            print('Error')

    def _calc_badges(self, f: Dict[str, Any]) -> List[str]:
        badges = []
        if 'searchable' in f:
            if f['searchable'] is True:
                badges.append('Searchable')
        if 'hidden' in f:
            if f['hidden'] is True:
                badges.append('Hidden')
        if 'calculated' in f:
            if f['calculated'] is True:
                badges.append('Calculated')
        return badges

    def _extract_view_metadata(
        self, object_name: str, data: Dict[str, Any]
    ) -> TableMetadata:
        # sort the fields by name because Amundsen requires a sort order for the columns and I did
        # not see one in the response
        fields = sorted(data["columns"], key=lambda x: x["fieldNameOrPath"])
        columns = [
            ColumnMetadata(
                name=f["fieldNameOrPath"],
                description=f["label"],
                col_type=f["type"],
                sort_order=i,
                badges=self._calc_badges(f)
            )
            for i, f in enumerate(fields)
        ]
        return TableMetadata(
            database=self._database,
            cluster=self._cluster,
            schema=self._schema,
            name=object_name,
            is_view=True,
            description=None,
            columns=columns,
            tags="View"
        )

    def _extract_table_metadata(
        self, object_name: str, data: Dict[str, Any]
    ) -> TableMetadata:
        # sort the fields by name because Amundsen requires a sort order for the columns and I did
        # not see one in the response
        fields = sorted(data["fields"], key=lambda x: x["name"])
        columns = [
            ColumnMetadata(
                name=f["name"],
                description=f["inlineHelpText"],
                col_type=f["type"],
                sort_order=i,
                badges=self._calc_badges(f)
            )
            for i, f in enumerate(fields)
        ]
        return TableMetadata(
            database=self._database,
            cluster=self._cluster,
            schema=self._schema,
            name=object_name,
            # TODO: Can we extract table description / does it exist?
            description=None,
            columns=columns,
        )

    def get_scope(self) -> str:
        return 'extractor.salesforce_metadata'

def run_salesforce_job(username, password, token):
    tmp_folder = f'/var/tmp/amundsen/salesforce'
    node_files_folder = f'{tmp_folder}/nodes'
    relationship_files_folder = f'{tmp_folder}/relationships'

    sf_extractor = CustomSalesForceExtractor()
    csv_loader = FsNeo4jCSVLoader()

    task = DefaultTask(extractor=sf_extractor,
                       loader=csv_loader,
                       transformer=NoopTransformer())

    job_config = ConfigFactory.from_dict({
        'extractor.salesforce_metadata.cluster_key': 'production',
        'extractor.salesforce_metadata.database_key': 'creos',
        'extractor.salesforce_metadata.schema_key': 'cre',
        'extractor.salesforce_metadata.username': username,
        'extractor.salesforce_metadata.password': password,
        'extractor.salesforce_metadata.security_token': token,
        'loader.filesystem_csv_neo4j.node_dir_path': node_files_folder,
        'loader.filesystem_csv_neo4j.relationship_dir_path': relationship_files_folder,
        #'loader.filesystem_csv_neo4j.delete_created_directories': True,
        'publisher.neo4j.node_files_directory': node_files_folder,
        'publisher.neo4j.relation_files_directory': relationship_files_folder,
        'publisher.neo4j.neo4j_endpoint': neo4j_endpoint,
        'publisher.neo4j.neo4j_user': neo4j_user,
        'publisher.neo4j.neo4j_password': neo4j_password,
        'publisher.neo4j.neo4j_encrypted': False,
        # should use unique tag here like {ds}
        'publisher.neo4j.job_publish_tag': 'unique_tag',
    })

    DefaultJob(conf=job_config,
               task=task,
               publisher=Neo4jCsvPublisher()).launch()
