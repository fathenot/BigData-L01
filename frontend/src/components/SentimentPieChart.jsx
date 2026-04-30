import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = { positive: '#22c55e', neutral: '#f59e0b', negative: '#ef4444' };

export default function SentimentPieChart({ overview }) {
  if (!overview) return null;

  const data = [
    { name: 'Positive', value: overview.positive_count },
    { name: 'Neutral',  value: overview.neutral_count  },
    { name: 'Negative', value: overview.negative_count },
  ].filter(d => d.value > 0);

  return (
    <div className="card">
      <div className="card-title">Phân bổ Sentiment</div>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={3}
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {data.map(entry => (
              <Cell key={entry.name} fill={COLORS[entry.name.toLowerCase()]} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => v.toLocaleString()} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
