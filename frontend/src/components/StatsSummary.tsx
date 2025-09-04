import React from 'react';
import { BarChartIcon, TrophyIcon, ShirtIcon } from 'lucide-react';
type StatsSummaryProps = {
  fullView?: boolean;
};
export const StatsSummary = ({
  fullView = false
}: StatsSummaryProps) => {
  const teamStats = {
    goals: {
      scored: 42,
      conceded: 18
    },
    possession: 58,
    passes: {
      completed: 12450,
      accuracy: 87
    },
    shots: {
      total: 325,
      onTarget: 142,
      accuracy: 44
    },
    discipline: {
      yellowCards: 28,
      redCards: 2
    }
  };
  const topScorers = [{
    id: 1,
    name: 'Bukayo Saka',
    position: 'RW',
    goals: 12,
    assists: 8
  }, {
    id: 2,
    name: 'Kai Havertz',
    position: 'CF',
    goals: 9,
    assists: 3
  }, {
    id: 3,
    name: 'Martin Ødegaard',
    position: 'AM',
    goals: 7,
    assists: 10
  }, {
    id: 4,
    name: 'Gabriel Martinelli',
    position: 'LW',
    goals: 6,
    assists: 4
  }];
  return <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold">Statistics</h2>
      </div>
      {!fullView ? <div className="p-4">
          <h3 className="text-sm font-medium text-gray-400 mb-3">
            Top Scorers
          </h3>
          <div className="space-y-2">
            {topScorers.slice(0, 3).map(player => <div key={player.id} className="flex justify-between items-center">
                <div className="flex items-center">
                  <div className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-700 text-xs mr-2">
                    {player.id}
                  </div>
                  <div>
                    <div className="text-sm">{player.name}</div>
                    <div className="text-xs text-gray-400">
                      {player.position}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold">
                    {player.goals} goals
                  </div>
                  <div className="text-xs text-gray-400">
                    {player.assists} assists
                  </div>
                </div>
              </div>)}
          </div>
        </div> : <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center">
                <BarChartIcon size={16} className="mr-1" />
                Team Stats
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Goals Scored/Conceded</span>
                    <span className="text-sm">
                      {teamStats.goals.scored}/{teamStats.goals.conceded}
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-l-full" style={{
                  width: `${teamStats.goals.scored / (teamStats.goals.scored + teamStats.goals.conceded) * 100}%`
                }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Possession</span>
                    <span className="text-sm">{teamStats.possession}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-l-full" style={{
                  width: `${teamStats.possession}%`
                }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Pass Accuracy</span>
                    <span className="text-sm">
                      {teamStats.passes.accuracy}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-l-full" style={{
                  width: `${teamStats.passes.accuracy}%`
                }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-sm">Shot Accuracy</span>
                    <span className="text-sm">{teamStats.shots.accuracy}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-blue-500 h-2 rounded-l-full" style={{
                  width: `${teamStats.shots.accuracy}%`
                }}></div>
                  </div>
                </div>
                <div className="flex justify-between">
                  <div className="text-sm">
                    <span className="text-yellow-400">■</span> Yellow Cards
                  </div>
                  <div className="text-sm">
                    {teamStats.discipline.yellowCards}
                  </div>
                </div>
                <div className="flex justify-between">
                  <div className="text-sm">
                    <span className="text-red-400">■</span> Red Cards
                  </div>
                  <div className="text-sm">{teamStats.discipline.redCards}</div>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-3 flex items-center">
                <ShirtIcon size={16} className="mr-1" />
                Top Scorers
              </h3>
              <div className="space-y-3">
                {topScorers.map(player => <div key={player.id} className="flex justify-between items-center p-2 bg-gray-750 rounded-md">
                    <div className="flex items-center">
                      <div className="w-6 h-6 flex items-center justify-center rounded-full bg-gray-700 text-xs mr-2">
                        {player.id}
                      </div>
                      <div>
                        <div className="text-sm">{player.name}</div>
                        <div className="text-xs text-gray-400">
                          {player.position}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold">
                        {player.goals} goals
                      </div>
                      <div className="text-xs text-gray-400">
                        {player.assists} assists
                      </div>
                    </div>
                  </div>)}
              </div>
            </div>
          </div>
        </div>}
    </div>;
};