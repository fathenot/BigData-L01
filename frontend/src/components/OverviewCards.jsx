export default function OverviewCards({ overview }) {
  if (!overview) return null;
  const { total_reviews, avg_confidence, positive_pct, neutral_pct, negative_pct } = overview;

  return (
    <div className="grid-4">
      <div className="card">
        <div className="card-title">Total Reviews</div>
        <div className="card-value">{total_reviews.toLocaleString()}</div>
        <div className="card-sub">mẫu đã phân tích</div>
      </div>

      <div className="card">
        <div className="card-title">Avg Confidence</div>
        <div className="card-value">{(avg_confidence * 100).toFixed(1)}%</div>
        <div className="card-sub">độ tin cậy trung bình</div>
      </div>

      <div className="card">
        <div className="card-title">Positive</div>
        <div className="card-value stat-positive">{positive_pct}%</div>
        <div className="card-sub">{overview.positive_count.toLocaleString()} reviews</div>
      </div>

      <div className="card">
        <div className="card-title">Negative</div>
        <div className="card-value stat-negative">{negative_pct}%</div>
        <div className="card-sub">{overview.negative_count.toLocaleString()} reviews</div>
      </div>
    </div>
  );
}
