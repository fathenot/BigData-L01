import { useState, useEffect, useCallback } from 'react';
import { fetchProducts, fetchOverview, fetchTrend, fetchReviews } from './api/index.js';
import FilterBar        from './components/FilterBar.jsx';
import OverviewCards    from './components/OverviewCards.jsx';
import SentimentPieChart from './components/SentimentPieChart.jsx';
import TrendChart       from './components/TrendChart.jsx';
import ReviewTable      from './components/ReviewTable.jsx';

const REFRESH_INTERVAL = 10_000; // 10s realtime refresh

export default function App() {
  const [dateRange,    setDateRange]    = useState('7d');
  const [productAsin,  setProductAsin]  = useState('');
  const [products,     setProducts]     = useState([]);
  const [overview,     setOverview]     = useState(null);
  const [trend,        setTrend]        = useState([]);
  const [reviews,      setReviews]      = useState([]);
  const [reviewTotal,  setReviewTotal]  = useState(0);
  const [page,         setPage]         = useState(1);
  const [onlyNegative, setOnlyNegative] = useState(false);

  // Load products once
  useEffect(() => {
    fetchProducts().then(setProducts).catch(console.error);
  }, []);

  // Reload overview + trend when filters change
  useEffect(() => {
    fetchOverview(dateRange, productAsin || undefined).then(setOverview).catch(console.error);
    fetchTrend(dateRange, productAsin || undefined).then(setTrend).catch(console.error);
    setPage(1);
  }, [dateRange, productAsin]);

  // Reload reviews when filters or page change
  const loadReviews = useCallback(() => {
    fetchReviews(dateRange, productAsin || undefined, undefined, page)
      .then(r => { setReviews(r.data); setReviewTotal(r.total); })
      .catch(console.error);
  }, [dateRange, productAsin, page]);

  useEffect(() => { loadReviews(); }, [loadReviews]);

  // Auto-refresh reviews every 10s
  useEffect(() => {
    const id = setInterval(loadReviews, REFRESH_INTERVAL);
    return () => clearInterval(id);
  }, [loadReviews]);

  return (
    <div className="dashboard">
      <div className="header">
        <h1>Sentiment Analysis Dashboard</h1>
        <p>Phân tích cảm xúc đánh giá Amazon theo thời gian thực</p>
      </div>

      <div className="section">
        <FilterBar
          dateRange={dateRange}     setDateRange={setDateRange}
          productAsin={productAsin} setProductAsin={setProductAsin}
          products={products}
        />
      </div>

      <div className="section">
        <OverviewCards overview={overview} />
      </div>

      <div className="section grid-2">
        <SentimentPieChart overview={overview} />
        <TrendChart trend={trend} />
      </div>

      <div className="section">
        <ReviewTable
          reviews={reviews}
          total={reviewTotal}
          page={page}
          setPage={setPage}
          onlyNegative={onlyNegative}
          setOnlyNegative={setOnlyNegative}
        />
      </div>
    </div>
  );
}
