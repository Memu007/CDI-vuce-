/**
 * PM2 Configuration - CDI Sistema MARÍA
 *
 * Configuración para PM2 process manager (alternativa a Gunicorn)
 *
 * Instalación:
 *   npm install -g pm2
 *
 * Uso:
 *   pm2 start ecosystem.config.js
 *   pm2 status
 *   pm2 logs cdi-maria
 *   pm2 stop cdi-maria
 *   pm2 restart cdi-maria
 */

module.exports = {
  apps: [
    {
      name: 'cdi-maria',
      script: 'gunicorn',
      args: 'proyecto_maria.server_funcional:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000',
      instances: 1,  // 1 instancia de gunicorn (que maneja 4 workers internos)
      exec_mode: 'fork',
      autorestart: true,
      watch: false,  // No watch en producción (muy intensivo)
      max_memory_restart: '1G',  // Restart si usa más de 1GB
      env: {
        NODE_ENV: 'production',
        PORT: 8000
      },
      error_file: './logs/pm2-error.log',
      out_file: './logs/pm2-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // Configuración avanzada
      kill_timeout: 5000,  // Tiempo para graceful shutdown
      listen_timeout: 10000,  // Tiempo para esperar que arranque

      // Scheduling (opcional)
      cron_restart: '0 3 * * *'  // Restart diario a las 3 AM (opcional)
    }
  ]
};
