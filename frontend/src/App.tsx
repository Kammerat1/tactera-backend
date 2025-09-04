import React, { useState, useEffect } from 'react';
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
import { AuthContainer } from './components/AuthContainer';
export function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userData, setUserData] = useState<any>(null);

  // Check if user is already logged in on app start
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const email = localStorage.getItem('userEmail');
    const managerName = localStorage.getItem('managerName');
    
    if (token && email) {
      setIsAuthenticated(true);
      setUserData({ email, managerName });
    }
  }, []);

  const handleAuthSuccess = (userData: any) => {
    setIsAuthenticated(true);
    setUserData(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('managerName');
    setIsAuthenticated(false);
    setUserData(null);
  };

  // Show authentication screen if not logged in
  if (!isAuthenticated) {
    return <AuthContainer onAuthSuccess={handleAuthSuccess} />;
  }
  
  return <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      <style jsx global>{`
        .transition-width {
          transition-property: width;
        }
      `}</style>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <div className={`fixed lg:static inset-y-0 left-0 z-30 transform transition-transform duration-300 lg:transform-none ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}>
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} onClose={() => setSidebarOpen(false)} />
      </div>
      <div className="flex flex-col flex-1 overflow-hidden lg:ml-0">
        <Header 
          onMenuClick={() => setSidebarOpen(true)} 
          userData={userData} 
          onLogout={handleLogout} 
        />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800">
          {activeTab === 'dashboard' && <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 md:gap-6 max-w-7xl mx-auto">
              <div className="xl:col-span-2 space-y-6">
                <div className="grid gap-6">
                  <NewsBox />
                  <TeamOverview />
                  <PlayerRoster />
                </div>
              </div>
              <div className="space-y-4 md:space-y-6">
                <FinancialSummary />
                <ClubRanking />
                <Fixtures />
                <LeagueTable />
                <StatsSummary />
              </div>
            </div>}
          {activeTab === 'squad' && <div className="max-w-7xl mx-auto"><PlayerRoster fullView={true} /></div>}
          {activeTab === 'fixtures' && <div className="max-w-7xl mx-auto"><Fixtures fullView={true} /></div>}
          {activeTab === 'table' && <div className="max-w-7xl mx-auto"><LeagueTable fullView={true} /></div>}
          {activeTab === 'finances' && <div className="max-w-7xl mx-auto"><FinancialSummary fullView={true} /></div>}
          {activeTab === 'stats' && <div className="max-w-7xl mx-auto"><StatsSummary fullView={true} /></div>}
          {activeTab === 'contracts' && <div className="max-w-4xl mx-auto p-8 bg-gray-800 rounded-xl shadow-lg border border-gray-700">
              <h2 className="text-2xl font-bold mb-4 text-center">Contracts Management</h2>
              <p className="text-gray-400 text-center">Coming soon - Player contract negotiations and renewals</p>
            </div>}
          {activeTab === 'transfers' && <div className="max-w-4xl mx-auto p-8 bg-gray-800 rounded-xl shadow-lg border border-gray-700">
              <h2 className="text-2xl font-bold mb-4 text-center">Transfer Market</h2>
              <p className="text-gray-400 text-center">Coming soon - Buy and sell players</p>
            </div>}
          {activeTab === 'staff' && <div className="max-w-4xl mx-auto p-8 bg-gray-800 rounded-xl shadow-lg border border-gray-700">
              <h2 className="text-2xl font-bold mb-4 text-center">Staff Management</h2>
              <p className="text-gray-400 text-center">Coming soon - Hire coaches and support staff</p>
            </div>}
        </main>
      </div>
    </div>;
}