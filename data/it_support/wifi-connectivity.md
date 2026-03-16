---
department: IT Support
last_updated: 2026-03-10
category: Connectivity
audience: All Employees
---

# WiFi Connectivity Guide (Office + Airport Lounges)

## Overview
SkyWing Airlines provides high-speed wireless internet access for all employees across corporate offices, airport lounges, and designated gate areas. This guide outlines the available WiFi networks and instructions for connecting to each.

## Corporate Office WiFi
SkyWing offices are equipped with a unified wireless network infrastructure. Two main networks are available:

### SkyWing-Staff (Primary)
- **SSID**: SkyWing-Staff
- **Authentication**: WPA3-Enterprise (802.1X)
- **Credentials**: Corporate SSO Username and Password
- **Access**: Full access to internal resources, including intranet, HR portals, and file shares.
- **Performance**: High-speed, prioritized for business applications (Teams, Outlook, Zoom).

### SkyWing-Guest (Secondary)
- **SSID**: SkyWing-Guest
- **Authentication**: Open with Captive Portal
- **Credentials**: Email address and Sponsor Name (SkyWing employee)
- **Access**: Internet only. No access to internal SkyWing resources.
- **Usage**: Intended for vendors, visitors, and personal mobile devices.

## Airport Lounge WiFi
SkyWing airport lounges provide a premium connectivity experience for both passengers and employees.

### SkyLounge-Premium
- **SSID**: SkyLounge-Premium
- **Authentication**: WPA2-Personal (Pre-shared Key)
- **Credentials**: The daily password is provided on the SkyWing internal portal (it.skywing.com/lounge-wifi).
- **Access**: Priority internet access and VPN connectivity.
- **Availability**: SkyWing hub airports (JFK, LHR, FRA, DXB, SIN).

## Gate Area and Operational WiFi
For ground staff and flight crews, dedicated operational networks are available at the gate and on the tarmac.

### SkyWing-Ops
- **SSID**: SkyWing-Ops
- **Authentication**: Certificate-based (Managed devices only)
- **Credentials**: Pre-installed digital certificate (provisioned by IT).
- **Access**: Optimized for flight operations tools, baggage tracking, and passenger manifest systems.
- **Coverage**: Gate podiums, baggage loading areas, and maintenance hangars.

## Technical Configuration and Troubleshooting

### Certificate Verification
When connecting to "SkyWing-Staff" for the first time, you may be prompted to trust a certificate from "skywing-ca.internal". Click "Trust" or "Continue" to establish the secure connection.

### Signal Strength and Interference
- **Minimum Signal**: For reliable performance, ensure your device shows at least 3 bars of signal.
- **Interference**: Common sources of interference include microwave ovens, Bluetooth devices, and high-density metal structures. 
- **Frequency**: SkyWing WiFi operates on both 2.4GHz and 5GHz bands. Modern devices will automatically select the 5GHz band for better performance.

### Connectivity Troubleshooting Steps
1. **Forget Network**: If you've recently changed your SSO password, "Forget" the "SkyWing-Staff" network and reconnect with the new credentials.
2. **Toggle WiFi**: Turn your device's WiFi off and back on to refresh the connection.
3. **Check VPN**: If using the SkyConnect VPN, ensure it is disconnected before attempting to join the local WiFi network.
4. **Proxy Settings**: SkyWing WiFi does not require a manual proxy. Ensure "Automatic Proxy Discovery" is enabled in your system settings.

## Security Policies
- **No Rogue Access Points**: Personal routers, hotspots, or unauthorized wireless extenders are strictly prohibited in SkyWing facilities.
- **Monitoring**: All wireless traffic is monitored for security threats and policy compliance in accordance with the SkyWing Acceptable Use Policy.

## Assistance
For WiFi-related issues, please contact the Network Operations Center at `noc@skywing.com` or extension 4444.
