import { useMemo, useState } from 'react';
import type { BatteryReportData } from '../core/types';
import { groupDataByPeriod, getISOWeekString, getMonthString, getYearString } from '../core/utils';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, Title, Tooltip, Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

export default function DegradationTab({ data }: { data: BatteryReportData }) {
  const [period, setPeriod] = useState<'week' | 'month' | 'year'>('month');

  const chartData = useMemo(() => {
    // We want to graph Health% over time (Line)
    // But also we want to see degradation *rate* (Bar) - the drop between periods
    if (data.health_data.length === 0) return null;

    const labels = data.health_data.map(d => d.date.toLocaleDateString());
    const healthVals = data.health_data.map(d => d.health);

    const minHealth = Math.min(...healthVals);

    return {
      lineChart: {
        labels,
        datasets: [
          {
            label: 'Battery Health (%)',
            data: healthVals,
            borderColor: 'rgba(59, 130, 246, 1)',
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            borderWidth: 2,
            tension: 0.2, // smoothing
            pointRadius: 2,
          }
        ]
      },
      minHealth
    };
  }, [data]);

  const degStats = useMemo(() => {
    // Calculate degradation drops per period
    // Since health data doesn't "accumulate" like usage hours, we have to find the max - min health per period
    // For simplicity, let's group all health readings by period and take the average, 
    // then calculate the delta between periods.
    if (data.health_data.length < 2) return null;

    // Removed unused map result
    groupDataByPeriod(
      data.health_data,
      (d) => d.date,
      (d) => d.health,
      period
    );

    // Let's do a manual pass for average
      const groupMap = new Map<string, number[]>();
      data.health_data.forEach(item => {
        let key = '';
        if (period === 'week') key = getISOWeekString(item.date);
        else if (period === 'month') key = getMonthString(item.date);
        else if (period === 'year') key = getYearString(item.date);
        
        if (!groupMap.has(key)) groupMap.set(key, []);
        groupMap.get(key)!.push(item.health);
      });
      return Array.from(groupMap.entries()).map(([label, vals]) => {
        return { label, avgHealth: vals.reduce((a, b) => a + b, 0) / vals.length };
      }).sort((a, b) => a.label.localeCompare(b.label));
    });

    const groups = avgByPeriod[0];
    const drops = [];
    for (let i = 1; i < groups.length; i++) {
        // Drop = Previous Health - Current Health. Positive means it degraded!
        const drop = groups[i-1].avgHealth - groups[i].avgHealth; 
        drops.push({
            label: groups[i].label,
            drop: drop
        });
    }

    if (drops.length === 0) return null;

    drops.sort((a, b) => b.drop - a.drop); // highest drop first

    return {
      worst: drops[0],
      best: drops[drops.length - 1],
      barChart: {
        labels: drops.map(d => d.label), // The array is sorted by magnitude, we should sort sequentially
      }
    };
  }, [data, period]);

  // Actually reconstruct bar chart sequential data for visual
  const barChartData = useMemo(() => {
    if (!degStats) return null;
    
    const manualGroupMap = new Map<string, number[]>();
    data.health_data.forEach(item => {
        let key = '';
        if (period === 'week') key = getISOWeekString(item.date);
        else if (period === 'month') key = getMonthString(item.date);
        else if (period === 'year') key = getYearString(item.date);
        if (!manualGroupMap.has(key)) manualGroupMap.set(key, []);
        manualGroupMap.get(key)!.push(item.health);
    });
    const sorted = Array.from(manualGroupMap.entries()).map(([label, vals]) => {
        return { label, avgHealth: vals.reduce((a, b) => a + b, 0) / vals.length };
    }).sort((a, b) => a.label.localeCompare(b.label));

    const labels = [];
    const values = [];
    for (let i = 1; i < sorted.length; i++) {
        labels.push(sorted[i].label);
        values.push(sorted[i-1].avgHealth - sorted[i].avgHealth); // Positive = degraded
    }

    return {
        labels,
        datasets: [{
            label: `Health Degradation % per ${period}`,
            data: values,
            backgroundColor: values.map(v => v > 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)'), // Red if degrading, Green if recovering magically
            borderRadius: 4
        }]
    }

  }, [data, period, degStats]);


  if (!chartData) {
    return <div className="glass-panel" style={{ padding: '2rem' }}>No initial capacity history found.</div>;
  }

  return (
    <div>
      <div className="dashboard-grid">
        <div className="glass-panel stat-card">
          <div className="stat-label">Current Health</div>
          <div className="stat-value" style={{ color: chartData.lineChart.datasets[0].data.slice(-1)[0] < 80 ? 'var(--danger)' : 'var(--success)' }}>
            {chartData.lineChart.datasets[0].data.slice(-1)[0]?.toFixed(2)}%
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-label">Worst Degradation ({period})</div>
          <div className="stat-value" style={{ color: 'var(--danger)' }}>
            {degStats?.worst?.drop.toFixed(2)}% <span style={{fontSize: '1rem', color: 'var(--text-secondary)'}}>in {degStats?.worst?.label}</span>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-label">Best {period}</div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>
            {degStats?.best?.drop.toFixed(2)}% <span style={{fontSize: '1rem', color: 'var(--text-secondary)'}}>in {degStats?.best?.label}</span>
          </div>
        </div>
      </div>

      <div className="glass-panel chart-container" style={{ height: '450px', marginBottom: '2rem' }}>
        <Line 
          data={chartData.lineChart} 
          options={{ 
            responsive: true, 
            maintainAspectRatio: false,
            scales: {
                y: { min: Math.max(0, chartData.minHealth - 5), max: 105 } // Focus the y-axis dynamically to the range of data
            },
            plugins: { title: { display: true, text: 'Overall Capacity History' } }
          }} 
        />
      </div>

      <div className="glass-panel chart-container" style={{ height: '400px' }}>
        <div className="chart-header">
           <h3 style={{ margin: 0 }}>Degradation Rate</h3>
           <select value={period} onChange={e => setPeriod(e.target.value as any)}>
               <option value="week">By Week (ISO Standard)</option>
               <option value="month">By Month</option>
               <option value="year">By Year</option>
           </select>
        </div>
        
        {barChartData && (
          <Bar 
            data={barChartData} 
            options={{ 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }} 
          />
        )}
      </div>

    </div>
  );
}
