const { Pool } = require('pg');

const pool = new Pool({
  host:     process.env.DB_HOST     || 'localhost',
  port:     parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME     || 'sentiment_db',
  user:     process.env.DB_USER     || 'admin',
  password: process.env.DB_PASSWORD || 'abc',
});

module.exports = pool;
