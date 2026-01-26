/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_STRIPE_PUBLIC_KEY: string
  readonly VITE_GOOGLE_CLIENT_ID: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_URL: string
  readonly VITE_DEBUG_MODE: string
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}