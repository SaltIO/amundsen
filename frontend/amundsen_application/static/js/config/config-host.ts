// This file should be used to add new config variables or overwrite defaults from config-default.ts

import { AppConfigCustom } from './config-types';

import googleAnalytics from '@analytics/google-analytics';
import googleTagManager from '@analytics/google-tag-manager';

const configHost: AppConfigCustom = {
  logoPath: '/static/images/cmdrvl-logo.png',
  logoTitle: 'Salt.io',
  indexDashboards: {
    enabled: true,
  },
  indexUsers: {
    enabled: true,
  },
  indexFiles: {
    enabled: true,
  },
  indexProviders: {
    enabled: true,
  },
  navLinks: [
    {
      label: 'Data Stories',
      id: 'nav::anaytics',
      href: 'https://count.co/connection/XM8NhhgFhAq',
      use_router: false,
      target: '_blank'
    },
    {
      label: 'Data Pipelines',
      id: 'nav::automation',
      href: 'https://salt.cmdrvl.com/airflow',
      use_router: false,
      target: '_blank'
    },
    {
      label: 'Announcements',
      id: 'nav::announcements',
      href: '/announcements',
      use_router: true,
    },
    {
      label: 'Browse',
      id: 'nav::browse',
      href: '/browse',
      use_router: true,
    },
    {
      label: 'Issues',
      id: 'nav::issues',
      href: 'https://foodtruck.atlassian.net/jira/software/c/projects/SDD/boards/10',
      use_router: false,
      target: '_blank'
    },
  ],
  analytics: {
    plugins: [
      googleAnalytics({
        measurementIds: 'G-W2N0GCH0N9',
        sampleRate: 100
      }),
      googleTagManager({
        containerId: 'GT-KFLHZL9'
      })
    ],
  },
  ai: {
    enabled: true
  },
  snowflake: {
    enabled: true,
    shares: {
      enabled: true
    }
  },
};

export default configHost;
