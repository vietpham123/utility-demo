const winston = require('winston');
module.exports = winston.createLogger({
  level: process.env.LOG_LEVEL || 'debug',
  format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
  defaultMeta: { service: 'grid-topology-service' },
  transports: [new winston.transports.Console()]
});
