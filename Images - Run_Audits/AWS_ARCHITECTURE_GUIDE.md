# AWS Architecture Guide — Data Ingestion & Data Exploitation

This document outlines the solution patterns and AWS services needed to satisfy **Part 2** of the HDB Technical Test for Senior Data Engineer. 

You can use the details below to construct your architecture diagrams (using draw.io, PowerPoint, or similar tools) and document your design assumptions for your submission.

---

## 1. Architecture Overview & Network Segmentation

To ensure security, scalability, and performance, HDB’s data platform must reside inside a **Virtual Private Cloud (VPC)**. The network is segmented into **Public Subnets** (for routing outbound-only traffic to the internet) and **Private Subnets** (for data processing, storage, and exploitation tools).

```
┌────────────────────────────────────────────────────────────────────────┐
│                              AWS VPC                                   │
│  ┌─────────────────────────┐             ┌──────────────────────────┐  │
│  │     Public Subnet       │             │      Private Subnet      │  │
│  │                         │             │                          │  │
│  │    [ NAT Gateway ] ◄────┼─────────────┼─── [ Ingestion Job ]     │  │
│  └──────────┬──────────────┘             │    (Glue / ECS Fargate)  │  │
│             │                            │                          │  │
│             ▼ Outbound HTTPS             │    [ Tableau Server ]    │  │
│      [ Public Internet ]                 │    (Hosted on EC2)       │  │
│             │                            │            │             │  │
│             ▼                            │            ▼ Athena JDBC │  │
│     [ data.gov.sg API ]                  │    [ Athena Endpoint ]   │  │
│                                          │      (VPC Endpoint)      │  │
│                                          └────────────┬─────────────┘  │
│                                                       │                │
│                                                       ▼                │
│                                               [ Amazon Athena ]        │
│                                                       │                │
│                                                       ▼                │
│                                              [ AWS S3 Bucket ]         │
│                                            (S3 VPC Gateway Endpoint)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Ingestion Architecture (Batch Ingestion)

### Requirements Met:
- Batch ingestion of files > 100 MB.
- Public-facing source (data.gov.sg API) routed into a Private VPC.
- Network segmentation for maximum security.

### Core AWS Services to Include in Your Ingestion Diagram:

#### 1. **Amazon VPC (Public & Private Subnets)**
- The data ingestion script runs entirely in a **Private Subnet** (no direct inbound internet access).
- **NAT Gateway (in the Public Subnet)**: Placed in the public subnet with an Elastic IP to allow the ingestion job in the private subnet to initiate outbound HTTPS requests to the data.gov.sg API.
- **Internet Gateway (IGW)**: Attached to the VPC to allow the NAT Gateway to route requests to the public internet.

#### 2. **AWS Glue (ETL Job) OR AWS ECS (Fargate)**
- **AWS Glue (Python Shell or PySpark)**: The ideal service for running the ingestion python script. It is serverless, fully managed, and can easily run on a schedule.
- **AWS ECS (Fargate)**: An alternative choice. Run the ingestion python script as a Docker container in a serverless task.
- *Glue/ECS Fargate easily handles > 100 MB files as it has high network throughput and ephemeral storage.*

#### 3. **Amazon EventBridge (Scheduler)**
- Triggers the ingestion job (Glue or ECS task) on a cron-like schedule (e.g., daily or monthly).

#### 4. **Amazon S3 Gateway VPC Endpoint**
- A **Gateway Endpoint** for S3 is configured in the VPC. This ensures that the ingestion job writes the downloaded data to S3 over a **private AWS connection**, bypassing the NAT Gateway and keeping the data within the AWS backbone.

---

## 3. Data Exploitation Architecture (Tableau & Athena)

### Requirements Met:
- Data integration via Tableau using the Athena JDBC/ODBC Driver.
- Private traffic routing when calling the AWS Athena public endpoint.

### Core AWS Services to Include in Your Exploitation Diagram:

#### 1. **Tableau Server / Desktop on AWS**
- Hosted on **Amazon EC2** instances running in the **Private Subnet** of the VPC.

#### 2. **Amazon Athena**
- Serves as the interactive query engine that reads the processed datasets directly from S3 (Raw, Cleaned, Transformed, Hashed) using SQL.

#### 3. **AWS Glue Data Catalog**
- Acts as the metadata schema database. The schemas of the S3 CSV files are registered here as tables (via Glue Crawlers or CloudFormation) so that Athena knows how to query them.

#### 4. **Interface VPC Endpoint (AWS PrivateLink) for Athena**
- *This is the most critical security configuration.*
- Usually, the Athena JDBC Driver connects to `athena.<region>.amazonaws.com` (a public endpoint).
- By creating an **Interface VPC Endpoint** for Athena (`com.amazonaws.<region>.athena`) in the Private Subnet, all queries sent by Tableau are routed via a local private IP address directly to the Athena service.
- The traffic **never traverses the public internet** or the NAT Gateway.

#### 5. **Amazon S3 Gateway VPC Endpoint (Shared)**
- Allows Athena to retrieve the raw data from S3, and write the query results back to the S3 query results bucket privately.

---

## 4. Governance, Security & Best Practices (Additional Points)

Including these services will demonstrate senior solutioning competencies to the HDB evaluators:

- **AWS IAM Roles & Policies**:
  - The ingestion job (Glue/ECS) is assigned an IAM role allowing it to put objects in the S3 bucket.
  - The Tableau EC2 instance (or Athena connection) is assigned an IAM role allowing it to query Athena and read from S3.
- **AWS Key Management Service (KMS)**:
  - All S3 buckets are encrypted using customer-managed KMS keys (SSE-KMS).
  - Athena query results and catalog metadata are also encrypted with KMS.
- **Amazon CloudWatch**:
  - Monitors Glue ETL logs, execution times, failures, and triggers notifications on error.

---

## 5. Summary of Recommended Connections for your Diagram

When drawing the diagram, ensure the following arrows/flows are visible:

1. **Ingest flow**:
   `EventBridge Scheduler` ──▶ `Glue Ingestion Job (Private Subnet)` ──▶ `NAT Gateway (Public Subnet)` ──▶ `Internet` ──▶ `data.gov.sg API` (Outbound only).
 2. **Write flow**:
   `Glue Ingestion Job (Private Subnet)` ──▶ `S3 Gateway Endpoint` ──▶ `S3 Bucket` (Private network).
 3. **Query flow**:
   `Tableau Server (Private Subnet)` ──▶ `Athena Interface VPC Endpoint (PrivateLink)` ──▶ `Amazon Athena` ──▶ `S3 Bucket` (Private network).
