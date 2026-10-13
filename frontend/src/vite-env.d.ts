/// <reference types="vite/client" />

interface ViteTypeOptions {
  strictImportMetaEnv: unknown
}

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_ENABLE_DEVTOOLS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
