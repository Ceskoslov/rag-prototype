---
department: IT Support
last_updated: 2026-01-15
category: Connectivity
audience: All Employees
---

# VPN Setup and Troubleshooting Guide

## Overview
SkyWing Airlines utilizes the SkyConnect VPN system to provide secure, encrypted access to internal resources for remote employees and contractors. This guide covers the initial installation, configuration, and common troubleshooting steps for the SkyConnect VPN client.

## Installation Steps
1. **Download**: Navigate to the internal IT portal (it.skywing.com/vpn) and download the SkyConnect installer for your operating system (Windows 11, macOS 14+, or Linux).
2. **Execution**: Run the installer with administrative privileges. 
3. **Configuration**: When prompted for the Server Address, enter `vpn-gate.skywing.com`.
4. **Authentication**: Use your standard SkyWing SSO credentials (Email and Password).

## Multi-Factor Authentication (MFA)
Access to the VPN requires secondary verification via the SkyWing Authenticator app.
- Once you enter your credentials, a push notification will be sent to your registered mobile device.
- You have 60 seconds to approve the request before it times out.
- Failure to approve three consecutive MFA requests will result in a temporary 30-minute account lockout.

## Troubleshooting Common Issues

### Error 403: Access Denied
This typically indicates your account does not have the "Remote Access" permission group assigned in Active Directory. Contact your manager to submit a ticket for the "REMOTE-USER" group assignment.

### Connection Timeout (Error 504)
If the connection hangs at "Authenticating...", verify your local internet connection. The SkyConnect VPN requires a minimum bandwidth of 5Mbps for stable operation.

### Latency and Performance
For users connecting from international locations, the VPN will automatically route through the nearest regional concentrator:
- **North America**: vpn-na.skywing.com
- **Europe/EMEA**: vpn-eu.skywing.com
- **Asia-Pacific**: vpn-ap.skywing.com

## Policy Thresholds
- **Idle Timeout**: VPN sessions will automatically disconnect after 4 hours of inactivity.
- **Max Session Length**: For security reasons, all sessions are terminated after 12 hours and require re-authentication.
- **Concurrent Logins**: Only one active VPN session is allowed per user ID. Initiating a second session will terminate the first.

## Escalation
If you are unable to connect after following these steps, please contact the IT Help Desk at extension 5555 or email `support@skywing.com` with your machine ID and a screenshot of the error message.
