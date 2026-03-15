import { useState } from 'react';
import type { BatteryReportData } from '../core/types';
import DegradationTab from './DegradationTab';
import UsageTab from './UsageTab';
import ProjectionsTab from './ProjectionsTab';
import { Activity, BatteryCharging, TrendingUp, Info } from 'lucide-react';

interface Props {
  data: BatteryReportData;
}

type TabType = 'degradation' | 'usage' | 'projections' | 'info';

export default function Dashboard({ data }: Props) {
  const [activeTab, setActiveTab] = useState<TabType>('degradation');

  const renderTab = () => {
    switch (activeTab) {
      case 'degradation':
        return <DegradationTab data={data} />;
      case 'usage':
        return <UsageTab data={data} />;
      case 'projections':
        return <ProjectionsTab data={data} />;
      case 'info':
        return (
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <h2>Battery Hardware Meta Info</h2>
            <div style={{ marginTop: '1.5rem', display: 'grid', gap: '1rem' }}>
              <p><strong>Manufacturer: </strong> {data.installed_batteries.manufacturer || 'Unknown'}</p>
              <p><strong>Model Name: </strong> {data.installed_batteries.name || 'Unknown'}</p>
              <p><strong>Serial Number: </strong> {data.installed_batteries.serial_number || 'Unknown'}</p>
              <p><strong>Design Capacity: </strong> {data.installed_batteries.design_capacity ? `${data.installed_batteries.design_capacity.toLocaleString()} mWh` : 'Unknown'}</p>
            </div>
            
            <button 
              className="btn" 
              style={{ marginTop: '2rem' }}
              onClick={() => window.open(`https://www.batterylookup.com/search?q=${data.installed_batteries.name || ''}`)}
            >
              Search Web for Replacement
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s' }}>
      <nav className="tabs-nav">
        <button 
          className={`tab-btn ${activeTab === 'degradation' ? 'active' : ''}`}
          onClick={() => setActiveTab('degradation')}
        >
          <TrendingUp size={18} /> Degradation
        </button>
        <button 
          className={`tab-btn ${activeTab === 'usage' ? 'active' : ''}`}
          onClick={() => setActiveTab('usage')}
        >
          <Activity size={18} /> Usage Patterns
        </button>
        <button 
          className={`tab-btn ${activeTab === 'projections' ? 'active' : ''}`}
          onClick={() => setActiveTab('projections')}
        >
          <BatteryCharging size={18} /> Projections
        </button>
        <button 
          className={`tab-btn ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          <Info size={18} /> Hardware Info
        </button>
      </nav>

      <main>
        {renderTab()}
      </main>
    </div>
  );
}
