import type { BatteryReportData } from './types';

// Helper to safely parse localized or comma-separated numbers from the HTML
function parseCapacity(text: string): number {
  const match = text.match(/\d[\d,]*/);
  if (!match) return 0;
  return parseInt(match[0].replace(/,/g, ''), 10);
}

// Helper to parse duration strings like "1.12:30:00" or "01:15:30" into hours (floating point)
function parseDurationToHours(durationStr: string): number {
  // Pattern looking for optional days "d." followed by "hh:mm:ss"
  const regex = /(?:(\d+)\.)?(\d{1,2}):(\d{2}):(\d{2})/;
  const match = durationStr.match(regex);
  if (!match) return 0;

  const days = match[1] ? parseInt(match[1], 10) : 0;
  const hours = parseInt(match[2], 10);
  const minutes = parseInt(match[3], 10);
  const seconds = parseInt(match[4], 10);

  return (days * 24) + hours + (minutes / 60) + (seconds / 3600);
}

export function parseBatteryReport(htmlContent: string): BatteryReportData {
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlContent, 'text/html');

  const reportData: BatteryReportData = {
    installed_batteries: {},
    health_data: [],
    usage_data: []
  };

  // Helper to find a table safely immediately following a specific heading text
  const findTableAfterHeading = (headingMatch: string | RegExp) => {
    // Look through all headings
    const headings = doc.querySelectorAll('h2, h3, div');
    for (let i = 0; i < headings.length; i++) {
      const text = headings[i].textContent || "";
      if (text.match(headingMatch)) {
        // Find the next sibling that is a table
        let nextNode = headings[i].nextElementSibling;
        while (nextNode) {
          if (nextNode.tagName.toLowerCase() === 'table') {
            return nextNode as HTMLTableElement;
          }
          nextNode = nextNode.nextElementSibling;
        }
      }
    }
    return null;
  };

  // 1. Parse Installed Batteries
  const batteryTable = findTableAfterHeading(/Installed batteries/i);
  if (batteryTable) {
    const rows = batteryTable.querySelectorAll('tr');
    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      if (cells.length >= 2) {
        const key = (cells[0].textContent || "").trim().toLowerCase().replace(/ /g, '_');
        const valText = (cells[1].textContent || "").trim();
        
        if (key === 'design_capacity' || key === 'full_charge_capacity') {
          (reportData.installed_batteries as any)[key] = parseCapacity(valText);
        } else {
          (reportData.installed_batteries as any)[key] = valText;
        }
      }
    });
  }

  // 2. Parse Battery Capacity History
  const capacityTable = findTableAfterHeading(/Battery capacity history/i);
  const tempHealthData = new Map<string, number[]>(); // map dateString to array of health% to average it later

  if (capacityTable) {
    const rows = capacityTable.querySelectorAll('tr');
    // Skip header row usually index 0
    for (let i = 1; i < rows.length; i++) {
      const cells = rows[i].querySelectorAll('td');
      if (cells.length >= 3) {
        const periodText = (cells[0].textContent || "").trim();
        const fullChargeText = (cells[1].textContent || "").trim();
        const designCapText = (cells[2].textContent || "").trim();

        const fullCharge = parseCapacity(fullChargeText);
        const designCapacity = parseCapacity(designCapText);

        if (designCapacity === 0) continue; // Skip bad capacity data

        const dateMatch = periodText.match(/\d{4}-\d{2}-\d{2}$/);
        if (dateMatch) {
          const dateStr = dateMatch[0];
          const health = (fullCharge / designCapacity) * 100;

          if (!tempHealthData.has(dateStr)) {
            tempHealthData.set(dateStr, []);
          }
          tempHealthData.get(dateStr)!.push(health);
        }
      }
    }
  }

  // Aggregate duplicate days by averaging (fixes bug 2 from implementation plan)
  const sortedDates = Array.from(tempHealthData.keys()).sort();
  sortedDates.forEach(dateStr => {
    const vals = tempHealthData.get(dateStr)!;
    const avgHealth = vals.reduce((a, b) => a + b, 0) / vals.length;
    reportData.health_data.push({
      date: new Date(dateStr + "T00:00:00"), // Force local 00:00 time
      health: avgHealth
    });
  });


  // 3. Parse Battery Usage
  const usageTable = findTableAfterHeading(/Battery usage/i);
  if (usageTable) {
    const rows = usageTable.querySelectorAll('tr');
    for (let i = 1; i < rows.length; i++) {
      const cells = rows[i].querySelectorAll('td');
      if (cells.length >= 4) {
        const startTime = (cells[0].textContent || "").trim();
        const state = (cells[1].textContent || "").trim();
        const duration = (cells[2].textContent || "").trim();
        const energyDrained = (cells[3].textContent || "").trim();

        if (energyDrained !== '-' && (state === 'Active' || state === 'Connected standby')) {
          const hours = parseDurationToHours(duration);
          if (hours > 0) {
            // "2023-11-20 14:35:00" -> parsing to local Date works cleanly replacing space with T if needed, or parse directly
            const dateObj = new Date(startTime.replace(' ', 'T'));
            if (!isNaN(dateObj.getTime())) {
              reportData.usage_data.push({
                date: dateObj,
                hours_used: hours
              });
            }
          }
        }
      }
    }
  }

  // Sort usage strictly ascending
  reportData.usage_data.sort((a, b) => a.date.getTime() - b.date.getTime());

  return reportData;
}
