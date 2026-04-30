import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

export default function TrendChart({ trend }) {
  if (!trend || trend.length === 0) {
    return (
      <div className="card">
        <div className="card-title">Xu hướng theo ngày</div>
        <div className="empty">Chưa có dữ liệu</div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-title">Xu hướng theo ngày</div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={trend} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey="positive" stackId="a" fill="#22c55e" name="Positive" />
          <Bar dataKey="neutral"  stackId="a" fill="#f59e0b" name="Neutral"  />
          <Bar dataKey="negative" stackId="a" fill="#ef4444" name="Negative" radius={[4,4,0,0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
