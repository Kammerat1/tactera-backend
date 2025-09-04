import React from 'react';
import { NewspaperIcon, ExternalLinkIcon } from 'lucide-react';
export const NewsBox = () => {
  const news = [{
    id: 1,
    title: 'Martin Ødegaard wins Player of the Month',
    date: '2 days ago',
    type: 'club'
  }, {
    id: 2,
    title: 'Transfer rumors: Arsenal interested in Victor Osimhen',
    date: '3 days ago',
    type: 'transfer'
  }, {
    id: 3,
    title: 'Champions League draw announced',
    date: '5 days ago',
    type: 'competition'
  }];
  return <div className="bg-gray-800 rounded-lg shadow-md mb-6">
      <div className="p-4 border-b border-gray-700 flex justify-between items-center">
        <h2 className="text-lg font-semibold flex items-center">
          <NewspaperIcon size={18} className="mr-2" />
          Latest News
        </h2>
        <button className="text-sm text-blue-400 hover:text-blue-300 flex items-center">
          View all
          <ExternalLinkIcon size={14} className="ml-1" />
        </button>
      </div>
      <div className="p-4">
        <div className="space-y-3">
          {news.map(item => <div key={item.id} className="flex justify-between items-center border-b border-gray-700 pb-2 last:border-0 last:pb-0">
              <div className="flex items-center">
                <span className={`w-2 h-2 rounded-full mr-2 ${item.type === 'club' ? 'bg-blue-500' : item.type === 'transfer' ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
                <span className="text-sm">{item.title}</span>
              </div>
              <span className="text-xs text-gray-400">{item.date}</span>
            </div>)}
        </div>
      </div>
    </div>;
};