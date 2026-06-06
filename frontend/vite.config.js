import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, '');
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000';

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@assets': path.resolve(__dirname, './src/assets'),
        '@auth': path.resolve(__dirname, './src/auth'),
        '@api': path.resolve(__dirname, './src/api'),
        '@hooks': path.resolve(__dirname, './src/hooks'),
        '@router': path.resolve(__dirname, './src/router'),
        '@layouts': path.resolve(__dirname, './src/layouts'),
        '@components': path.resolve(__dirname, './src/components'),
        '@pages': path.resolve(__dirname, './src/pages'),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
        },
        '/media': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
        },
      },
      allowedHosts: [
        'localhost',
        '127.0.0.1',
        '10.10.73.5',
        'leave.oanhhong.xyz'
      ]
    }
  };
})
