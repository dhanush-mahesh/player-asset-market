import { useState, useEffect } from 'react';
import axios from 'axios';

function Watchlist({ apiUrl, onPlayerClick }) {
  const [watchlist, setWatchlist] = useState([]);
  const [playersData, setPlayersData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load watchlist from localStorage
    const saved = localStorage.getItem('watchlist');
    if (saved) {
      setWatchlist(JSON.parse(saved));
    }
  }, []);

  useEffect(() => {
    if (watchlist.length > 0) {
      fetchWatchlistData();
    } else {
      setLoading(false);
    }
  }, [watchlist]);

  const fetchWatchlistData = async () => {
    try {
      setLoading(true);
      const promises = watchlist.map(id => 
        Promise.all([
          axios.get(`${apiUrl}/player/${id}`),
          axios.get(`${apiUrl}/player/${id}/enhanced_metrics`)
        ])
      );
      
      const results = await Promise.all(promises);
      const data = results.map(([playerRes, metricsRes]) => ({
        ...playerRes.data,
        metrics: metricsRes.data
      }));
      
      setPlayersData(data);
    } catch (error) {
      console.error('Error fetching watchlist data:', error);
    } finally {
      setLoading(false);
    }
  };

  const removeFromWatchlist = (playerId) => {
    const updated = watchlist.filter(id => id !== playerId);
    setWatchlist(updated);
    localStorage.setItem('watchlist', JSON.stringify(updated));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-neutral-400">Loading watchlist...</p>
        </div>
      </div>
    );
  }

  if (watchlist.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">⭐</div>
        <h2 className="text-2xl font-bold mb-2">Your Watchlist is Empty</h2>
        <p className="text-neutral-400">Add players to your watchlist to track their performance!</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-yellow-400 via-orange-400 to-red-400 bg-clip-text text-transparent mb-2">
            ⭐ Your Watchlist
          </h1>
          <p className="text-neutral-400">Tracking {watchlist.length} player{watchlist.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={fetchWatchlistData}
          className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-blue-500 hover:to-purple-500 flex items-center gap-2 transition-all shadow-lg hover:shadow-xl hover:scale-105"
        >
          <span>🔄</span> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {playersData.map((player) => (
          <div
            key={player.id}
            className="group relative overflow-hidden bg-gradient-to-br from-neutral-800/50 to-neutral-900/50 border border-neutral-700/50 rounded-2xl p-6 hover:border-yellow-500/50 transition-all hover:shadow-xl hover:shadow-yellow-500/10 backdrop-blur-sm"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/0 to-orange-500/0 group-hover:from-yellow-500/5 group-hover:to-orange-500/5 transition-all"></div>
            
            <div className="relative z-10">
              {/* Remove Button */}
              <button
                onClick={() => removeFromWatchlist(player.id)}
                className="absolute top-0 right-0 text-neutral-400 hover:text-red-400 transition-colors"
                title="Remove from watchlist"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>

              {/* Player Info */}
              <div className="flex items-start gap-4 mb-4">
                <img
                  src={player.headshot_url || '/default-player.png'}
                  alt={player.full_name}
                  className="w-20 h-20 rounded-full border-2 border-yellow-500/50"
                  onError={(e) => { e.target.src = '/default-player.png'; }}
                />
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-1">{player.full_name}</h3>
                  <p className="text-sm text-neutral-400">{player.team_name}</p>
                  <p className="text-xs text-neutral-500">{player.position}</p>
                </div>
              </div>

              {/* Metrics */}
              {player.metrics && (
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-neutral-400">Value Score</span>
                    <span className="text-lg font-bold text-blue-400">
                      {player.metrics.value_score?.toFixed(2) || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-neutral-400">Momentum</span>
                    <span className={`text-sm font-semibold ${
                      player.metrics.momentum_score > 0.5 ? 'text-green-400' :
                      player.metrics.momentum_score > 0 ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {player.metrics.momentum_status || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-neutral-400">Confidence</span>
                    <span className="text-sm font-semibold text-purple-400">
                      {player.metrics.confidence_level || 'N/A'}
                    </span>
                  </div>
                </div>
              )}

              {/* View Details Button */}
              <button
                onClick={() => onPlayerClick(player.id)}
                className="w-full bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-500 hover:to-orange-500 text-white py-3 rounded-xl transition-all text-sm font-semibold shadow-lg hover:shadow-xl hover:scale-105"
              >
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Watchlist;
