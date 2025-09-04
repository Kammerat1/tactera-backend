import React, { useState, useEffect } from 'react';
import { BellIcon, MailIcon, SearchIcon, UserIcon, MenuIcon, LogOutIcon } from 'lucide-react';
import { api } from '../services/api';
type HeaderProps = {
  onMenuClick?: () => void;
  userData?: any;
  onLogout?: () => void;
};

export const Header = ({ onMenuClick, userData, onLogout }: HeaderProps) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [clubName, setClubName] = useState('Loading...');
  const [leagueName, setLeagueName] = useState('League');
  
  const managerName = userData?.managerName || 'Manager';
  const email = userData?.email || '';
  
  // For now, assuming manager is associated with club ID 1
  const clubId = 1;
  
  useEffect(() => {
    const fetchClubInfo = async () => {
      try {
        const financialData = await api.stadium.getFinancialSummary(clubId);
        setClubName(financialData.club_info?.name || 'Unknown Club');
        setLeagueName('League 1'); // TODO: Get actual league name
      } catch (err) {
        console.error('Failed to fetch club info:', err);
        setClubName('Unknown Club');
      }
    };
    
    fetchClubInfo();
  }, [clubId]);
  return (
    <>
      {/* Overlay to close dropdown when clicking outside */}
      {showUserMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowUserMenu(false)}
        />
      )}
      
      <header className="bg-gray-800 border-b border-gray-700 py-4 px-4 md:px-6 flex items-center justify-between relative z-50">
      <div className="flex items-center">
        {/* Mobile menu button */}
        <button 
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-md hover:bg-gray-700 mr-3 transition-colors duration-200"
        >
          <MenuIcon size={20} />
        </button>
        <h2 className="text-lg md:text-xl font-semibold">{clubName}</h2>
        <span className="ml-2 md:ml-3 px-2 py-1 bg-blue-600 text-xs font-medium rounded-md hidden sm:inline">
          {leagueName}
        </span>
      </div>
      <div className="flex items-center space-x-1 md:space-x-4">
        <div className="relative hidden md:block">
          <input type="text" placeholder="Search..." className="bg-gray-700 text-sm rounded-md py-2 pl-10 pr-4 text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500" />
          <SearchIcon size={18} className="absolute left-3 top-2.5 text-gray-400" />
        </div>
        <button className="p-2 rounded-md hover:bg-gray-700 relative">
          <MailIcon size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
        <button className="p-2 rounded-md hover:bg-gray-700 relative">
          <BellIcon size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>
        <div className="relative">
          <button 
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center ml-2 p-1 rounded-md hover:bg-gray-700 transition-colors duration-200"
          >
            <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
              <UserIcon size={18} />
            </div>
            <div className="ml-2 hidden md:block">
              <div className="text-sm font-medium">{managerName}</div>
              <div className="text-xs text-gray-400">Manager</div>
            </div>
          </button>
          
          {/* User dropdown menu */}
          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50">
              <div className="p-3 border-b border-gray-700">
                <div className="text-sm font-medium text-white">{managerName}</div>
                <div className="text-xs text-gray-400">{email}</div>
              </div>
              <div className="py-2">
                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    onLogout?.();
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white flex items-center transition-colors duration-200"
                >
                  <LogOutIcon size={16} className="mr-2" />
                  Sign out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      </header>
    </>
  );
};