import { useMemo, useState } from 'react';
import type { BatteryReportData } from '../core/types';
import { groupDataByPeriod, getISOWeekString } from '../core/utils';
import { pearsonCorrelation } from '../core/analyzer';
import { Bar } from 'react-chartjs-2';

export default function UsageTab({ data }: { data: BatteryReportData }) {
  const [period, setPeriod] = useState<'week' | 'month' | 'year'>('week');

  const usageStats = useMemo(() => {
    if (data.usage_data.length === 0) return null;

    // Use utils to reliably group usage and SUM the hours
    const grouped = groupDataByPeriod(data.usage_data, d => d.date, d => d.hours_used, period);
    
    // Convert to chart.js format
    const chartData = {
      labels: grouped.map(g => g.label),
      datasets: [{
        label: `Active Battery Usage (Hours)`,
        data: grouped.map(g => g.value),
        backgroundColor: 'rgba(139, 92, 246, 0.6)',
        borderRadius: 4
      }]
    };

    // Find most/least
    const sorted = [...grouped].sort((a, b) => b.value - a.value);

    return {
      chartData,
      mostUsed: sorted[0],
      leastUsed: sorted[sorted.length - 1],
      total: grouped.reduce((sum, item) => sum + item.value, 0)
    };
  }, [data, period]);

  const correlationInfo = useMemo(() => {
      // Find correlation between weekly usage sums and weekly degradation sums
      if (data.health_data.length < 2 || data.usage_data.length === 0) return null;

      const groupedUsage = groupDataByPeriod(data.usage_data, d => d.date, d => d.hours_used, 'week');
      
      const manualGroupMap = new Map<string, number[]>();
      data.health_data.forEach(item => {
          let key = getISOWeekString(item.date);
          if (!manualGroupMap.has(key)) manualGroupMap.set(key, []);
          manualGroupMap.get(key)!.push(item.health);
      });
      const sortedHealth = Array.from(manualGroupMap.entries()).map(([label, vals]) => {
          return { label, avgHealth: vals.reduce((a, b) => a + b, 0) / vals.length };
      }).sort((a, b) => a.label.localeCompare(b.label));

      // Build arrays where labels match
      const usageMap = new Map<string, number>(groupedUsage.map(g => [g.label, g.value]));
      const x = [];
      const y = [];

      for (let i = 1; i < sortedHealth.length; i++) {
        const drop = sortedHealth[i-1].avgHealth - sortedHealth[i].avgHealth;
        const weekLabel = sortedHealth[i].label;

        // If we have usage data for this precise mapped ISO week
        if (usageMap.has(weekLabel)) {
            y.push(drop); // Target var: degradation
            x.push(usageMap.get(weekLabel)!); // Predictor var: usage hours
        }
      }

      if (x.length < 3) return null;

      const cc = pearsonCorrelation(x, y);

      return {
          coefficient: cc,
          samples: x.length
      };

  }, [data]);

  if (!usageStats) {
      return <div className="glass-panel" style={{ padding: '2rem' }}>No usage history found in report. Windows may have purged it.</div>;
  }

  return (
    <div>
        <div className="dashboard-grid">
            <div className="glass-panel stat-card">
              <div className="stat-label">Total Time On Battery</div>
              <div className="stat-value" style={{ color: 'var(--accent-secondary)' }}>
                {usageStats.total.toFixed(0)} <span style={{fontSize: '1rem', color: 'var(--text-secondary)'}}>Hours</span>
              </div>
            </div>
            <div className="glass-panel stat-card">
              <div className="stat-label">Peak Usage ({period})</div>
              <div className="stat-value" style={{ color: 'var(--text-primary)' }}>
                {usageStats.mostUsed.value.toFixed(1)}h <span style={{fontSize: '1rem', color: 'var(--text-secondary)'}}>in {usageStats.mostUsed.label}</span>
              </div>
            </div>
            {correlationInfo && (
              <div className="glass-panel stat-card">
                <div className="stat-label">Usage / Degradation Correlation</div>
                <div className="stat-value" style={{ color: correlationInfo.coefficient > 0.5 ? 'var(--danger)' : 'var(--text-primary)' }}>
                    {correlationInfo.coefficient.toFixed(2)}
                </div>
                {correlationInfo.coefficient > 0.5 ? 
                    <p style={{fontSize: '0.85rem', color: 'var(--danger)', margin: 0}}>Strong indication that heavy usage causes your degradation.</p> :
                    <p style={{fontSize: '0.85rem', color: 'var(--success)', margin: 0}}>Time spent on battery does not seem to directly degrade capacity.</p>
                }
              </div>
            )}
        </div>

        <div className="glass-panel chart-container" style={{ height: '500px' }}>
          <div className="chart-header">
             <h3 style={{ margin: 0 }}>Battery Usage Patterns</h3>
             <select value={period} onChange={e => setPeriod(e.target.value as any)}>
                 <option value="week">By Week (ISO Standard)</option>
                 <option value="month">By Month</option>
                 <option value="year">By Year</option>
             </select>
          </div>
          <Bar 
              data={usageStats.chartData} 
              options={{ 
                  responsive: true, 
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } }
              }} 
            />
        </div>

    </div>
  );
}
