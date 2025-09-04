import React from 'react';
import { CalendarIcon } from 'lucide-react';
type FixturesProps = {
  fullView?: boolean;
};
export const Fixtures = ({
  fullView = false
}: FixturesProps) => {
  const fixtures = [{
    id: 1,
    competition: 'Premier League',
    home: false,
    opponent: 'Liverpool',
    date: 'Sat, 15 Oct',
    time: '17:30',
    difficulty: 'hard'
  }, {
    id: 2,
    competition: 'Champions League',
    home: true,
    opponent: 'Barcelona',
    date: 'Tue, 18 Oct',
    time: '20:00',
    difficulty: 'hard'
  }, {
    id: 3,
    competition: 'Premier League',
    home: true,
    opponent: 'Crystal Palace',
    date: 'Sat, 22 Oct',
    time: '15:00',
    difficulty: 'medium'
  }, {
    id: 4,
    competition: 'EFL Cup',
    home: false,
    opponent: 'Brighton',
    date: 'Wed, 26 Oct',
    time: '19:45',
    difficulty: 'medium'
  }, {
    id: 5,
    competition: 'Premier League',
    home: false,
    opponent: 'Nottingham Forest',
    date: 'Sat, 29 Oct',
    time: '15:00',
    difficulty: 'easy'
  }, {
    id: 6,
    competition: 'Champions League',
    home: false,
    opponent: 'Bayern Munich',
    date: 'Wed, 2 Nov',
    time: '20:00',
    difficulty: 'hard'
  }];
  const results = [{
    id: 1,
    competition: 'Premier League',
    home: true,
    opponent: 'Tottenham',
    result: 'W 2-0',
    score: '2-0'
  }, {
    id: 2,
    competition: 'Champions League',
    home: false,
    opponent: 'PSG',
    result: 'D',
    score: '1-1'
  }, {
    id: 3,
    competition: 'Premier League',
    home: false,
    opponent: 'Man City',
    result: 'L',
    score: '0-1'
  }, {
    id: 4,
    competition: 'Premier League',
    home: true,
    opponent: 'Everton',
    result: 'W',
    score: '3-1'
  }];
  const difficultyColors = {
    easy: 'bg-green-600',
    medium: 'bg-yellow-600',
    hard: 'bg-red-600'
  };
  const resultColors = {
    W: 'text-green-400',
    D: 'text-yellow-400',
    L: 'text-red-400'
  };
  const displayedFixtures = fullView ? fixtures : fixtures.slice(0, 3);
  const displayedResults = fullView ? results : results.slice(0, 2);
  return <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold">Fixtures & Results</h2>
      </div>
      <div className="p-4">
        <h3 className="text-sm font-medium text-gray-400 mb-3">
          Upcoming Fixtures
        </h3>
        <div className="space-y-3">
          {displayedFixtures.map(fixture => <div key={fixture.id} className="flex items-center justify-between p-2 bg-gray-750 rounded-md">
              <div className="flex items-center">
                <div className={`w-2 h-full mr-3 rounded-sm ${difficultyColors[fixture.difficulty as keyof typeof difficultyColors]}`}></div>
                <div>
                  <div className="text-sm font-medium">
                    {fixture.home ? 'vs ' : '@ '}
                    {fixture.opponent}
                  </div>
                  <div className="text-xs text-gray-400">
                    {fixture.competition}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm">{fixture.date}</div>
                <div className="text-xs text-gray-400">{fixture.time}</div>
              </div>
            </div>)}
        </div>
        {fullView && <div className="flex justify-center mt-4">
            <button className="flex items-center text-blue-400 hover:text-blue-300 text-sm">
              <CalendarIcon size={14} className="mr-1" />
              View full calendar
            </button>
          </div>}
        <h3 className="text-sm font-medium text-gray-400 mt-6 mb-3">
          Recent Results
        </h3>
        <div className="space-y-3">
          {displayedResults.map(result => <div key={result.id} className="flex items-center justify-between p-2 bg-gray-750 rounded-md">
              <div>
                <div className="text-sm font-medium">
                  {result.home ? 'vs ' : '@ '}
                  {result.opponent}
                </div>
                <div className="text-xs text-gray-400">
                  {result.competition}
                </div>
              </div>
              <div className="text-right">
                <div className={`text-sm font-bold ${resultColors[result.result[0] as keyof typeof resultColors]}`}>
                  {result.result}
                </div>
                <div className="text-xs text-gray-400">{result.score}</div>
              </div>
            </div>)}
        </div>
      </div>
    </div>;
};