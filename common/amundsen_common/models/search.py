# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, List, Optional, Dict

import attr

from marshmallow3_annotations.ext.attrs import AttrsSchema


@attr.s(auto_attribs=True, kw_only=True)
class HighlightOptions:
    enable_highlight: bool = False


class HighlightOptionsSchema(AttrsSchema):
    class Meta:
        target = HighlightOptions
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class Filter:
    name: str
    values: List[str]
    operation: str


class FilterSchema(AttrsSchema):
    class Meta:
        target = Filter
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class SearchRequest:
    query_term: str
    resource_types: List[str] = []
    page_index: Optional[int] = 0
    results_per_page: Optional[int] = 10
    filters: List[Filter] = []
    # highlight options are defined per resource
    highlight_options: Optional[Dict[str, HighlightOptions]] = {}


class SearchRequestSchema(AttrsSchema):
    class Meta:
        target = SearchRequest
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class SearchResponse:
    msg: str
    page_index: int
    results_per_page: int
    results: Dict[str, Any]
    status_code: int


class SearchResponseSchema(AttrsSchema):
    class Meta:
        target = SearchResponse
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class KnnSearchRequest:
    vector: List[float]
    resource_type: str
    filters: Optional[List[Filter]] = None
    results_count: Optional[int] = 10

class KnnSearchRequestSchema(AttrsSchema):
    class Meta:
        target = KnnSearchRequest
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class KnnSearchHit:
    score: float
    result: Dict[str, Any]

class KnnSearchHitSchema(AttrsSchema):
    class Meta:
        target = KnnSearchHit
        register_as_scheme = True

@attr.s(auto_attribs=True, kw_only=True)
class KnnSearchResponse:
    msg: str
    results: Optional[List[KnnSearchHit]] = None
    status_code: int


class KnnSearchResponseSchema(AttrsSchema):
    class Meta:
        target = KnnSearchResponse
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class HybridSearchRequest:
    # Text search parameters
    text_queries: List[str]  # List of text strings to search for
    resource_types: List[str] = []  # Empty list means search all resource types
    page_index: Optional[int] = 0
    results_per_page: Optional[int] = 10
    filters: List[Filter] = []
    highlight_options: Optional[Dict[str, HighlightOptions]] = {}

    # KNN search parameters
    knn_vectors: List[List[float]]  # List of vectors to search with
    knn_results_count: Optional[int] = 10  # Number of KNN results per vector


class HybridSearchRequestSchema(AttrsSchema):
    class Meta:
        target = HybridSearchRequest
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class HybridSearchHit:
    score: float
    result: Dict[str, Any]
    search_type: str  # "text" or "knn" to indicate which search found this result


class HybridSearchHitSchema(AttrsSchema):
    class Meta:
        target = HybridSearchHit
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class HybridSearchResponse:
    msg: str
    results: Optional[List[HybridSearchHit]] = None
    page_index: int
    results_per_page: int
    status_code: int


class HybridSearchResponseSchema(AttrsSchema):
    class Meta:
        target = HybridSearchResponse
        register_as_scheme = True


@attr.s(auto_attribs=True, kw_only=True)
class UpdateDocumentRequest:
    resource_key: str
    resource_type: str
    field: str
    value: Optional[str]
    operation: str  # can be add or overwrite


class UpdateDocumentRequestSchema(AttrsSchema):
    class Meta:
        target = UpdateDocumentRequest
        register_as_scheme = True
