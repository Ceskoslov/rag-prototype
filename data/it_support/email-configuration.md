---
department: IT Support
last_updated: 2026-03-12
category: Communication
audience: All Employees
---

# Email Configuration (Outlook, Mobile Devices)

## Overview
SkyWing Airlines uses Microsoft 365 as its primary communication platform. This document provides instructions for configuring corporate email accounts on desktops, laptops, and personal mobile devices.

## Corporate Email Accounts
All SkyWing employees are provisioned with a primary email address in the format:
- `first.last@skywing.com` (Standard Employees)
- `first.last@ops.skywing.com` (Ground Crew, Flight Ops)
- `first.last@admin.skywing.com` (IT, Legal, HR)

## Configuring Outlook on Windows and macOS
SkyWing laptops come pre-installed with Microsoft Outlook as the standard email client.

### First-Time Setup
1. **Open Outlook**: Launch the application from the Start Menu or Applications folder.
2. **Account Setup**: Outlook will automatically detect your logged-in Windows or macOS credentials.
3. **Connect**: Click "Connect" to set up your primary `@skywing.com` account.
4. **MFA Approval**: If prompted, approve the login request via the SkyWing Authenticator app.
5. **Synchronization**: Outlook will begin downloading your mailbox and calendar data. This may take 15-30 minutes for large mailboxes.

## Mobile Device Configuration (iOS and Android)
SkyWing follows a "Bring Your Own Device" (BYOD) policy for mobile email, managed via Microsoft Intune (MDM).

### Required Applications
To access SkyWing email on your personal device, you must install:
- **Microsoft Outlook** (from App Store or Google Play)
- **Microsoft Authenticator** (from App Store or Google Play)
- **Intune Company Portal** (Android only)

### Setup Steps for iOS
1. **Add Account**: Open Outlook and select "Add Email Account".
2. **Email Address**: Enter your full SkyWing email address.
3. **MFA**: Authenticate through the SkyWing SSO portal and approve the request on the Authenticator app.
4. **Enrollment**: You will be prompted to "Enroll" your device in the SkyWing Intune management system. This is required for security compliance.
5. **App Protection**: A 4-digit PIN for the Outlook app must be created. This is separate from your phone's passcode.

### Setup Steps for Android
1. **Company Portal**: Open the Intune Company Portal app and sign in with your SkyWing SSO credentials.
2. **Device Enrollment**: Follow the on-screen prompts to "Register" and "Enroll" your device. This creates a "Work Profile" on your phone.
3. **Outlook Work**: Open the "Outlook" app located within the "Work" tab or folder on your home screen.
4. **Account Setup**: Your SkyWing account will be automatically added. Authenticate when prompted.

## Shared Mailboxes and Resource Calendars
- **Shared Mailboxes**: Access to shared mailboxes (e.g., `info@skywing.com`, `ops-support@skywing.com`) must be requested via the IT Service Portal.
- **Resource Calendars**: Conference rooms and shared equipment can be booked via the "Calendar" tab in Outlook by clicking "Add Calendar" > "From Room List".

## Email Security and Protection
- **External Sender Tag**: All emails originating from outside SkyWing will be marked with a `[EXTERNAL]` tag in the subject line.
- **Reporting Phishing**: Use the "Report Message" button in the Outlook toolbar to report suspicious or malicious emails.
- **Attachment Limits**: The maximum size for a single attachment is 25MB. For larger files, use SkyWing OneDrive or SharePoint.
- **Retention Policy**: Emails in the "Inbox" and "Sent Items" are retained for 7 years. Deleted items are permanently purged after 30 days.

## Support
For issues with email configuration or to request a mailbox size increase (standard limit is 50GB), contact the Messaging Team at `email-ops@skywing.com` or extension 3333.
