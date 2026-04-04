import React from 'react';
import { type Commodity } from '../api-client';
import { listCommoditiesCommoditiesGet } from '../api-client/sdk.gen';
import { client } from '../api-client/client.gen';
import * as Lucide from 'lucide-react';
import './dashboard.css';

// MODIFIED BY AI - PREMIUM FINTECH UPGRADE
// 设置 API 基础路径
client.setConfig({
  baseUrl: 'http://localhost:8000',
});

export const dynamic = 'force-dynamic';

/**
 * Dynamic Icon Component to map icon strings from API to Lucide components
 */
const IconComponent = ({ name, className }: { name: string; className?: string }) => {
  // @ts-ignore - name comes from backend contract
  const Icon = Lucide[name] || Lucide.Globe;
  return <Icon className={className} size={20} />;
};

/**
 * Global Commodity Dashboard (Next.js App Router)
 * Displays professional-grade commodity data with full contract-driven type support.
 */
export default async function CommoditiesDashboard() {
  // 1. 调用自动生成的契约函数 (Using SDK instead of raw fetch for full safety)
  const { data: commodities, error } = await listCommoditiesCommoditiesGet({
    // @ts-ignore - Next.js extra fetch options are supported by the client
    cache: 'no-store' 
  });

  if (error || !commodities) {
    return (
      <div className="dashboard-container">
        <div className="header">
          <h1>Market Unavailable</h1>
        </div>
        <p>Error connecting to Global Liquidity Hub (FastAPI Backend)...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="header">
        <div>
          <span className="category-tag">Real-time Global Market Data</span>
          <h1>Commodity Pulse</h1>
        </div>
        <div className="market-status">
          <span className="status-dot"></span>
          Live Exchange Status: Operational
        </div>
      </header>

      <div className="grid">
        {commodities.map((item: Commodity) => (
          <div key={item.ticker} className="card">
            <div className={`trend-badge trend-${item.trend}`}>
              {item.trend}
            </div>
            
            <div className="card-header">
              <div className="title-with-icon">
                <div className={`icon-container cat-${item.category.toLowerCase().replace(' ', '-')}`}>
                  <IconComponent name={item.icon} />
                </div>
                <div>
                  <span className="ticker">{item.ticker}</span>
                  <span className="name">{item.name}</span>
                </div>
              </div>
              <span className="category-tag">{item.category}</span>
            </div>
            
            <div className="price-section">
              <div className="price">
                ${item.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                <span className="unit">USD/{item.unit}</span>
              </div>
              
              <div className={`change ${item.change_pct >= 0 ? 'plus' : 'minus'}`}>
                <span className="change-abs">
                  {item.change_abs >= 0 ? '+' : ''}{item.change_abs.toFixed(2)}
                </span>
                <span className="change-pct">
                  ({item.change_pct >= 0 ? '+' : ''}{item.change_pct.toFixed(2)}%)
                </span>
                <span style={{ fontSize: '0.7rem', color: '#94a3b8', marginLeft: '4px' }}>
                  (24H)
                </span>
              </div>
            </div>

            <div className="card-footer-meta">
              Updated: {item.last_updated}
            </div>
          </div>
        ))}
      </div>

      <footer className="footer">
        <p>© 2026 Global Commodities Exchange • API-First Architecture • Next.js + FastAPI</p>
      </footer>
    </div>
  );
}
