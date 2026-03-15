import type { HealthData } from './types';

// Simple Linear Regression algorithm for Javascript, calculating slope and intercept
export function calculateLinearRegression(dataPoints: {x: number, y: number}[]) {
  const n = dataPoints.length;
  if (n < 2) return null;

  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

  for (let i = 0; i < n; i++) {
    const {x, y} = dataPoints[i];
    sumX += x;
    sumY += y;
    sumXY += (x * y);
    sumX2 += (x * x);
  }

  const denominator = ((n * sumX2) - (sumX * sumX));
  if (denominator === 0) return null; 

  const slope = ((n * sumXY) - (sumX * sumY)) / denominator;
  const intercept = (sumY - (slope * sumX)) / n;

  return { slope, intercept };
}

export function predictDateForTargetHealth(healthData: HealthData[], targetHealth: number): Date | null {
  if (healthData.length < 2) return null;

  // Convert dates to timestamps (seconds to prevent massive numbers breaking floating point precision)
  const dataPoints = healthData.map(d => ({
    x: d.date.getTime() / 1000, 
    y: d.health
  }));

  const model = calculateLinearRegression(dataPoints);
  
  if (!model) return null;
  // If slope is positive or zero, battery isn't degrading
  if (model.slope >= 0) return null;

  const { slope, intercept } = model;
  
  // Algebra: target = slope * x + intercept  =>  x = (target - intercept) / slope
  const targetTimestampSec = (targetHealth - intercept) / slope;
  
  if (targetTimestampSec <= 0) return null; // Overflow or error

  return new Date(targetTimestampSec * 1000);
}

export function pearsonCorrelation(x: number[], y: number[]): number {
  if (x.length !== y.length || x.length === 0) return 0;
  const n = x.length;

  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;

  for (let i = 0; i < n; i++) {
    sumX += x[i];
    sumY += y[i];
    sumXY += x[i] * y[i];
    sumX2 += x[i] * x[i];
    sumY2 += y[i] * y[i];
  }

  const numerator = (n * sumXY) - (sumX * sumY);
  const denominator = Math.sqrt(((n * sumX2) - (sumX * sumX)) * ((n * sumY2) - (sumY * sumY)));
  
  if (denominator === 0) return 0;
  return numerator / denominator;
}
