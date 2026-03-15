export interface BatteryMeta {
  manufacturer: string;
  name: string;
  serial_number: string;
  design_capacity: number;
}

export interface HealthData {
  date: Date;
  health: number; // percentage (0-100)
}

export interface UsageData {
  date: Date;
  hours_used: number;
}

export interface BatteryReportData {
  installed_batteries: Partial<BatteryMeta>;
  health_data: HealthData[];
  usage_data: UsageData[];
}
