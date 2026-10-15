# Smart Plug Backend API (Node.js)

## Overview
This Node.js/Express API is part of an A-level OCR Computer Science NEA project, **Smart Plug**. The wider system combines electricity-pricing information, an Android application, and smart-plug automation/control.

## Features documented in the source
- User registration and login
- Password changes
- Server/device-related settings and notification preferences
- Mobile notification-token updates
- Electricity-price retrieval
- Device schedule retrieval

Routes present include `GET /`, `POST /register`, `POST /login`, `POST /change_password`, `POST /server_setting`, `POST /token`, `GET /price_data`, and `GET /devices_schedule/:userid/:temp`.

## Technologies
- Node.js and Express
- MySQL
- JSON Web Tokens (`jsonwebtoken`)
- `body-parser`
- Node.js `crypto`

## Configuration
Sensitive configuration is read from environment variables:
- `DB_HOST`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `JWT_SECRET`

Set these in your local environment before starting the server. This source reads environment variables directly; it does not load a `.env` file automatically. If you use a `.env` file with a dotenv loader, keep it untracked and never commit it.

The original host and database credentials are not included in this portfolio version. The application depends on database tables/views such as `userProfiles`, `userDevices`, `schedules`, and `_v_rates_for_today_threshold`, so routes need a compatible database schema and data to function.

## Security considerations
This is an educational project snapshot, not production-ready. Before deploying it:
- Use HTTPS; do not send credentials over plain HTTP.
- Add authentication and authorisation checks to all private routes, including checks that a user may only access their own records.
- Validate request data and handle errors consistently.
- Consider a modern password-hashing algorithm such as Argon2id, scrypt, or bcrypt for a production system.
- Keep database credentials, JWT secrets, smart-device credentials, and notification tokens out of source control.
- Add rate limiting and appropriate CORS configuration.
- Rotate any real credentials that may previously have been exposed.

Parameterised SQL is used in the queries visible in this file, which helps reduce SQL-injection risk for those values but does not make the API secure by itself.

## Relationship to the wider Smart Plug project
The NEA report describes three main components: electricity-pricing retrieval and analysis, an Android application, and smart-plug API integration/control. This Node.js API supports some account, pricing, and schedule functions used by the mobile app. The separate Python repository contains additional automation and data-processing components.

## Privacy
The full NEA report contains candidate-identifying information. Use this summary for a public portfolio instead of publishing the full assessment report.

## Status
Prepared for portfolio review. The API has not been run, compiled, penetration-tested, or verified against a live database during this preparation.
