import { useState, useEffect } from 'react';
import axios from 'axios';

function LiveScores({ apiUrl }) {
  const [scores, setScores] = useState(null);
  const [topPerformers, setTopPerformers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedGame, setSelectedGame] = useState(null);
  const [boxScore, setBoxScore] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchScores();
    fetchTopPerformers();
    
    // Auto-refresh every 30 seconds for live games
    const interval = setInterval(() => {
      fetchScores(true); // Silent refresh
      if (selectedGame) {
        fetchBoxScore(selectedGame);
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchScores = async (silent = false) => {
    if (!silent) setRefreshing(true);
    try {
      const response = await axios.get(`${apiUrl}/live/scores`);
      setScores(response.data);
      setLastUpdated(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching live scores:', error);
      setLoading(false);
    } finally {
      if (!silent) setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    fetchScores();
    fetchTopPerformers();
  };

  const fetchTopPerformers = async () => {
    try {
      const response = await axios.get(`${apiUrl}/live/top-performers`);
      setTopPerformers(response.data.performers);
    } catch (error) {
      console.error('Error fetching top performers:', error);
    }
  };

  const fetchBoxScore = async (gameId) => {
    try {
      const response = await axios.get(`${apiUrl}/live/game/${gameId}`);
      setBoxScore(response.data);
      setSelectedGame(gameId);
    } catch (error) {
      console.error('Error fetching box score:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-neutral-400">Loading live scores...</p>
        </div>
      </div>
    );
  }

  if (!scores || scores.games_count === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🏀</div>
        <h2 className="text-2xl font-bold mb-2">No Games Today</h2>
        <p className="text-neutral-400">Check back on game days for live scores!</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-blue-600/10 via-purple-600/10 to-pink-600/10 rounded-2xl p-8 border border-blue-500/20 backdrop-blur-sm">
        <div className="absolute inset-0 bg-grid-white/[0.02] pointer-events-none"></div>
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-2 flex items-center gap-3">
                <svg className="w-10 h-10 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                  <path d="M12 2 L12 22 M2 12 L22 12 M5 5 L19 19 M19 5 L5 19" stroke="currentColor" strokeWidth="0.5"/>
                </svg>
                Live Scores
              </h1>
              <p className="text-neutral-300 text-lg">
                {new Date(scores.date).toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <button 
                onClick={handleRefresh}
                disabled={refreshing}
                className="group bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-blue-500 hover:to-purple-500 flex items-center gap-2 transition-all shadow-lg hover:shadow-xl hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                <svg 
                  className={`w-5 h-5 ${refreshing ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span className="font-semibold">{refreshing ? 'Refreshing...' : 'Refresh'}</span>
              </button>
              {lastUpdated && (
                <span className="text-xs text-neutral-500">
                  Updated {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="group relative overflow-hidden bg-gradient-to-br from-red-500/20 to-red-600/20 border border-red-500/30 rounded-xl p-5 hover:border-red-400/50 transition-all hover:scale-105">
              <div className="absolute top-0 right-0 w-20 h-20 bg-red-500/10 rounded-full blur-2xl"></div>
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">🔴</span>
                  <div className="text-red-300 text-sm font-bold tracking-wider">LIVE NOW</div>
                </div>
                <div className="text-4xl font-bold text-white">{scores.live_games.length}</div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-gradient-to-br from-green-500/20 to-green-600/20 border border-green-500/30 rounded-xl p-5 hover:border-green-400/50 transition-all hover:scale-105">
              <div className="absolute top-0 right-0 w-20 h-20 bg-green-500/10 rounded-full blur-2xl"></div>
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">✅</span>
                  <div className="text-green-300 text-sm font-bold tracking-wider">COMPLETED</div>
                </div>
                <div className="text-4xl font-bold text-white">{scores.completed_games.length}</div>
              </div>
            </div>

            <div className="group relative overflow-hidden bg-gradient-to-br from-blue-500/20 to-blue-600/20 border border-blue-500/30 rounded-xl p-5 hover:border-blue-400/50 transition-all hover:scale-105">
              <div className="absolute top-0 right-0 w-20 h-20 bg-blue-500/10 rounded-full blur-2xl"></div>
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">⏰</span>
                  <div className="text-blue-300 text-sm font-bold tracking-wider">UPCOMING</div>
                </div>
                <div className="text-4xl font-bold text-white">{scores.upcoming_games.length}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Games */}
      {scores.live_games.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <span className="animate-pulse text-3xl">🔴</span>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-red-400 to-red-600 bg-clip-text text-transparent">
              Live Games
            </h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {scores.live_games.map((game) => (
              <GameCard 
                key={game.game_id} 
                game={game} 
                onViewDetails={() => fetchBoxScore(game.game_id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Completed Games */}
      {scores.completed_games.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">✅</span>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-green-600 bg-clip-text text-transparent">
              Final Scores
            </h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {scores.completed_games.map((game) => (
              <GameCard 
                key={game.game_id} 
                game={game}
                onViewDetails={() => fetchBoxScore(game.game_id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Upcoming Games */}
      {scores.upcoming_games.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl"></span>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
              Upcoming Games
            </h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {scores.upcoming_games.map((game) => (
              <GameCard key={game.game_id} game={game} />
            ))}
          </div>
        </div>
      )}

      {/* Top Performers */}
      {topPerformers.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">🌟</span>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-yellow-400 to-orange-600 bg-clip-text text-transparent">
              Top Performers Today
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topPerformers.slice(0, 6).map((player, index) => (
              <PerformerCard key={index} player={player} rank={index + 1} />
            ))}
          </div>
        </div>
      )}

      {/* Box Score Modal */}
      {boxScore && (
        <BoxScoreModal 
          boxScore={boxScore} 
          onClose={() => {
            setBoxScore(null);
            setSelectedGame(null);
          }}
        />
      )}
    </div>
  );
}

function GameCard({ game, onViewDetails }) {
  const awayWinning = game.away_team.score > game.home_team.score;
  const homeWinning = game.home_team.score > game.away_team.score;

  // NBA team logo URL helper
  const getTeamLogoUrl = (teamTricode) => {
    return `https://cdn.nba.com/logos/nba/${game.away_team.team_id}/primary/L/logo.svg`;
  };

  return (
    <div className="group relative overflow-hidden bg-gradient-to-br from-neutral-800/50 to-neutral-900/50 border border-neutral-700/50 rounded-2xl p-6 hover:border-blue-500/50 transition-all hover:shadow-xl hover:shadow-blue-500/10 backdrop-blur-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 to-purple-500/0 group-hover:from-blue-500/5 group-hover:to-purple-500/5 transition-all"></div>
      
      <div className="relative z-10">
        {/* Status Badge */}
        <div className="flex justify-between items-center mb-4">
          <span className={`text-xs font-bold px-3 py-1.5 rounded-full ${
            game.is_live ? 'bg-gradient-to-r from-red-600 to-red-500 text-white animate-pulse shadow-lg shadow-red-500/50' :
            game.is_final ? 'bg-gradient-to-r from-green-600 to-green-500 text-white shadow-lg shadow-green-500/50' :
            'bg-gradient-to-r from-neutral-600 to-neutral-500 text-white'
          }`}>
            {game.is_live ? `Q${game.period} - ${game.game_clock}` :
             game.is_final ? 'FINAL' :
             game.game_status_text}
          </span>
        </div>

        {/* Away Team */}
        <div className={`flex items-center justify-between mb-3 p-4 rounded-xl transition-all ${
          awayWinning ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30' : 'bg-neutral-800/30'
        }`}>
          <div className="flex items-center gap-3 flex-1">
            <img
              src={`https://cdn.nba.com/logos/nba/${game.away_team.team_id}/primary/L/logo.svg`}
              alt={game.away_team.team_tricode}
              className="w-12 h-12 object-contain"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            <div>
              <div className="flex items-center gap-2">
                <div className={`text-lg font-bold ${awayWinning ? 'text-blue-300' : 'text-white'}`}>
                  {game.away_team.team_tricode}
                </div>
                <span className="text-xs text-neutral-500 font-medium">AWAY</span>
              </div>
              <div className="text-xs text-neutral-400 font-medium">
                {game.away_team.wins}-{game.away_team.losses}
              </div>
            </div>
          </div>
          <div className={`text-3xl font-bold ${awayWinning ? 'text-blue-400' : 'text-neutral-300'}`}>
            {game.away_team.score}
          </div>
        </div>

        {/* @ Symbol */}
        <div className="flex items-center justify-center my-2">
          <div className="text-sm text-neutral-500 font-bold">@</div>
        </div>

        {/* Home Team */}
        <div className={`flex items-center justify-between mb-4 p-4 rounded-xl transition-all ${
          homeWinning ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30' : 'bg-neutral-800/30'
        }`}>
          <div className="flex items-center gap-3 flex-1">
            <img
              src={`https://cdn.nba.com/logos/nba/${game.home_team.team_id}/primary/L/logo.svg`}
              alt={game.home_team.team_tricode}
              className="w-12 h-12 object-contain"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            <div>
              <div className="flex items-center gap-2">
                <div className={`text-lg font-bold ${homeWinning ? 'text-blue-300' : 'text-white'}`}>
                  {game.home_team.team_tricode}
                </div>
                <span className="text-xs text-neutral-500 font-medium">HOME</span>
              </div>
              <div className="text-xs text-neutral-400 font-medium">
                {game.home_team.wins}-{game.home_team.losses}
              </div>
            </div>
          </div>
          <div className={`text-3xl font-bold ${homeWinning ? 'text-blue-400' : 'text-neutral-300'}`}>
            {game.home_team.score}
          </div>
        </div>

        {/* View Details Button */}
        {(game.is_live || game.is_final) && onViewDetails && (
          <button
            onClick={onViewDetails}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white py-3 rounded-xl transition-all text-sm font-semibold shadow-lg hover:shadow-xl hover:scale-105 flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            View Box Score
          </button>
        )}
      </div>
    </div>
  );
}

function PerformerCard({ player, rank }) {
  const getRankColor = (rank) => {
    if (rank === 1) return 'from-yellow-400 to-yellow-600';
    if (rank === 2) return 'from-gray-300 to-gray-500';
    if (rank === 3) return 'from-orange-400 to-orange-600';
    return 'from-blue-400 to-purple-600';
  };

  return (
    <div className="group relative overflow-hidden bg-gradient-to-br from-neutral-800/50 to-neutral-900/50 border border-neutral-700/50 rounded-2xl p-5 hover:border-purple-500/50 transition-all hover:shadow-xl hover:shadow-purple-500/10 backdrop-blur-sm">
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/0 to-pink-500/0 group-hover:from-purple-500/5 group-hover:to-pink-500/5 transition-all"></div>
      
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className={`inline-block text-2xl font-black bg-gradient-to-r ${getRankColor(rank)} bg-clip-text text-transparent mb-1`}>
              #{rank}
            </div>
            <div className="font-bold text-lg text-white mb-1">{player.name}</div>
            <div className="text-sm text-neutral-400 font-medium">{player.team} vs {player.opponent}</div>
          </div>
          <span className={`text-xs px-3 py-1 rounded-full font-bold ${
            player.game_status === 'LIVE' 
              ? 'bg-gradient-to-r from-red-600 to-red-500 text-white animate-pulse shadow-lg shadow-red-500/50' 
              : 'bg-gradient-to-r from-green-600 to-green-500 text-white shadow-lg shadow-green-500/50'
          }`}>
            {player.game_status}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-3 mt-4">
          <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-xl p-3 text-center border border-blue-500/30">
            <div className="text-3xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              {player.points}
            </div>
            <div className="text-xs text-neutral-400 font-bold mt-1">PTS</div>
          </div>
          <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 rounded-xl p-3 text-center border border-green-500/30">
            <div className="text-3xl font-black text-green-400">{player.rebounds}</div>
            <div className="text-xs text-neutral-400 font-bold mt-1">REB</div>
          </div>
          <div className="bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-xl p-3 text-center border border-orange-500/30">
            <div className="text-3xl font-black text-orange-400">{player.assists}</div>
            <div className="text-xs text-neutral-400 font-bold mt-1">AST</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function BoxScoreModal({ boxScore, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-highlight-dark border border-neutral-700 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-highlight-dark border-b border-neutral-700 p-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold">📊 Box Score</h2>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        <div className="p-4 space-y-6">
          {/* Away Team */}
          <div>
            <h3 className="text-xl font-bold mb-3">Away Team</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-neutral-800">
                  <tr>
                    <th className="text-left p-2">Player</th>
                    <th className="p-2">MIN</th>
                    <th className="p-2">PTS</th>
                    <th className="p-2">REB</th>
                    <th className="p-2">AST</th>
                    <th className="p-2">FG</th>
                    <th className="p-2">3PT</th>
                    <th className="p-2">+/-</th>
                  </tr>
                </thead>
                <tbody>
                  {boxScore.away_players.map((player, i) => (
                    <tr key={i} className="border-b border-neutral-700">
                      <td className="p-2 font-semibold">{player.name}</td>
                      <td className="p-2 text-center">{player.minutes}</td>
                      <td className="p-2 text-center font-bold">{player.points}</td>
                      <td className="p-2 text-center">{player.rebounds}</td>
                      <td className="p-2 text-center">{player.assists}</td>
                      <td className="p-2 text-center text-xs">{player.fg_made}/{player.fg_attempted}</td>
                      <td className="p-2 text-center text-xs">{player.three_made}/{player.three_attempted}</td>
                      <td className={`p-2 text-center ${player.plus_minus > 0 ? 'text-green-400' : player.plus_minus < 0 ? 'text-red-400' : ''}`}>
                        {player.plus_minus > 0 ? '+' : ''}{player.plus_minus}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Home Team */}
          <div>
            <h3 className="text-xl font-bold mb-3">Home Team</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-neutral-800">
                  <tr>
                    <th className="text-left p-2">Player</th>
                    <th className="p-2">MIN</th>
                    <th className="p-2">PTS</th>
                    <th className="p-2">REB</th>
                    <th className="p-2">AST</th>
                    <th className="p-2">FG</th>
                    <th className="p-2">3PT</th>
                    <th className="p-2">+/-</th>
                  </tr>
                </thead>
                <tbody>
                  {boxScore.home_players.map((player, i) => (
                    <tr key={i} className="border-b border-neutral-700">
                      <td className="p-2 font-semibold">{player.name}</td>
                      <td className="p-2 text-center">{player.minutes}</td>
                      <td className="p-2 text-center font-bold">{player.points}</td>
                      <td className="p-2 text-center">{player.rebounds}</td>
                      <td className="p-2 text-center">{player.assists}</td>
                      <td className="p-2 text-center text-xs">{player.fg_made}/{player.fg_attempted}</td>
                      <td className="p-2 text-center text-xs">{player.three_made}/{player.three_attempted}</td>
                      <td className={`p-2 text-center ${player.plus_minus > 0 ? 'text-green-400' : player.plus_minus < 0 ? 'text-red-400' : ''}`}>
                        {player.plus_minus > 0 ? '+' : ''}{player.plus_minus}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LiveScores;
