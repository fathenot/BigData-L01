const express = require('express');
const pool    = require('../db');
const router  = express.Router();

const INTERVALS = { '1d': '1 day', '3d': '3 days', '7d': '7 days', '30d': '30 days' };

router.get('/', async (req, res) => {
  const interval    = INTERVALS[req.query.dateRange] || '7 days';
  const productAsin = req.query.productAsin || null;

  try {
    const { rows } = await pool.query(
      `SELECT
         DATE(ar.event_time)  AS date,
         sr.sentiment_label   AS label,
         COUNT(*)             AS count
       FROM sentimentresult sr
       JOIN amazonreview ar ON sr.review_id = ar.review_id
       WHERE ar.event_time >= NOW() - $1::interval
         AND ($2::text IS NULL OR ar.product_asin = $2)
       GROUP BY DATE(ar.event_time), sr.sentiment_label
       ORDER BY date`,
      [interval, productAsin]
    );

    // Pivot thành { date, positive, neutral, negative } cho Recharts
    const map = {};
    for (const r of rows) {
      const d = r.date.toISOString().slice(0, 10);
      if (!map[d]) map[d] = { date: d, positive: 0, neutral: 0, negative: 0 };
      map[d][r.label] = parseInt(r.count);
    }

    res.json(Object.values(map).sort((a, b) => a.date.localeCompare(b.date)));
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
