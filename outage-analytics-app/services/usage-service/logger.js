const { createLogger, format, transports } = require('winston');

const logger = createLogger({
  level: process.env.LOG_LEVEL || 'debug',
  format: format.combine(
    format.timestamp(),
    format.json()
  ),
  defaultMeta: { service: 'usage-service' },
  transports: [
    new transports.Console()
  ]
});

module.exports = logger;
