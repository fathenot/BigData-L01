const DATE_RANGES = [
  { label: 'Hôm nay', value: '1d' },
  { label: '3 ngày',  value: '3d' },
  { label: '1 tuần',  value: '7d' },
  { label: '1 tháng', value: '30d' },
];

export default function FilterBar({ dateRange, setDateRange, productAsin, setProductAsin, products }) {
  return (
    <div className="card filter-bar">
      <div className="btn-group">
        {DATE_RANGES.map(d => (
          <button
            key={d.value}
            className={`btn ${dateRange === d.value ? 'active' : ''}`}
            onClick={() => setDateRange(d.value)}
          >
            {d.label}
          </button>
        ))}
      </div>

      <select
        className="select"
        value={productAsin}
        onChange={e => setProductAsin(e.target.value)}
      >
        <option value="">Tất cả sản phẩm</option>
        {products.map(p => (
          <option key={p.product_asin} value={p.product_asin}>
            {p.product_asin}{p.product_name ? ` — ${p.product_name}` : ''}
          </option>
        ))}
      </select>
    </div>
  );
}
