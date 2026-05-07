const express = require('express');
const pool    = require('../db');
const router  = express.Router();

const INTERVALS = { '1d': '1 day', '3d': '3 days', '7d': '7 days', '30d': '30 days' };

router.get('/', async (req, res) => {
  const interval      = INTERVALS[req.query.dateRange] || '7 days';
  const productAsin   = req.query.productAsin  || null;
  const confidenceMin = req.query.confidenceMin != null && req.query.confidenceMin !== '' ? parseFloat(req.query.confidenceMin) : null;
  const confidenceMax = req.query.confidenceMax != null && req.query.confidenceMax !== '' ? parseFloat(req.query.confidenceMax) : null;

  try {
    const { rows } = await pool.query(
      `SELECT
         COUNT(*)                                                   AS total_reviews,
         ROUND(AVG(sr.confidence_score)::numeric, 4)               AS avg_confidence,
         COUNT(*) FILTER (WHERE sr.sentiment_label = 'positive')   AS positive_count,
         COUNT(*) FILTER (WHERE sr.sentiment_label = 'neutral')    AS neutral_count,
         COUNT(*) FILTER (WHERE sr.sentiment_label = 'negative')   AS negative_count
       FROM sentimentresult sr
       JOIN amazonreview ar ON sr.review_id = ar.review_id
       WHERE ar.event_time >= NOW() - $1::interval
         AND ($2::text    IS NULL OR ar.product_asin      =  $2)
         AND ($3::numeric IS NULL OR sr.confidence_score >= $3)
         AND ($4::numeric IS NULL OR sr.confidence_score <= $4)`,
      [interval, productAsin, confidenceMin, confidenceMax]
    );
    const row   = rows[0];
    const total = parseInt(row.total_reviews) || 0;

    res.json({
      total_reviews:    total,
      avg_confidence:   parseFloat(row.avg_confidence) || 0,
      positive_count:   parseInt(row.positive_count)   || 0,
      neutral_count:    parseInt(row.neutral_count)    || 0,
      negative_count:   parseInt(row.negative_count)   || 0,
      positive_pct:     total ? +((row.positive_count / total) * 100).toFixed(1) : 0,
      neutral_pct:      total ? +((row.neutral_count  / total) * 100).toFixed(1) : 0,
      negative_pct:     total ? +((row.negative_count / total) * 100).toFixed(1) : 0,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
