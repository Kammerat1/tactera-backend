import React from 'react';
import { BellIcon, MailIcon, SearchIcon, UserIcon } from 'lucide-react';
export const Header = () => {
  return <header className="bg-gray-800 border-b border-gray-700 py-4 px-6 flex items-center justify-between">
      <div className="flex items-center">
        <h2 className="text-xl font-semibold">Arsenal FC</h2>
        <span className="ml-3 px-2 py-1 bg-blue-600 text-xs font-medium rounded-md">
          Premier League
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
        <div className="flex items-center ml-2">
          <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
            <UserIcon size={18} />
          </div>
          <div className="ml-2 hidden md:block">
            <div className="text-sm font-medium">John Smith</div>
            <div className="text-xs text-gray-400">Manager</div>
          </div>
        </div>
      </div>
    </header>;
};