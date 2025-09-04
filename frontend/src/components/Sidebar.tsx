import React, { useState } from 'react';
import { HomeIcon, UsersIcon, CalendarIcon, TrophyIcon, PieChartIcon, DollarSignIcon, ClipboardIcon, ShirtIcon, SettingsIcon, LogOutIcon, FileTextIcon, RefreshCwIcon, UsersRoundIcon, ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';
type SidebarProps = {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onClose?: () => void;
};
export const Sidebar = ({
  activeTab,
  setActiveTab,
  onClose
}: SidebarProps) => {
  const [collapsed, setCollapsed] = useState(false);
  const menuItems = [{
    id: 'dashboard',
    label: 'Dashboard',
    icon: <HomeIcon size={20} />
  }, {
    id: 'squad',
    label: 'Squad',
    icon: <UsersIcon size={20} />
  }, {
    id: 'tactics',
    label: 'Tactics',
    icon: <ClipboardIcon size={20} />
  }, {
    id: 'contracts',
    label: 'Contracts',
    icon: <FileTextIcon size={20} />
  }, {
    id: 'transfers',
    label: 'Transfers',
    icon: <RefreshCwIcon size={20} />
  }, {
    id: 'staff',
    label: 'Staff',
    icon: <UsersRoundIcon size={20} />
  }, {
    id: 'fixtures',
    label: 'Fixtures',
    icon: <CalendarIcon size={20} />
  }, {
    id: 'table',
    label: 'League Table',
    icon: <TrophyIcon size={20} />
  }, {
    id: 'training',
    label: 'Training',
    icon: <ShirtIcon size={20} />
  }, {
    id: 'finances',
    label: 'Finances',
    icon: <DollarSignIcon size={20} />
  }, {
    id: 'stats',
    label: 'Statistics',
    icon: <PieChartIcon size={20} />
  }];
  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };
  return <div className={`${collapsed ? 'w-16' : 'w-64'} bg-gray-800 border-r border-gray-700 flex flex-col transition-all duration-300 ease-in-out relative shadow-xl`}>
      {/* Toggle button */}
      <button onClick={toggleSidebar} className="absolute -right-3 top-20 bg-gray-700 hover:bg-gray-600 rounded-full p-1.5 border border-gray-600 text-gray-300 hover:text-white z-10 transition-all duration-200 shadow-lg hover:shadow-xl">
        {collapsed ? <ChevronRightIcon size={16} /> : <ChevronLeftIcon size={16} />}
      </button>
      <div className={`p-6 flex ${collapsed ? 'justify-center' : 'justify-start'} border-b border-gray-700/50`}>
        {collapsed ? <span className="text-2xl font-bold text-blue-400 tracking-wide">T</span> : <h1 className="text-xl font-bold text-blue-400 tracking-wide">Tactera</h1>}
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className={`${collapsed ? 'px-2' : 'px-4'} space-y-2`}>
          {menuItems.map(item => <button key={item.id} className={`group flex items-center w-full ${collapsed ? 'justify-center' : 'justify-start'} px-3 py-3 rounded-lg transition-all duration-200 ${activeTab === item.id ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`} onClick={() => setActiveTab(item.id)} title={collapsed ? item.label : ''}>
              <span className={`${collapsed ? '' : 'mr-3'} group-hover:scale-110 transition-transform duration-200`}>{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </button>)}
          
          {/* Mobile close area */}
          <div className="lg:hidden mt-4 px-4">
            <button 
              onClick={onClose}
              className="w-full px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-all duration-200 text-sm"
            >
              Close Menu
            </button>
          </div>
        </nav>
      </div>
      <div className={`p-4 border-t border-gray-700/50 ${collapsed ? 'flex flex-col items-center' : ''} bg-gray-800/50`}>
        <button className={`group flex items-center ${collapsed ? 'justify-center w-10 h-10' : 'w-full px-3 py-2'} text-gray-300 hover:bg-gray-700 hover:text-white rounded-lg transition-all duration-200`} title={collapsed ? 'Settings' : ''}>
          <span className={`${collapsed ? '' : 'mr-3'} group-hover:scale-110 transition-transform duration-200`}>
            <SettingsIcon size={20} />
          </span>
          {!collapsed && <span>Settings</span>}
        </button>
        <button className={`group flex items-center ${collapsed ? 'justify-center w-10 h-10 mt-2' : 'w-full px-3 py-2 mt-1'} text-gray-300 hover:bg-red-600 hover:text-white rounded-lg transition-all duration-200`} title={collapsed ? 'Logout' : ''}>
          <span className={`${collapsed ? '' : 'mr-3'} group-hover:scale-110 transition-transform duration-200`}>
            <LogOutIcon size={20} />
          </span>
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </div>;
};