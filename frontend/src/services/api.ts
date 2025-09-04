// API service for connecting to the FastAPI backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Generic API request function that handles common HTTP operations
 * @param endpoint - API endpoint path (e.g., '/clubs')
 * @param options - Fetch options (method, headers, body, etc.)
 * @returns Promise with the response data
 */
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
}

// Club-related API calls
export const clubApi = {
  // Get club squad with injury info
  getClubSquad: (clubId: number) => 
    apiRequest<any[]>(`/clubs/clubs/${clubId}/squad`),
  
  // Get training drills
  getTrainingDrills: () => 
    apiRequest<any[]>('/clubs/training/drills'),
  
  // Train club players
  trainClub: (clubId: number, trainingData: any) => 
    apiRequest<any>(`/clubs/${clubId}`, { 
      method: 'POST',
      body: JSON.stringify(trainingData)
    }),
};

// Stadium/Financial API calls
export const stadiumApi = {
  // Get club's financial summary
  getFinancialSummary: (clubId: number) => 
    apiRequest<any>(`/stadiums/club/${clubId}/financial-summary`),
  
  // Get stadium by club
  getStadiumByClub: (clubId: number) => 
    apiRequest<any>(`/stadiums/club/${clubId}`),
  
  // Calculate match revenue
  getMatchRevenue: (clubId: number, attendancePercentage: number = 0.8) => 
    apiRequest<any>(`/stadiums/club/${clubId}/match-revenue?attendance_percentage=${attendancePercentage}`),
};

// League-related API calls
export const leagueApi = {
  // Get league fixtures
  getFixtures: (leagueId: number) => 
    apiRequest<any[]>(`/leagues/${leagueId}/fixtures`),
  
  // Get league standings
  getStandings: (leagueId: number) => 
    apiRequest<any[]>(`/leagues/standings/${leagueId}`),
  
  // Simulate match
  simulateMatch: (fixtureId: number) => 
    apiRequest<any>(`/leagues/simulate-match/${fixtureId}`, { method: 'POST' }),
  
  // Simulate round
  simulateRound: (leagueId: number) => 
    apiRequest<any>(`/leagues/${leagueId}/simulate-round`, { method: 'POST' }),
};

// Player-related API calls  
export const playerApi = {
  // Get a specific player with injury info
  getPlayer: (playerId: number) => 
    apiRequest<any>(`/players/players/${playerId}`),
  
  // Get player stat summary
  getPlayerStats: (playerId: number) => 
    apiRequest<any>(`/players/players/${playerId}/stat-summary`),
  
  // Get current injuries
  getCurrentInjuries: () => 
    apiRequest<any[]>('/players/injuries'),
};

// Match-related API calls
export const matchApi = {
  // Get fixtures for a league
  getLeagueFixtures: (leagueId: number) => 
    apiRequest<any[]>(`/matches/league/${leagueId}/fixtures`),
  
  // Get completed matches for a league
  getLeagueResults: (leagueId: number) => 
    apiRequest<any[]>(`/matches/league/${leagueId}/results`),
};

// Authentication-related API calls
export const authApi = {
  // Login manager
  login: (email: string, password: string) => 
    apiRequest<any>('/auth/login', { 
      method: 'POST',
      body: JSON.stringify({ email, password })
    }),
  
  // Register new manager
  register: (email: string, password: string, manager_name: string) => 
    apiRequest<any>('/auth/register', { 
      method: 'POST',
      body: JSON.stringify({ email, password, manager_name })
    }),
};

// Export the main API object
export const api = {
  auth: authApi,
  club: clubApi,
  stadium: stadiumApi,
  league: leagueApi,
  player: playerApi,
  match: matchApi,
};

export default api;