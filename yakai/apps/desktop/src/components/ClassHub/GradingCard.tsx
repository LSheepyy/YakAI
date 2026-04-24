import type { GradingWeight } from '../../types'

interface Props {
  weights: GradingWeight[]
}

export function GradingCard({ weights }: Props) {
  const total = weights.reduce((sum, w) => sum + w.weight_pct, 0)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-3">Grading</h3>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-300">
        {weights.map((w) => (
          <span key={w.id}>
            {w.component}{' '}
            <span className="text-indigo-400 font-medium">{w.weight_pct}%</span>
          </span>
        ))}
      </div>
      {/* Mini bar visualization */}
      <div className="flex gap-0.5 mt-3 h-2 rounded-full overflow-hidden">
        {weights.map((w, i) => {
          const colors = [
            'bg-indigo-500', 'bg-violet-500', 'bg-blue-500',
            'bg-cyan-500', 'bg-teal-500', 'bg-emerald-500',
          ]
          return (
            <div
              key={w.id}
              className={`${colors[i % colors.length]} transition-all`}
              style={{ width: `${(w.weight_pct / Math.max(total, 100)) * 100}%` }}
              title={`${w.component}: ${w.weight_pct}%`}
            />
          )
        })}
      </div>
    </div>
  )
}
