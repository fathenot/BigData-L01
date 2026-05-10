import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

export const fetchProducts = () =>
  api.get('/products').then(r => r.data);

export const fetchOverview = (dateRange, productAsin, confidenceMin, confidenceMax) =>
  api.get('/overview', { params: { dateRange, productAsin, confidenceMin, confidenceMax } }).then(r => r.data);

export const fetchTrend = (dateRange, productAsin) =>
  api.get('/trend', { params: { dateRange, productAsin } }).then(r => r.data);

export const fetchReviews = (dateRange, productAsin, sentiment, page, limit = 50, confidenceMin, confidenceMax) =>
  api.get('/reviews', { params: { dateRange, productAsin, sentiment, page, limit, confidenceMin, confidenceMax } }).then(r => r.data);
