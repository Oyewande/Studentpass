/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Railway backend URL — set on Vercel, omitted in local dev */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
