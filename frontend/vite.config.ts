import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// Read version from local VERSION file first, fallback to root VERSION
let majorVersion = '0.0.0'
for (const candidate of ['./VERSION', '../VERSION']) {
  try {
    majorVersion = fs.readFileSync(path.resolve(__dirname, candidate), 'utf-8').trim()
    break
  } catch {
    // try next candidate
  }
}
const now = new Date()
const buildTimestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}.${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`
const version = `${majorVersion}+${buildTimestamp}`
const defaultAppName = 'Clawith'
const defaultAppDescription = 'Clawith — 企业数字员工平台'

// These branding values are resolved when Vite builds index.html.
// Set VITE_APP_NAME / VITE_APP_DESCRIPTION before `npm run build` or Docker image build time.
// Updating runtime container env later will not rewrite the already-built frontend assets.

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, __dirname, '')
    const appName = env.VITE_APP_NAME || defaultAppName
    const appDescription = env.VITE_APP_DESCRIPTION || defaultAppDescription

    return {
        plugins: [
            react(),
            {
                name: 'brand-html-defaults',
                transformIndexHtml(html) {
                    return html
                        .replaceAll('__APP_NAME__', appName)
                        .replaceAll('__APP_DESCRIPTION__', appDescription)
                },
            },
        ],
        define: {
            __APP_VERSION__: JSON.stringify(version),
        },
        resolve: {
            alias: {
                '@': path.resolve(__dirname, './src'),
            },
        },
        server: {
            port: 3008,
            host: '0.0.0.0',
            proxy: {
                '/api': {
                    target: 'http://localhost:8008',
                    changeOrigin: true,
                },
                '/ws': {
                    target: 'ws://localhost:8008',
                    ws: true,
                },
            },
        },
    }
})
