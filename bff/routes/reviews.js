const express = require('express');
const pool    = require('../db');
const router  = express.Router();

const INTERVALS = { '1d': '1 day', '3d': '3 days', '7d': '7 days', '30d': '30 days' };

router.get('/', async (req, res) => {
  const interval    = INTERVALS[req.query.dateRange] || '7 days';
  const productAsin = req.query.productAsin || null;
  const sentiment   = req.query.sentiment   || null;
  const limit       = parseInt(req.query.limit) || 50;
  const page        = parseInt(req.query.page)  || 1;
  const offset      = (page - 1) * limit;

  try {
    const [dataResult, countResult] = await Promise.all([
      pool.query(
        `SELECT
           ar.event_time, ar.product_asin, ar.star_rating,
           sr.sentiment_label, sr.confidence_score, ar.original_text
         FROM sentimentresult sr
         JOIN amazonreview ar ON sr.review_id = ar.review_id
         WHERE ar.event_time >= NOW() - $1::interval
           AND ($2::text IS NULL OR ar.product_asin = $2)
           AND ($3::text IS NULL OR sr.sentiment_label = $3)
         ORDER BY ar.event_time DESC
         LIMIT $4 OFFSET $5`,
        [interval, productAsin, sentiment, limit, offset]
      ),
      pool.query(
        `SELECT COUNT(*) AS total
         FROM sentimentresult sr
         JOIN amazonreview ar ON sr.review_id = ar.review_id
         WHERE ar.event_time >= NOW() - $1::interval
           AND ($2::text IS NULL OR ar.product_asin = $2)
           AND ($3::text IS NULL OR sr.sentiment_label = $3)`,
        [interval, productAsin, sentiment]
      ),
    ]);

    res.json({
      data:       dataResult.rows,
      total:      parseInt(countResult.rows[0].total),
      page,
      limit,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
