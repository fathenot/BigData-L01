import { useState } from 'react';

function Stars({ n }) {
  if (!n) return <span style={{ color: '#94a3b8' }}>—</span>;
  return <span title={`${n} sao`}>{'★'.repeat(n)}{'☆'.repeat(5 - n)}</span>;
}

const CONFIDENCE_OPTIONS = [
  { label: '70–80%',  value: '70-80'  },
  { label: '80–90%',  value: '80-90'  },
  { label: '90–100%', value: '90-100' },
];

export default function ReviewTable({ reviews, total, page, setPage, onlyNegative, setOnlyNegative, confidenceRange, setConfidenceRange }) {
  const [expanded, setExpanded] = useState(null);
  const LIMIT = 50;

  const rows = onlyNegative
    ? (reviews || []).filter(r => r.sentiment_label === 'negative')
    : (reviews || []);

  return (
    <div className="card">
      <div className="toolbar">
        <span className="toolbar-title">
          Bảng đánh giá chi tiết
          <span style={{ color: '#94a3b8', fontWeight: 400, marginLeft: 8 }}>
            ({total?.toLocaleString()} kết quả)
          </span>
        </span>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Độ tin cậy:</span>
          {CONFIDENCE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              className={`btn-outline ${confidenceRange === opt.value ? 'active' : ''}`}
              onClick={() => setConfidenceRange(confidenceRange === opt.value ? null : opt.value)}
            >
              {opt.label}
            </button>
          ))}
          <button
            className={`btn-outline ${onlyNegative ? 'active' : ''}`}
            onClick={() => setOnlyNegative(!onlyNegative)}
          >
            {onlyNegative ? '✕ Bỏ lọc tiêu cực' : '⚠ Chỉ xem Tiêu cực'}
          </button>
        </div>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Thời gian</th>
              <th>ASIN</th>
              <th>Sao</th>
              <th>Nhãn</th>
              <th>Độ tin cậy</th>
              <th>Nội dung</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr><td colSpan={6} className="empty">Không có dữ liệu</td></tr>
            )}
            {rows.map((r, i) => {
              const key = `${r.event_time}-${i}`;
              const isOpen = expanded === key;
              return (
                <tr key={key} onClick={() => setExpanded(isOpen ? null : key)} style={{ cursor: 'pointer' }}>
                  <td style={{ whiteSpace: 'nowrap', fontSize: '0.78rem', color: '#64748b' }}>
                    {new Date(r.event_time).toLocaleString('vi-VN')}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '0.78rem' }}>{r.product_asin}</td>
                  <td style={{ color: '#f59e0b' }}><Stars n={r.star_rating} /></td>
                  <td><span className={`badge ${r.sentiment_label}`}>{r.sentiment_label}</span></td>
                  <td>{(r.confidence_score * 100).toFixed(1)}%</td>
                  <td>
                    {isOpen
                      ? <span>{r.original_text}</span>
                      : <span className="text-truncate" style={{ display: 'block' }}>{r.original_text}</span>
                    }
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {!onlyNegative && (
        <div className="pagination">
          <button onClick={() => setPage(p => p - 1)} disabled={page <= 1}>← Trước</button>
          <span>Trang {page} / {Math.ceil((total || 0) / LIMIT)}</span>
          <button onClick={() => setPage(p => p + 1)} disabled={page >= Math.ceil((total || 0) / LIMIT)}>Sau →</button>
        </div>
      )}
    </div>
  );
}
