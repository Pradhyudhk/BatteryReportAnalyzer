import { useMemo, useState } from 'react';
import type { BatteryReportData } from '../core/types';
import { predictDateForTargetHealth } from '../core/analyzer';
import { Line } from 'react-chartjs-2';

export default function ProjectionsTab({ data }: { data: BatteryReportData }) {
  const [targetHealth, setTargetHealth] = useState<number>(80);

  const projection = useMemo(() => {
    if (data.health_data.length < 2) return null;

    const futureDate = predictDateForTargetHealth(data.health_data, targetHealth);

    // Current health
    const currentHealth = data.health_data[data.health_data.length - 1].health;

    // We want to draw a line from the last known data point to the predicted point
    const lastDate = data.health_data[data.health_data.length - 1].date;

    const chartData = {
      labels: [lastDate.toLocaleDateString(), futureDate ? futureDate.toLocaleDateString() : 'Unknown'],
      datasets: [
        {
          label: 'Projected Degradation Path',
          data: [currentHealth, targetHealth],
          borderColor: 'rgba(245, 158, 11, 1)', // Warning yellow/orange
          borderDash: [5, 5],
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 4,
          pointBackgroundColor: 'rgba(245, 158, 11, 1)',
        }
      ]
    };

    return {
      futureDate,
      currentHealth,
      chartData
    };
  }, [data, targetHealth]);

  if (!projection) {
    return (
      <div className="glass-panel" style={{ padding: '2rem' }}>
        <h2>Insufficient Data</h2>
        <p>The linear regression model requires at least 2 consecutive health capacity readings to chart a slope. Check back later.</p>
      </div>
    );
  }

  return (
    <div>
        <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem' }}>
          <h2 style={{ marginBottom: '1rem', color: 'var(--text-primary)'}}>Health Projection Engine</h2>
          <p style={{ color: 'var(--text-secondary)' }}>
            Using Linear Regression (Ordinary Least Squares), this model calculates the slope of your historical capacity degradation and predicts when your battery will reach critical failure or replacement threshold.
          </p>
          
          <div style={{ marginTop: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <label style={{ fontWeight: 600 }}>Target Replacement Health (%):</label>
              <input 
                type="number" 
                value={targetHealth} 
                onChange={e => setTargetHealth(Number(e.target.value))} 
                min={1} 
                max={99}
                style={{ width: '80px', fontSize: '1.2rem', textAlign: 'center' }} 
              />
          </div>

          <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: 'var(--radius-md)'}}>
            {projection.futureDate ? (
               <div>
                  <h3 style={{ color: 'var(--warning)', margin: 0 }}>Predicted Replacement Date</h3>
                  <div style={{ fontSize: '2.5rem', fontWeight: 700, marginTop: '0.5rem' }}>
                    {projection.futureDate.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
                  </div>
                  <p style={{ marginTop: '0.5rem', color: 'var(--text-secondary)' }}>
                    Based on your current trajectory, you will drop to {targetHealth}% capacity in approximately {Math.max(0, Math.round((projection.futureDate.getTime() - new Date().getTime()) / 86400000))} days.
                  </p>
               </div>
            ) : (
               <div>
                 <h3 style={{ color: 'var(--success)', margin: 0 }}>Healthy Trajectory</h3>
                 <p style={{ marginTop: '0.5rem' }}>Your battery is currently maintaining a flat or increasing capacity slope. No degradation detected yet!</p>
               </div>
            )}
          </div>
        </div>

        {projection.futureDate && (
          <div className="glass-panel chart-container" style={{ height: '300px' }}>
            <div className="chart-header">
              <h3 style={{ margin: 0 }}>Projection Visualizer</h3>
            </div>
            <Line 
              data={projection.chartData} 
              options={{ 
                  responsive: true, 
                  maintainAspectRatio: false,
                  scales: { y: { min: Math.max(0, targetHealth - 5), max: Math.min(100, projection.currentHealth + 5) } }
              }} 
            />
          </div>
        )}
    </div>
  );
}
