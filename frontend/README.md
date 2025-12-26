# Banwee - Vite Template

## Getting Started

1. Run `npm install`
2. Copy `.env.example` to `.env` and configure your environment variables
3. Run `npm run dev`

## Environment Variables

### Required Configuration

Copy `.env.example` to `.env` and fill in the following values:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/v1
VITE_WS_BASE_URL=ws://localhost:8000
VITE_STRIPE_PUBLIC_KEY=your_stripe_public_key

# Social Auth Configuration
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_FACEBOOK_APP_ID=your_facebook_app_id
VITE_TIKTOK_CLIENT_ID=your_tiktok_client_id
```

### Social Authentication Setup

#### Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized JavaScript origins: `http://localhost:5173` (development) and your production URL
6. Copy the Client ID to `VITE_GOOGLE_CLIENT_ID`

#### Facebook Login
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app or select an existing one
3. Add Facebook Login product
4. Configure OAuth redirect URIs
5. Copy the App ID to `VITE_FACEBOOK_APP_ID`
6. **Note:** Facebook Login requires HTTPS in production

#### TikTok Login
1. Go to [TikTok Developers](https://developers.tiktok.com/)
2. Create a new app
3. Enable Login Kit
4. Configure redirect URIs
5. Copy the Client Key to `VITE_TIKTOK_CLIENT_ID`

### Development Notes

- Social authentication buttons will show configuration warnings if credentials are missing
- Facebook Login will not work over HTTP (requires HTTPS)
- For local development with HTTPS, consider using tools like [mkcert](https://github.com/FiloSottile/mkcert)
