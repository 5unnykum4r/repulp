# System Architecture Guide

**Author:** Engineering Team | **Version:** 2.0 | **Last Updated:** December 2025

## Overview

The Acme Platform follows a modular microservices architecture deployed on
Kubernetes. Services communicate via gRPC for internal calls and expose REST
APIs for external consumers. All data flows through a central event bus
(Apache Kafka) for asynchronous processing.

## Service Topology

### Core Services

| Service         | Tech Stack       | Database                   | Responsibility                                   |
| --------------- | ---------------- | -------------------------- | ------------------------------------------------ |
| API Gateway     | Envoy Proxy      | None                       | Auth, rate limiting, routing, TLS termination    |
| User Service    | Go + gRPC        | PostgreSQL                 | Accounts, authentication, sessions, permissions  |
| Project Service | Go + gRPC        | PostgreSQL (pg\_trgm)      | Project CRUD, member management, settings        |
| Billing Service | Python + FastAPI | PostgreSQL (separate, PCI) | Subscriptions, usage tracking, invoicing, Stripe |

### Supporting Services

| Service              | Tech Stack       | Database                    | Responsibility                           |
| -------------------- | ---------------- | --------------------------- | ---------------------------------------- |
| Notification Service | Node.js          | Redis (queue)               | Email (SES), Slack, webhook delivery     |
| Search Service       | Python + FastAPI | Elasticsearch 8.x           | Full-text search, filters, facets        |
| File Service         | Go               | S3 + metadata in PostgreSQL | Uploads, virus scanning, thumbnails, CDN |

## Infrastructure

### Kubernetes Clusters

| Cluster      | Region    | Nodes | Purpose            |
| ------------ | --------- | ----- | ------------------ |
| prod-us-east | us-east-1 | 12    | Primary production |
| prod-eu-west | eu-west-1 | 8     | EMEA traffic       |
| staging      | us-east-1 | 4     | Pre-production     |
| dev          | us-east-1 | 2     | Development        |

### Data Stores

| Technology    | Version | Use Case           | Hosting                   |
| ------------- | ------- | ------------------ | ------------------------- |
| PostgreSQL    | 16      | Transactional data | RDS Multi-AZ              |
| Elasticsearch | 8.x     | Search indices     | 3-node cluster            |
| Redis         | 7       | Caching, sessions  | ElastiCache               |
| Apache Kafka  | 3.6     | Event streaming    | MSK                       |
| S3            | N/A     | Object storage     | AWS (intelligent tiering) |

## Request Lifecycle

1. Client sends HTTPS request to the load balancer
2. Load balancer routes to API Gateway (Envoy)
3. Gateway validates JWT token with User Service
4. Gateway routes request to the appropriate backend service
5. Backend service processes request, writes to its database
6. Backend service publishes event to Kafka
7. Downstream services consume events asynchronously
8. Response flows back through Gateway to client

## Kafka Topics

| Topic                  | Schema | Producers       | Consumers                   |
| ---------------------- | ------ | --------------- | --------------------------- |
| `acme.users.events`    | Avro   | User Service    | Search, Notification, Audit |
| `acme.projects.events` | Avro   | Project Service | Search, Notification        |
| `acme.billing.events`  | Avro   | Billing Service | Notification, Audit         |
| `acme.audit.log`       | Avro   | All services    | Audit Service, S3 archiver  |

## Monitoring Stack

* **Prometheus + Grafana** for metrics and dashboards
* **Jaeger** for distributed tracing (10% sample rate)
* **ELK Stack** for log aggregation
* **PagerDuty** for on-call alerting
* **Datadog** for APM and infrastructure monitoring

## Security

### Network

* All inter-service communication uses mTLS
* Network policies restrict pod-to-pod communication
* WAF rules on API Gateway block common attack patterns
* DDoS protection via CloudFront and AWS Shield

### Data

* Encryption at rest (AES-256) for all databases
* Encryption in transit (TLS 1.3) for all connections
* PII fields use application-level encryption with rotating keys
* Database credentials managed via HashiCorp Vault

### Compliance

| Standard            | Status                              | Audit Frequency      |
| ------------------- | ----------------------------------- | -------------------- |
| SOC 2 Type II       | Certified                           | Annual               |
| GDPR                | Compliant (data residency controls) | Continuous           |
| HIPAA               | Ready (BAA available)               | Annual               |
| Penetration Testing | Passed                              | Annual (third-party) |