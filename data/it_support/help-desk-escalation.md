---
department: IT Support
last_updated: 2026-03-15
category: Operations
audience: IT Staff
---

# Help Desk Escalation Procedures

## Overview
SkyWing Airlines relies on a structured, multi-tier IT support model to ensure timely and effective resolution of technical issues. This document outlines the escalation procedures for Help Desk staff and provides guidance on when and how to escalate tickets to specialized teams.

## Support Tiers and Responsibilities

### Tier 1 (Help Desk Analysts)
- **Primary Focus**: Initial contact, basic troubleshooting, and ticket categorization.
- **Responsibilities**: Password resets, basic software installation, email configuration, and mobile device setup.
- **Goal**: Resolve 70% of all incoming tickets on the first contact.
- **SLA**: Initial response within 1 hour; resolution within 4 hours.

### Tier 2 (Desktop Support / Systems Admin)
- **Primary Focus**: Complex issues requiring on-site or remote hands-on intervention.
- **Responsibilities**: Hardware repair, OS re-imaging, network connectivity issues, and software conflicts.
- **Escalation Trigger**: Issue not resolved by Tier 1 within 4 hours or requires specialized knowledge.
- **SLA**: Resolution within 24 hours.

### Tier 3 (Engineering / Security / Network Operations)
- **Primary Focus**: High-impact issues, system-wide outages, and security incidents.
- **Responsibilities**: Server maintenance, firewall configuration, database management, and cybersecurity forensics.
- **Escalation Trigger**: Major service disruption (P1/P2) or complex technical issues beyond Tier 2 expertise.
- **SLA**: Resolution within 4-8 hours for P1; 48 hours for non-critical issues.

## Priority Levels and Definition

### P1: Critical (Emergency)
- **Definition**: Total loss of a core business service (e.g., flight booking system down, airport-wide WiFi failure).
- **Impact**: Affects more than 100 users or halts flight operations.
- **Escalation**: Immediate verbal notification to IT Management and the NOC.

### P2: High (Urgent)
- **Definition**: Significant degradation of a service (e.g., slow response from the SkyWing Crew Portal, multiple users unable to access VPN).
- **Impact**: Affects 20-100 users or a critical department.
- **Escalation**: Notify the relevant Team Lead within 30 minutes.

### P3: Medium (Standard)
- **Definition**: Individual user issue with a workaround (e.g., single laptop failing, software error in a non-critical app).
- **Impact**: Affects 1-5 users.
- **Escalation**: Regular ticket workflow.

### P4: Low (Planned)
- **Definition**: General inquiries, feature requests, or scheduled maintenance (e.g., request for new software, hardware upgrade).
- **Impact**: No immediate business impact.
- **Escalation**: Regular ticket workflow.

## Escalation Workflow

### 1. Ticket Assignment
When a Tier 1 analyst identifies an issue beyond their scope, they must:
- Update the ticket description with all troubleshooting steps taken.
- Change the ticket status to "Escalated to Tier 2" (or Tier 3).
- Assign the ticket to the appropriate functional group (e.g., "Networking", "Security", "Assets").

### 2. Management Notification
For all P1 and P2 incidents, the IT Help Desk Manager must be notified via a "Major Incident Notification" (MIN) email. The MIN should include:
- **Incident Summary**: Brief description of the issue.
- **Current Status**: Investigating, Identifying, or Resolving.
- **Estimated Time of Resolution (ETR)**: If available.

### 3. "Warm" Handoff
For P1 incidents, a "warm handoff" is required. This means the Tier 1 analyst must directly contact the Tier 2 or Tier 3 engineer via phone or Teams to ensure they are aware of the critical ticket.

## Post-Incident Review (PIR)
For every P1 incident, a mandatory Post-Incident Review meeting will be held within 3 business days of resolution.
- **Participants**: Incident Manager, relevant Engineers, and affected Business Leads.
- **Goal**: Identify the root cause, document "lessons learned", and implement preventative measures.

## Contact Information
- **IT Help Desk Manager**: Extension 8800
- **Network Operations Center (NOC)**: Extension 4444
- **Security Operations Center (SOC)**: Extension 9111
- **Escalation Email**: `it-escalation@skywing.com`
