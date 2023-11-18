import axios, { AxiosResponse } from 'axios';
import { Issue, CreateIssuePayload, NotificationPayload } from 'interfaces';
import { notificationsEnabled } from 'config/config-utils';

export const API_PATH = '/api/issue';
export const NOTIFICATION_API_PATH = '/api/mail/v0/notification';

export type IssuesAPI = {
  issues: {
    issues: Issue[];
    total: number;
    open_count: number;
    all_issues_url: string;
    open_issues_url: string;
    closed_issues_url: string;
  };
};

export type IssueApi = {
  issue: Issue;
};

export function getIssues(issue_type: string, key: string) {
  return axios
    .get(`${API_PATH}/issues?issue_type=${issue_type}&key=${key}`)
    .then((response: AxiosResponse<IssuesAPI>) => response.data.issues);
}

export function createIssue(
  payload: CreateIssuePayload,
  notificationPayload: NotificationPayload
) {
  return axios
    .post(`${API_PATH}/issue`, {
      issue_type: payload.issue_type,
      key: payload.key,
      title: payload.title,
      description: payload.description,
      owner_ids: payload.owner_ids,
      frequent_user_ids: payload.frequent_user_ids,
      priority_level: payload.priority_level,
      project_key: payload.project_key,
      resource_path: payload.resource_path,
    })
    .then((response: AxiosResponse<IssueApi>) => {
      if (notificationsEnabled()) {
        notificationPayload.options.data_issue_url = response.data.issue.url;
        axios.post(NOTIFICATION_API_PATH, notificationPayload);
      }

      return response.data.issue;
    });
}
