# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Optional, Dict


class Priority():
    def __init__(self, level: str, jira_severity: str):
        self.level = level
        self.jira_severity = jira_severity

    def __repr__(self):
        return f"Priority(level={self.level}, jira_severity={self.jira_severity})"


class PriorityConfig():
    P0 = Priority('P0', 'Blocker')
    P1 = Priority('P1', 'Critical')
    P2 = Priority('P2', 'Major')
    P3 = Priority('P3', 'Minor')

    @classmethod
    def override_jira_severities(cls, jira_severity_overrides: dict):
        """Override JIRA severities dynamically at runtime."""
        for level, new_severity in jira_severity_overrides.items():
            if level in cls.__dict__:  # Ensure the Enum level exists
                cls.__dict__[level].jira_severity = new_severity

    @staticmethod
    def from_jira_severity(jira_severity: str) -> Optional['Priority']:
        """Find Priority by jira_severity, including overrides."""
        for _, p in PriorityConfig.__dict__.items():
            if isinstance(p, Priority) and p.jira_severity == jira_severity:
                return p
        return None  # Return None if not found

    @staticmethod
    def from_level(level: str) -> Optional['Priority']:
        """Find Priority by level."""
        return PriorityConfig.__dict__.get(level)

    @staticmethod
    def get_jira_severity_from_level(level: str) -> str:
        """Return jira_severity based on level, defaulting to P3."""
        if level in PriorityConfig.__dict__:
            return PriorityConfig.__dict__.get(level).jira_severity
        return PriorityConfig.P3.jira_severity  # Default to P3 if not found


class DataIssue:
    def __init__(self,
                 issue_key: str,
                 title: str,
                 url: str,
                 status: str,
                 priority: Optional[Priority]) -> None:
        self.issue_key = issue_key
        self.title = title
        self.url = url
        self.status = status
        self.priority = priority

    def serialize(self) -> dict:
        return {'issue_key': self.issue_key,
                'title': self.title,
                'url': self.url,
                'status': self.status,
                'priority_name': self.priority.jira_severity.lower() if self.priority else None,
                'priority_display_name': self.priority.level if self.priority else None}

# print(PriorityConfig.__dict__)
# print(PriorityConfig.from_jira_severity("Blocker"))
# PriorityConfig.override_jira_severities({"P0": "test"})
# print(PriorityConfig.P0.jira_severity)