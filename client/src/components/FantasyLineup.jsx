import { useState, useEffect } from 'react';
import axios from 'axios';

function FantasyLineup({ apiUrl, onPlayerClick }) {
  const [lineup, setLineup] = useState([]);
  const [valuePicks, setValuePicks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('optimal');

  useEffect(() => {
    fetchLineupData();
  }, []);

  const fetchLineupData = async () => {
    try {
      setLoading(true);
      const [lineupRes, valueRes] = await Promise.all([
        axios.get(`${apiUrl}/fantasy/lineup`),
        axios.get(`${apiUrl}/fantasy/value-picks`)
      ]);
      
      setLineup(lineupRes.data.lineup || []);
      setValuePicks(valueRes.data.value_picks || []);
    } catch (error) {
      console.error('Error fetching fantasy data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-neutral-400">Loading fantasy lineup...</p>
        </div>
      </div>
    );
  }

  const totalProjectedPoints = lineup.slice(0, 8).reduce((sum, p) => sum + p.projected_fantasy_points, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-highlight-dark rounded-lg p-6 border border-neutral-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              🏀 Fantasy Basketball Optimizer
            </h1>
            <p className="text-neutral-400 mt-1">
              Optimized lineups based on projected performance
            </p>
          </div>
          <button 
            onClick={fetchLineupData}
            className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-xl hover:from-purple-500 hover:to-pink-500 flex items-center gap-2 transition-all shadow-lg hover:shadow-xl hover:scale-105"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Lineup
          </button>
        </div>

        {/* Lineup Summary */}
        {lineup.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-4">
              <div className="text-purple-400 text-sm font-semibold mb-1">TOTAL PROJECTED</div>
              <div className="text-3xl font-bold">{totalProjectedPoints.toFixed(1)}</div>
              <div className="text-sm text-neutral-400 mt-1">Fantasy Points (Top 8)</div>
            </div>

            <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
              <div className="text-blue-400 text-sm font-semibold mb-1">OPTIMAL PICKS</div>
              <div className="text-3xl font-bold">{lineup.length}</div>
              <div className="text-sm text-neutral-400 mt-1">Players Available</div>
            </div>

            <div className="bg-green-900/20 border border-green-700 rounded-lg p-4">
              <div className="text-green-400 text-sm font-semibold mb-1">VALUE PLAYS</div>
              <div className="text-3xl font-bold">{valuePicks.length}</div>
              <div className="text-sm text-neutral-400 mt-1">Sleeper Picks</div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-neutral-700">
        <button
          onClick={() => setActiveTab('optimal')}
          className={`px-4 py-2 font-semibold ${
            activeTab === 'optimal'
              ? 'text-purple-500 border-b-2 border-purple-500'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          🏆 Optimal Lineup ({lineup.length})
        </button>
        <button
          onClick={() => setActiveTab('value')}
          className={`px-4 py-2 font-semibold ${
            activeTab === 'value'
              ? 'text-purple-500 border-b-2 border-purple-500'
              : 'text-neutral-400 hover:text-white'
          }`}
        >
          💎 Value Picks ({valuePicks.length})
        </button>
      </div>

      {/* Content */}
      {activeTab === 'optimal' && (
        <div>
          {lineup.length > 0 ? (
            <div className="space-y-4">
              <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4 mb-4">
                <h3 className="font-semibold mb-2">📋 How to Use</h3>
                <p className="text-sm text-neutral-300">
                  Players are ranked by projected fantasy points (standard scoring: 1pt = 1, reb = 1.2, ast = 1.5, stl/blk = 3, to = -1).
                  Projections factor in recent performance and momentum trends.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {lineup.map((player, idx) => (
                  <FantasyPlayerCard
                    key={player.player_id}
                    player={player}
                    rank={idx + 1}
                    onClick={() => onPlayerClick(player.player_id)}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 bg-highlight-dark rounded-lg border border-neutral-700">
              <div className="text-6xl mb-4">🏀</div>
              <h3 className="text-xl font-bold mb-2">No Lineup Data</h3>
              <p className="text-neutral-400">
                Unable to generate lineup. Check back later.
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'value' && (
        <div>
          {valuePicks.length > 0 ? (
            <div className="space-y-4">
              <div className="bg-green-900/20 border border-green-700 rounded-lg p-4 mb-4">
                <h3 className="font-semibold mb-2">💎 Value Picks Explained</h3>
                <p className="text-sm text-neutral-300">
                  These are "sleeper" picks - players with solid projected points but lower ownership/value scores.
                  Great for tournaments where you need differentiation from the field.
                </p>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {valuePicks.map((player, idx) => (
                  <FantasyPlayerCard
                    key={player.player_id}
                    player={player}
                    rank={idx + 1}
                    isValue={true}
                    onClick={() => onPlayerClick(player.player_id)}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 bg-highlight-dark rounded-lg border border-neutral-700">
              <div className="text-6xl mb-4">💎</div>
              <h3 className="text-xl font-bold mb-2">No Value Picks</h3>
              <p className="text-neutral-400">
                No value plays identified at this time.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FantasyPlayerCard({ player, rank, isValue = false, onClick }) {
  const borderColor = rank <= 3 && !isValue ? 'border-yellow-500' : isValue ? 'border-green-700' : 'border-neutral-700';
  const bgColor = rank <= 3 && !isValue ? 'bg-yellow-900/10' : isValue ? 'bg-green-900/10' : 'bg-highlight-dark';

  return (
    <div
      onClick={onClick}
      className={`${bgColor} border ${borderColor} rounded-lg p-4 cursor-pointer hover:border-purple-500 transition-all hover:scale-[1.02]`}
    >
      <div className="flex items-start gap-4">
        {/* Rank */}
        <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center font-bold text-xl ${
          rank === 1 ? 'bg-yellow-500 text-black' :
          rank === 2 ? 'bg-gray-400 text-black' :
          rank === 3 ? 'bg-orange-600 text-white' :
          'bg-neutral-700 text-neutral-300'
        }`}>
          {rank}
        </div>

        {/* Player Info */}
        <div className="flex-1">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h3 className="font-bold text-lg">{player.player_name}</h3>
              <p className="text-sm text-neutral-400">{player.team} • {player.position}</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-purple-400">
                {player.projected_fantasy_points}
              </div>
              <div className="text-xs text-neutral-400">Projected FP</div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-5 gap-3 mb-3">
            <div className="bg-neutral-800 rounded p-2">
              <div className="text-xs text-neutral-400">PTS</div>
              <div className="font-semibold">{player.recent_stats.points}</div>
            </div>
            <div className="bg-neutral-800 rounded p-2">
              <div className="text-xs text-neutral-400">REB</div>
              <div className="font-semibold">{player.recent_stats.rebounds}</div>
            </div>
            <div className="bg-neutral-800 rounded p-2">
              <div className="text-xs text-neutral-400">AST</div>
              <div className="font-semibold">{player.recent_stats.assists}</div>
            </div>
            <div className="bg-neutral-800 rounded p-2">
              <div className="text-xs text-neutral-400">Avg FP</div>
              <div className="font-semibold">{player.avg_fantasy_points}</div>
            </div>
            <div className="bg-neutral-800 rounded p-2">
              <div className="text-xs text-neutral-400">Consistency</div>
              <div className="font-semibold">{player.consistency_score}</div>
            </div>
          </div>

          {/* Metrics */}
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-neutral-400">Momentum:</span>
              <div className="flex items-center gap-1">
                <div className="w-16 bg-neutral-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                    style={{ width: `${Math.min(player.momentum * 100, 100)}%` }}
                  />
                </div>
                <span className="text-purple-400 font-semibold">
                  {(player.momentum * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            
            {isValue && (
              <div className="flex items-center gap-2">
                <span className="text-neutral-400">Value Score:</span>
                <span className="text-green-400 font-semibold">{player.value_score.toFixed(1)}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default FantasyLineup;
