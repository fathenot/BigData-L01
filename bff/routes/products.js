const express = require('express');
const pool    = require('../db');
const router  = express.Router();

router.get('/', async (_req, res) => {
  try {
    const { rows } = await pool.query(
      `SELECT product_asin, product_name FROM product ORDER BY product_asin`
    );
    res.json(rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
