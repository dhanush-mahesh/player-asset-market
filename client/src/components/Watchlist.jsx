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
    <div className="space-y-8">
      {/* Header Section */}
      <div className="bg-gradient-to-br from-neutral-800/80 to-neutral-900/80 border border-neutral-700/50 rounded-2xl p-8 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-2xl flex items-center justify-center shadow-lg">
              <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-4xl font-bold text-white mb-1">
                Your Watchlist
              </h1>
              <p className="text-neutral-400 text-lg">
                Tracking {watchlist.length} player{watchlist.length !== 1 ? 's' : ''} • Updated in real-time
              </p>
            </div>
          </div>
          <button
            onClick={fetchWatchlistData}
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl hover:from-blue-500 hover:to-purple-500 flex items-center gap-2 transition-all shadow-lg hover:shadow-xl hover:scale-105"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Data
          </button>
        </div>
      </div>

      {/* Players Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {playersData.map((player) => (
          <div
            key={player.id}
            className="group relative overflow-hidden bg-gradient-to-br from-neutral-800/80 to-neutral-900/80 border border-neutral-700/50 rounded-2xl hover:border-yellow-500/50 transition-all hover:shadow-2xl hover:shadow-yellow-500/20 backdrop-blur-sm"
          >
            {/* Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/0 to-orange-500/0 group-hover:from-yellow-500/10 group-hover:to-orange-500/10 transition-all"></div>
            
            <div className="relative z-10 p-6">
              {/* Remove Button */}
              <button
                onClick={() => removeFromWatchlist(player.id)}
                className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-full bg-neutral-800/80 text-neutral-400 hover:bg-red-600 hover:text-white transition-all"
                title="Remove from watchlist"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>

              {/* Player Header */}
              <div className="flex items-start gap-4 mb-6">
                <div className="relative">
                  <img
                    src={player.headshot_url || '/default-player.png'}
                    alt={player.full_name}
                    className="w-20 h-20 rounded-full border-2 border-yellow-500/50 shadow-lg"
                    onError={(e) => { e.target.src = '/default-player.png'; }}
                  />
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center shadow-lg">
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-xl font-bold text-white mb-1 truncate">{player.full_name}</h3>
                  <p className="text-sm text-neutral-400 font-medium">{player.team_name}</p>
                  <p className="text-xs text-neutral-500 mt-1 inline-block px-2 py-0.5 bg-neutral-800 rounded-full">
                    {player.position}
                  </p>
                </div>
              </div>

              {/* Metrics Grid */}
              {player.metrics && (
                <div className="space-y-3 mb-6">
                  {/* Value Score */}
                  <div className="bg-neutral-800/50 rounded-xl p-3 border border-neutral-700/50">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-neutral-400 font-medium uppercase tracking-wide">Value Score</span>
                      <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                        {player.metrics.value_score?.toFixed(2) || 'N/A'}
                      </span>
                    </div>
                  </div>

                  {/* Momentum & Confidence */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-neutral-800/50 rounded-xl p-3 border border-neutral-700/50">
                      <div className="text-xs text-neutral-400 font-medium uppercase tracking-wide mb-1">Momentum</div>
                      <div className={`text-sm font-bold ${
                        player.metrics.momentum_score > 0.5 ? 'text-green-400' :
                        player.metrics.momentum_score > 0 ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {player.metrics.momentum_status || 'N/A'}
                      </div>
                    </div>
                    <div className="bg-neutral-800/50 rounded-xl p-3 border border-neutral-700/50">
                      <div className="text-xs text-neutral-400 font-medium uppercase tracking-wide mb-1">Confidence</div>
                      <div className="text-sm font-bold text-purple-400">
                        {player.metrics.confidence_level || 'N/A'}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* View Details Button */}
              <button
                onClick={() => onPlayerClick(player.id)}
                className="w-full bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-500 hover:to-orange-500 text-white py-3 rounded-xl transition-all text-sm font-semibold shadow-lg hover:shadow-xl hover:scale-[1.02] flex items-center justify-center gap-2"
              >
                <span>View Full Details</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Watchlist;
