import React from 'react';
import { AwardIcon, TrendingUpIcon, TrendingDownIcon } from 'lucide-react';
export const ClubRanking = () => {
  const rankings = [{
    id: 1,
    category: 'UEFA Club Ranking',
    position: 8,
    change: 2,
    total: '85.000 pts'
  }, {
    id: 2,
    category: 'World Club Ranking',
    position: 12,
    change: -1,
    total: '1820 pts'
  }, {
    id: 3,
    category: 'League Reputation',
    position: 3,
    change: 0,
    total: '4.5 stars'
  }];
  return <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold flex items-center">
          <AwardIcon size={18} className="mr-2" />
          Club Ranking
        </h2>
      </div>
      <div className="p-4">
        <div className="space-y-4">
          {rankings.map(rank => <div key={rank.id} className="bg-gray-750 p-3 rounded-md">
              <div className="text-xs text-gray-400">{rank.category}</div>
              <div className="flex items-center justify-between mt-1">
                <div className="flex items-center">
                  <span className="text-lg font-bold">
                    {rank.position.toString().padStart(2, '0')}
                  </span>
                  {rank.change > 0 && <span className="flex items-center ml-2 text-green-400 text-xs">
                      <TrendingUpIcon size={14} className="mr-1" /> +
                      {rank.change}
                    </span>}
                  {rank.change < 0 && <span className="flex items-center ml-2 text-red-400 text-xs">
                      <TrendingDownIcon size={14} className="mr-1" />{' '}
                      {rank.change}
                    </span>}
                  {rank.change === 0 && <span className="ml-2 text-gray-400 text-xs">—</span>}
                </div>
                <span className="text-sm">{rank.total}</span>
              </div>
            </div>)}
        </div>
      </div>
    </div>;
};