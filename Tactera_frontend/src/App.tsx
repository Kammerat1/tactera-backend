import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { NewsBox } from './components/NewsBox';
import { TeamOverview } from './components/TeamOverview';
import { PlayerRoster } from './components/PlayerRoster';
import { Fixtures } from './components/Fixtures';
import { LeagueTable } from './components/LeagueTable';
import { FinancialSummary } from './components/FinancialSummary';
import { StatsSummary } from './components/StatsSummary';
import { ClubRanking } from './components/ClubRanking';
export function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  return <div className="flex h-screen bg-gray-900 text-white">
      <style jsx global>{`
        .transition-width {
          transition-property: width;
        }
      `}</style>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {activeTab === 'dashboard' && <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <NewsBox />
                <TeamOverview />
                <div className="mt-6">
                  <PlayerRoster />
                </div>
              </div>
              <div className="space-y-6">
                <FinancialSummary />
                <ClubRanking />
                <Fixtures />
                <LeagueTable />
                <StatsSummary />
              </div>
            </div>}
          {activeTab === 'squad' && <PlayerRoster fullView={true} />}
          {activeTab === 'fixtures' && <Fixtures fullView={true} />}
          {activeTab === 'table' && <LeagueTable fullView={true} />}
          {activeTab === 'finances' && <FinancialSummary fullView={true} />}
          {activeTab === 'stats' && <StatsSummary fullView={true} />}
          {activeTab === 'contracts' && <div className="p-4 bg-gray-800 rounded-lg">
              Contracts management coming soon
            </div>}
          {activeTab === 'transfers' && <div className="p-4 bg-gray-800 rounded-lg">
              Transfer market coming soon
            </div>}
          {activeTab === 'staff' && <div className="p-4 bg-gray-800 rounded-lg">
              Staff management coming soon
            </div>}
        </main>
      </div>
    </div>;
}