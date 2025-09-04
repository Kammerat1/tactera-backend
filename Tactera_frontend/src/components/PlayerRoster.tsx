import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, FilterIcon } from 'lucide-react';
type PlayerRosterProps = {
  fullView?: boolean;
};
export const PlayerRoster = ({
  fullView = false
}: PlayerRosterProps) => {
  const [sortField, setSortField] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');
  const players = [{
    id: 1,
    name: 'Martin Ødegaard',
    position: 'AM',
    nationality: '🇳🇴',
    age: 25,
    rating: 87,
    fitness: 95,
    form: 'excellent',
    value: '€75M'
  }, {
    id: 2,
    name: 'Bukayo Saka',
    position: 'RW',
    nationality: '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    age: 22,
    rating: 86,
    fitness: 90,
    form: 'good',
    value: '€90M'
  }, {
    id: 3,
    name: 'William Saliba',
    position: 'CB',
    nationality: '🇫🇷',
    age: 23,
    rating: 85,
    fitness: 98,
    form: 'good',
    value: '€65M'
  }, {
    id: 4,
    name: 'Declan Rice',
    position: 'DM',
    nationality: '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    age: 25,
    rating: 85,
    fitness: 92,
    form: 'good',
    value: '€85M'
  }, {
    id: 5,
    name: 'Gabriel Jesus',
    position: 'ST',
    nationality: '🇧🇷',
    age: 27,
    rating: 84,
    fitness: 76,
    form: 'poor',
    value: '€55M'
  }, {
    id: 6,
    name: 'Gabriel Martinelli',
    position: 'LW',
    nationality: '🇧🇷',
    age: 23,
    rating: 83,
    fitness: 88,
    form: 'average',
    value: '€60M'
  }, {
    id: 7,
    name: 'Kai Havertz',
    position: 'CF',
    nationality: '🇩🇪',
    age: 25,
    rating: 82,
    fitness: 94,
    form: 'excellent',
    value: '€60M'
  }, {
    id: 8,
    name: 'Gabriel Magalhães',
    position: 'CB',
    nationality: '🇧🇷',
    age: 26,
    rating: 84,
    fitness: 91,
    form: 'good',
    value: '€55M'
  }];
  const formClasses = {
    excellent: 'bg-green-600',
    good: 'bg-green-500',
    average: 'bg-yellow-500',
    poor: 'bg-red-500',
    injured: 'bg-gray-500'
  };
  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };
  const displayedPlayers = fullView ? players : players.slice(0, 5);
  return <div className="bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <div className="p-4 flex justify-between items-center border-b border-gray-700">
        <h2 className="text-lg font-semibold">Squad</h2>
        {!fullView && <button className="text-sm text-blue-400 hover:text-blue-300">
            View all players
          </button>}
        {fullView && <div className="flex items-center">
            <button className="flex items-center text-sm bg-gray-700 hover:bg-gray-600 px-3 py-1.5 rounded-md mr-2">
              <FilterIcon size={14} className="mr-1" />
              Filter
            </button>
            <select className="bg-gray-700 text-sm rounded-md py-1.5 px-3 text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500">
              <option>All Positions</option>
              <option>Goalkeepers</option>
              <option>Defenders</option>
              <option>Midfielders</option>
              <option>Forwards</option>
            </select>
          </div>}
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-700">
            <tr>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer" onClick={() => toggleSort('name')}>
                <div className="flex items-center">
                  Player
                  {sortField === 'name' && (sortDirection === 'asc' ? <ChevronUpIcon size={16} /> : <ChevronDownIcon size={16} />)}
                </div>
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Pos
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Age
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer" onClick={() => toggleSort('rating')}>
                <div className="flex items-center">
                  Rating
                  {sortField === 'rating' && (sortDirection === 'asc' ? <ChevronUpIcon size={16} /> : <ChevronDownIcon size={16} />)}
                </div>
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Fitness
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Form
              </th>
              {fullView && <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Value
                </th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {displayedPlayers.map(player => <tr key={player.id} className="hover:bg-gray-750">
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="ml-2">
                      <div className="text-sm font-medium">{player.name}</div>
                      <div className="text-xs text-gray-400">
                        {player.nationality}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs rounded-md bg-gray-700">
                    {player.position}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  {player.age}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm font-semibold">{player.rating}</div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="w-16 bg-gray-600 rounded-full h-1.5">
                    <div className={`h-1.5 rounded-full ${player.fitness > 85 ? 'bg-green-500' : player.fitness > 70 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{
                  width: `${player.fitness}%`
                }}></div>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full ${formClasses[player.form as keyof typeof formClasses]}`}>
                    {player.form}
                  </span>
                </td>
                {fullView && <td className="px-4 py-3 whitespace-nowrap text-sm">
                    {player.value}
                  </td>}
              </tr>)}
          </tbody>
        </table>
      </div>
    </div>;
};