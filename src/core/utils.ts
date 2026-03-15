// ISO Week Date grouping
export function getISOWeekString(d: Date): string {
  const date = new Date(d.getTime());
  date.setHours(0, 0, 0, 0);
  
  // Thursday in current week decides the year.
  date.setDate(date.getDate() + 3 - (date.getDay() + 6) % 7);
  
  // January 4 is always in week 1.
  const week1 = new Date(date.getFullYear(), 0, 4);
  
  // Adjust to Thursday in week 1 and count number of weeks from date to week1.
  const weekNumber = 1 + Math.round(((date.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
  
  return `${date.getFullYear()}-W${weekNumber.toString().padStart(2, '0')}`;
}

export function getMonthString(d: Date): string {
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}`;
}

export function getYearString(d: Date): string {
  return `${d.getFullYear()}`;
}

export function groupDataByPeriod<T>(
  data: T[], 
  dateSelector: (item: T) => Date, 
  valueSelector: (item: T) => number,
  periodType: 'week' | 'month' | 'year'
): { label: string; value: number }[] {
  const map = new Map<string, number>();

  data.forEach(item => {
    const d = dateSelector(item);
    let key = '';
    
    if (periodType === 'week') key = getISOWeekString(d);
    else if (periodType === 'month') key = getMonthString(d);
    else if (periodType === 'year') key = getYearString(d);
    
    if (!map.has(key)) {
      map.set(key, 0);
    }
    map.set(key, map.get(key)! + valueSelector(item));
  });

  // Convert map to sorted array
  return Array.from(map.entries())
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => a.label.localeCompare(b.label));
}
