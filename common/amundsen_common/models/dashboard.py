# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Literal, Optional
import attr
from marshmallow import EXCLUDE, pre_load
from marshmallow3_annotations.ext.attrs import AttrsSchema

from amundsen_common.models.user import User
from amundsen_common.models.badge import Badge
from amundsen_common.models.tag import Tag



@attr.s(auto_attribs=True, kw_only=True)
class DashboardSummary:
    uri: str = attr.ib()
    cluster: str = attr.ib()
    group_name: str = attr.ib()
    group_url: str = attr.ib()
    product: str = attr.ib()
    name: str = attr.ib()
    url: str = attr.ib()
    description: Optional[str] = None
    last_successful_run_timestamp: Optional[float] = None
    chart_names: Optional[List[str]] = []


class DashboardSummarySchema(AttrsSchema):
    class Meta:
        target = DashboardSummary
        register_as_scheme = True
        unknown = EXCLUDE


@attr.s(auto_attribs=True, kw_only=True)
class DashboardGroup:
    key: Optional[str] = None
    product: str
    cluster: str
    dashboard_group_name: str
    url: Optional[str] = None
    description: Optional[str] = None

class DashboardGroupSchema(AttrsSchema):
    class Meta:
        target = DashboardGroup
        register_as_scheme = True
        unknown = EXCLUDE

@attr.s(auto_attribs=True, kw_only=True)
class DashboardChart:
    key: Optional[str] = None
    product: str
    cluster: str
    dashboard_group_name: str
    dashboard_name: str
    dashboard_query_name: str
    chart_name: Optional[str] = None,
    chart_type: Optional[str] = None,
    chart_url: Optional[str] = None,

class DashboardChartSchema(AttrsSchema):
    class Meta:
        target = DashboardChart
        register_as_scheme = True
        unknown = EXCLUDE

@attr.s(auto_attribs=True, kw_only=True)
class DashboardQueryExecution:
    key: Optional[str] = None
    product: str
    cluster: str
    dashboard_group_name: str
    dashboard_name: str
    dashboard_query_name: str
    query_execution_timestamp: int
    query_execution_state: str
    query_execution_name: str = '_last_execution'

class DashboardQueryExecutionSchema(AttrsSchema):
    class Meta:
        target = DashboardQueryExecution
        register_as_scheme = True
        unknown = EXCLUDE

@attr.s(auto_attribs=True, kw_only=True)
class DashboardQuery:
    key: Optional[str] = None
    product: str
    cluster: str
    dashboard_group_name: str
    dashboard_name: str
    dashboard_query_name: str
    query_statement: str
    query_url: Optional[str] = None
    charts: Optional[List[DashboardChart]] = None
    last_execution: Optional[DashboardQueryExecution] = None

class DashboardQuerySchema(AttrsSchema):
    class Meta:
        target = DashboardQuery
        register_as_scheme = True
        unknown = EXCLUDE

    @pre_load
    def inject_key_context(self, data, **kwargs):
        product = data.get("product")
        cluster = data.get("cluster")
        dashboard_group_name = data.get("dashboard_group_name")
        dashboard_name = data.get("dashboard_name")
        dashboard_query_name = data.get("dashboard_query_name")

        charts = data.get("charts", None)
        if charts:
            for chart in charts:
                chart.setdefault("product", product)
                chart.setdefault("cluster", cluster)
                chart.setdefault("dashboard_group_name", dashboard_group_name)
                chart.setdefault("dashboard_name", dashboard_name)
                chart.setdefault("dashboard_query_name", dashboard_query_name)

        last_execution = data.get("last_execution", None)
        if last_execution:
            last_execution.setdefault("product", product)
            last_execution.setdefault("cluster", cluster)
            last_execution.setdefault("dashboard_group_name", dashboard_group_name)
            last_execution.setdefault("dashboard_name", dashboard_name)
            last_execution.setdefault("dashboard_query_name", dashboard_query_name)

        return data

@attr.s(auto_attribs=True, kw_only=True)
class DashboardLastModifiedTimestamp:
    key: Optional[str] = None
    product: str
    cluster: str
    dashboard_group_name: str
    dashboard_name: str
    last_modified_timestamp: int

class DashboardLastModifiedTimestampSchema(AttrsSchema):
    class Meta:
        target = DashboardLastModifiedTimestamp
        register_as_scheme = True
        unknown = EXCLUDE

@attr.s(auto_attribs=True, kw_only=True)
class Dashboard:
    key: Optional[str] = None
    product: str
    cluster: str
    dashboard_group_name: str
    dashboard_name: str
    url: Optional[str] = None
    description: Optional[str] = None
    created_timestamp: Optional[int] = None,
    tags: Optional[List[str]] = None
    owners: Optional[List[str]] = None
    dashboard_group: Optional[DashboardGroup] = None
    dashboard_queries: Optional[List[DashboardQuery]] = None
    dashboard_last_modified_timestamp: Optional[DashboardLastModifiedTimestamp] = None

class DashboardSchema(AttrsSchema):
    class Meta:
        target = Dashboard
        register_as_scheme = True
        unknown = EXCLUDE

    @pre_load
    def inject_key_context(self, data, **kwargs):
        product = data.get("product")
        cluster = data.get("cluster")
        dashboard_group_name = data.get("dashboard_group_name")
        dashboard_name = data.get("dashboard_name")

        dashboard_group = data.get("dashboard_group", None)
        if dashboard_group:
            dashboard_group.setdefault("product", product)
            dashboard_group.setdefault("cluster", cluster)
            dashboard_group.setdefault("dashboard_group_name", dashboard_group_name)

        queries = data.get("dashboard_queries", None)
        if queries:
            for query in queries:
                query.setdefault("product", product)
                query.setdefault("cluster", cluster)
                query.setdefault("dashboard_group_name", dashboard_group_name)
                query.setdefault("dashboard_name", dashboard_name)

                charts = query.get("charts", None)
                if charts:
                    dashboard_query_name = query.get("dashboard_query_name")
                    for chart in charts:
                        chart.setdefault("product", product)
                        chart.setdefault("cluster", cluster)
                        chart.setdefault("dashboard_group_name", dashboard_group_name)
                        chart.setdefault("dashboard_name", dashboard_name)
                        chart.setdefault("dashboard_query_name", dashboard_query_name)

                last_execution = query.get("last_execution", None)
                if last_execution:
                    last_execution.setdefault("product", product)
                    last_execution.setdefault("cluster", cluster)
                    last_execution.setdefault("dashboard_group_name", dashboard_group_name)
                    last_execution.setdefault("dashboard_name", dashboard_name)
                    last_execution.setdefault("dashboard_query_name", dashboard_query_name)

        dashboard_last_modified_timestamp = data.get("dashboard_last_modified_timestamp", None)
        if dashboard_last_modified_timestamp:
            dashboard_last_modified_timestamp.setdefault("product", product)
            dashboard_last_modified_timestamp.setdefault("cluster", cluster)
            dashboard_last_modified_timestamp.setdefault("dashboard_group_name", dashboard_group_name)
            dashboard_last_modified_timestamp.setdefault("dashboard_name", dashboard_name)

        return data

