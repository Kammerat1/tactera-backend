import React from 'react';
import { TrendingUpIcon, TrendingDownIcon, ActivityIcon, CircleIcon } from 'lucide-react';
export const TeamOverview = () => {
  return <div className="bg-gray-800 rounded-lg shadow-md p-5">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Team Overview</h2>
        <span className="text-xs px-2 py-1 bg-green-600 rounded-full">
          In Form
        </span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-700 p-3 rounded-md">
          <div className="text-xs text-gray-400">Form</div>
          <div className="flex items-center mt-1 space-x-1">
            <span className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center text-xs">
              W
            </span>
            <span className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center text-xs">
              W
            </span>
            <span className="w-4 h-4 rounded-full bg-gray-500 flex items-center justify-center text-xs">
              D
            </span>
            <span className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center text-xs">
              W
            </span>
            <span className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center text-xs">
              L
            </span>
          </div>
        </div>
        <div className="bg-gray-700 p-3 rounded-md">
          <div className="text-xs text-gray-400">Position</div>
          <div className="flex items-center mt-1">
            <span className="text-lg font-bold">3rd</span>
            <span className="flex items-center ml-2 text-green-400 text-xs">
              <TrendingUpIcon size={14} className="mr-1" /> +1
            </span>
          </div>
        </div>
        <div className="bg-gray-700 p-3 rounded-md">
          <div className="text-xs text-gray-400">Goals</div>
          <div className="flex items-center mt-1">
            <span className="text-lg font-bold">42:18</span>
            <span className="ml-2 text-xs text-gray-400">+24</span>
          </div>
        </div>
        <div className="bg-gray-700 p-3 rounded-md">
          <div className="text-xs text-gray-400">Points</div>
          <div className="flex items-center mt-1">
            <span className="text-lg font-bold">36</span>
            <span className="flex items-center ml-2 text-green-400 text-xs">
              <ActivityIcon size={14} className="mr-1" /> 2.0 PPG
            </span>
          </div>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-700 p-4 rounded-md">
          <div className="text-sm font-medium mb-2">Team Morale</div>
          <div className="flex items-center">
            <div className="w-full bg-gray-600 rounded-full h-2.5">
              <div className="bg-green-500 h-2.5 rounded-full" style={{
              width: '85%'
            }}></div>
            </div>
            <span className="ml-2 text-sm">85%</span>
          </div>
        </div>
        <div className="bg-gray-700 p-4 rounded-md">
          <div className="text-sm font-medium mb-2">Fitness</div>
          <div className="flex items-center">
            <div className="w-full bg-gray-600 rounded-full h-2.5">
              <div className="bg-yellow-500 h-2.5 rounded-full" style={{
              width: '72%'
            }}></div>
            </div>
            <span className="ml-2 text-sm">72%</span>
          </div>
        </div>
        <div className="bg-gray-700 p-4 rounded-md">
          <div className="text-sm font-medium mb-2">Next Match</div>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <CircleIcon size={8} className="text-red-500 mr-1" />
              <span className="text-sm">vs Liverpool (A)</span>
            </div>
            <span className="text-xs text-gray-400">In 2 days</span>
          </div>
        </div>
      </div>
    </div>;
};