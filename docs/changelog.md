# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Each revision is versioned by the date of the revision.

## 2026-11-27

- Added the Security explanation page outlining security risks and best practices for the Indico charm.

## 2026-11-20

- Terraform modules now require the Juju Terraform provider `>= 1.0, < 3.0`.

## 2026-11-17

- Added the list of plugins shipped with the charm to the Plugins reference page.

## 2026-11-16

- Added the `valkey` integration for caching and the Celery message broker. The `redis` integration is kept for existing deployments; if both are integrated, the charm uses Valkey.

## 2026-01-12

- Plugin installations now only fixes Indico version, any other packages may change as long as they don't break Indico requirements.

## 2026-01-05

- Plugin installations now does not change installed Python packages.

## 2025-12-17

- Moved charm-architecture.md from Explanation to Reference category.

### 2025-06-06

- Add Service Health Grafana dashboard.

### 2025-04-14

- Add how-to landing page.
- Add changelog for tracking user-relevant changes.
