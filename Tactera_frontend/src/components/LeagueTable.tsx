import React from 'react';
import { ChevronUpIcon, ChevronDownIcon, MinusIcon } from 'lucide-react';
type LeagueTableProps = {
  fullView?: boolean;
};
export const LeagueTable = ({
  fullView = false
}: LeagueTableProps) => {
  const teams = [{
    id: 1,
    position: 1,
    change: 0,
    name: 'Manchester City',
    played: 18,
    won: 14,
    drawn: 2,
    lost: 2,
    gd: '+28',
    points: 44
  }, {
    id: 2,
    position: 2,
    change: 1,
    name: 'Liverpool',
    played: 18,
    won: 12,
    drawn: 5,
    lost: 1,
    gd: '+24',
    points: 41
  }, {
    id: 3,
    position: 3,
    change: -1,
    name: 'Arsenal',
    played: 18,
    won: 11,
    drawn: 3,
    lost: 4,
    gd: '+24',
    points: 36
  }, {
    id: 4,
    position: 4,
    change: 0,
    name: 'Aston Villa',
    played: 18,
    won: 11,
    drawn: 3,
    lost: 4,
    gd: '+15',
    points: 36
  }, {
    id: 5,
    position: 5,
    change: 1,
    name: 'Tottenham',
    played: 18,
    won: 10,
    drawn: 3,
    lost: 5,
    gd: '+8',
    points: 33
  }, {
    id: 6,
    position: 6,
    change: -1,
    name: 'West Ham',
    played: 18,
    won: 9,
    drawn: 3,
    lost: 6,
    gd: '+5',
    points: 30
  }, {
    id: 7,
    position: 7,
    change: 0,
    name: 'Brighton',
    played: 18,
    won: 8,
    drawn: 6,
    lost: 4,
    gd: '+4',
    points: 30
  }, {
    id: 8,
    position: 8,
    change: 0,
    name: 'Man United',
    played: 18,
    won: 9,
    drawn: 1,
    lost: 8,
    gd: '-1',
    points: 28
  }];
  // Highlight positions for Champions League, Europa League, and Relegation
  const getPositionClass = (position: number) => {
    if (position <= 4) return 'border-l-4 border-blue-500 pl-2';
    if (position <= 6) return 'border-l-4 border-orange-500 pl-2';
    if (position >= 18) return 'border-l-4 border-red-500 pl-2';
    return 'pl-3';
  };
  const getChangeIcon = (change: number) => {
    if (change > 0) return <ChevronUpIcon size={16} className="text-green-500" />;
    if (change < 0) return <ChevronDownIcon size={16} className="text-red-500" />;
    return <MinusIcon size={16} className="text-gray-500" />;
  };
  const displayedTeams = fullView ? teams : teams.slice(0, 6);
  return <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold">Premier League</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-gray-700">
            <tr>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Pos
              </th>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Team
              </th>
              <th scope="col" className="px-3 py-2 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                P
              </th>
              {fullView && <>
                  <th scope="col" className="px-3 py-2 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                    W
                  </th>
                  <th scope="col" className="px-3 py-2 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                    D
                  </th>
                  <th scope="col" className="px-3 py-2 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                    L
                  </th>
                </>}
              <th scope="col" className="px-3 py-2 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                GD
              </th>
              <th scope="col" className="px-3 py-2 text-center text-xs font-medium text-gray-300 uppercase tracking-wider">
                Pts
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {displayedTeams.map(team => <tr key={team.id} className={team.name === 'Arsenal' ? 'bg-blue-900/20' : ''}>
                <td className={`py-2 whitespace-nowrap text-sm ${getPositionClass(team.position)}`}>
                  <div className="flex items-center">
                    {team.position}
                    <span className="ml-1">{getChangeIcon(team.change)}</span>
                  </div>
                </td>
                <td className="px-3 py-2 whitespace-nowrap">
                  <div className="text-sm">{team.name}</div>
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-center text-sm">
                  {team.played}
                </td>
                {fullView && <>
                    <td className="px-3 py-2 whitespace-nowrap text-center text-sm">
                      {team.won}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-center text-sm">
                      {team.drawn}
                    </td>
                    <td className="px-3 py-2 whitespace-nowrap text-center text-sm">
                      {team.lost}
                    </td>
                  </>}
                <td className="px-3 py-2 whitespace-nowrap text-center text-sm">
                  {team.gd}
                </td>
                <td className="px-3 py-2 whitespace-nowrap text-center text-sm font-bold">
                  {team.points}
                </td>
              </tr>)}
          </tbody>
        </table>
      </div>
      {!fullView && <div className="p-2 border-t border-gray-700 text-center">
          <button className="text-sm text-blue-400 hover:text-blue-300">
            View full table
          </button>
        </div>}
    </div>;
};