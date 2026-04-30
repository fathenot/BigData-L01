require('dotenv').config({ path: '../.env' });
const express = require('express');
const cors = require('cors');

const productsRouter = require('./routes/products');
const overviewRouter = require('./routes/overview');
const trendRouter   = require('./routes/trend');
const reviewsRouter = require('./routes/reviews');

const app  = express();
const PORT = process.env.BFF_PORT || 3001;

app.use(cors());
app.use(express.json());

app.use('/api/products', productsRouter);
app.use('/api/overview', overviewRouter);
app.use('/api/trend',    trendRouter);
app.use('/api/reviews',  reviewsRouter);

app.get('/health', (_req, res) => res.json({ status: 'ok' }));

app.listen(PORT, () => console.log(`BFF running at http://localhost:${PORT}`));
