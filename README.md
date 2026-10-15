# Smart-plug-Android-App
Android application for monitoring electricity prices and controlling a smart plug accordingly as part of a smart home system
# Smart Plug — Smart Home Energy Management System

## Overview

Smart Plug is an A-level OCR Computer Science NEA project exploring how electricity-pricing information, smart-plug control and automation can be combined to help users manage household energy use and costs.

The project consists of three connected components:

1. **Android Application** — provides a mobile interface for users to view electricity-pricing information, manage settings and interact with the wider system.
2. **Python Smart Home System** — supports device integrations, energy-usage retrieval, scheduled tasks, data synchronisation and data processing.
3. **Node.js Backend API** — provides server-side functionality for user accounts, password changes, settings, notification tokens, electricity-price data and device schedules.

The wider project also includes the retrieval and analysis of electricity-pricing information from Octopus Energy and integration with compatible smart devices.

## System Architecture

The system is divided into three main components:

| Component | Main responsibility | Technologies |
|---|---|---|
| Android application | Mobile interface, pricing views, account features and settings | Java, Android SDK, Gradle |
| Python smart home system | Automation, scheduling, usage retrieval, device integration and data processing | Python |
| Backend API | Account-related requests, pricing data and schedule endpoints | Node.js, Express, MySQL |

These components were developed as parts of the same project. The portfolio versions have had sensitive configuration replaced with placeholders, so the complete system is not expected to work without additional setup.

## 1. Android Application

The Android application provides the user-facing mobile interface.

Features documented in the project include:

- User registration and login screens.
- Home and electricity-pricing views.
- Pricing details and data-analysis screens.
- Settings and password-change functionality.
- Notification and threshold-related settings.
- Dashboard and device-scheduling interfaces.
- API-client code for communication with the backend.

**Technologies:** Java, Android SDK, Gradle, Android layouts and resources.

The project can be opened in Android Studio. Gradle dependencies and API configuration may need to be reviewed before running it.

## 2. Python Smart Home System

The Python component supports the background tasks and integrations used by the wider smart home system.

The project contains the following modules:

- `updater/` — updater tasks.
- `tapo/` — integration with compatible Tapo smart devices.
- `getUsages/` — energy-usage retrieval.
- `yeelight/` — Yeelight device-control integration.
- `scheduler/` — scheduled tasks and automation.
- `dataSync/` — data synchronisation and notification-related tasks.
- `dataMart/` — data processing and database access.

The wider project also covers electricity-pricing data retrieval, analysis of pricing periods and scheduling or control behaviour.

**Technology:** Python, alongside the libraries and services required by individual modules.

Running the system may require additional dependencies, compatible hardware, device credentials and a configured database or backend.

## 3. Node.js Backend API

The Node.js backend provides server-side endpoints used by the wider application.

### API endpoints

The source includes the following routes:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Root endpoint |
| `POST` | `/register` | User registration |
| `POST` | `/login` | User login |
| `POST` | `/change_password` | Password changes |
| `POST` | `/server_setting` | Server or device-related settings |
| `POST` | `/token` | Notification-token updates |
| `GET` | `/price_data` | Electricity-price data retrieval |
| `GET` | `/devices_schedule/:userid/:temp` | Device-schedule retrieval |

The exact behaviour of each endpoint depends on the source implementation and its database configuration.

**Technologies:**
- Node.js
- Express
- MySQL
- JSON Web Tokens (`jsonwebtoken`)
- `body-parser`
- Node.js `crypto`

### Configuration

The backend reads sensitive configuration from environment variables:

- `DB_HOST`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `JWT_SECRET`

These values must be configured in the local environment before the server can start successfully. The source does not automatically load a `.env` file unless a suitable loader is added.

The API also depends on a compatible database schema, including tables or views such as `userProfiles`, `userDevices`, `schedules` and `_v_rates_for_today_threshold`.

## Setup and Limitations

The cleaned project copies do not include the original online database credentials or live backend configuration. Some functionality will therefore require additional configuration before it can be demonstrated.

Before running the projects:

1. Review the dependencies and setup requirements for each component.
2. Configure your own authorised database and backend environment.
3. Set required secrets using environment variables or an untracked local configuration file.
4. Review the API endpoint and device settings.
5. Test each component separately before attempting to connect the complete system.

The projects have not been independently built, run or tested as part of preparing these portfolio copies. Live functionality should not be assumed.

## Security Considerations

Before public release or deployment:

- Never commit database passwords, API keys, JWT secrets or access tokens.
- Keep personal information, private logs, database dumps and device credentials out of the repository.
- Use HTTPS for communication with a deployed API.
- Implement appropriate authentication and authorisation checks for private endpoints.
- Validate request data and handle errors consistently.
- Use a suitable modern password-hashing algorithm for production authentication.
- Consider rate limiting and appropriate CORS configuration.
- Rotate any real credentials that may have been exposed previously.

The full NEA assessment report contains candidate-identifying information and should not be included in the public repository.

## Project Context

This project was developed as part of an **A-level OCR Computer Science NEA**. It explores the integration of a mobile application, backend services, electricity-pricing data and smart-home automation.

The three components demonstrate different areas of software development, including mobile application development, Python automation, API design, database integration and connected-device functionality.

## Current Status

**Portfolio project — configuration and testing required.**

The source code and documentation are being prepared for public review on GitHub. The original live services and credentials are not included, and further configuration, testing and security improvements are required before deployment.

## Author
Tsz Hei WONG (Karson)
A-level OCR Computer Science project.
