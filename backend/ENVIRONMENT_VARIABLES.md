# Environment Variables

This document provides a detailed overview of the environment variables used in the Banwee E-commerce Platform.

## Backend

The backend uses the following environment variables. You can set them in a `.env` file in the `backend` directory.

- `POSTGRES_USER`: The username for the PostgreSQL database.
- `POSTGRES_PASSWORD`: The password for the PostgreSQL database.
- `POSTGRES_SERVER`: The hostname of the PostgreSQL database.
- `POSTGRES_PORT`: The port of the PostgreSQL database.
- `POSTGRES_DB`: The name of the PostgreSQL database.
- `DATABASE_URL`: The full database connection string. If this is set, it will override the individual `POSTGRES_*` variables. For example, `DATABASE_URL=sqlite:///./test.db`.
- `DOMAIN`: The domain name of the application.
- `ENVIRONMENT`: The environment the application is running in (e.g., `local`, `production`).
- `BACKEND_CORS_ORIGINS`: A comma-separated list of allowed CORS origins.
- `SECRET_KEY`: A secret key for signing JWTs.
- `ALGORITHM`: The algorithm to use for signing JWTs.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: The expiration time for access tokens in minutes.
- `REFRESH_TOKEN_EXPIRE_DAYS`: The expiration time for refresh tokens in days.
- `STRIPE_SECRET_KEY`: Your Stripe secret key.
- `STRIPE_PUBLIC_KEY`: Your Stripe public key.
- `STRIPE_WEBHOOK_SECRET`: Your Stripe webhook secret.
- `SMTP_HOSTNAME`: The hostname of the SMTP server.
- `SMTP_PORT`: The port of the SMTP server.
- `SMTP_USER`: The username for the SMTP server.
- `SMTP_PASSWORD`: The password for the SMTP server.
- `SMTP_FROM_EMAIL`: The email address to send emails from.
- `SMTP_FROM_NAME`: The name to send emails from.
- `GOOGLE_CLIENT_ID`: Your Google client ID for social authentication.
- `GOOGLE_CLIENT_SECRET`: Your Google client secret for social authentication.
- `FACEBOOK_APP_ID`: Your Facebook app ID for social authentication.
- `FACEBOOK_APP_SECRET`: Your Facebook app secret for social authentication.
- `TIKTOK_CLIENT_KEY`: Your TikTok client key for social authentication.
- `TIKTOK_CLIENT_SECRET`: Your TikTok client secret for social authentication.
- `SMS_API_KEY`: Your SMS API key.
- `SMS_API_URL`: Your SMS API URL.
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.

## Frontend

The frontend uses the following environment variables. You can set them in a `.env.local` file in the `frontend` directory.

- `VITE_API_BASE_URL`: The base URL of the backend API.
- `VITE_STRIPE_PUBLIC_KEY`: Your Stripe public key.
- `VITE_GOOGLE_CLIENT_ID`: Your Google client ID for social authentication.
- `VITE_FACEBOOK_APP_ID`: Your Facebook app ID for social authentication.
- `VITE_TIKTOK_CLIENT_ID`: Your TikTok client ID for social authentication.
- `VITE_APP_NAME`: The name of the application.
- `VITE_APP_URL`: The URL of the application.
