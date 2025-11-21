import { useState, useEffect } from 'react';
import axios from 'axios';

function TradeSimulator({ apiUrl, onPlayerClick }) {
  const [allPlayers, setAllPlayers] = useState([]);
  const [portfolio, setPortfolio] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredPlayers, setFilteredPlayers] = useState([]);
  const [portfolioAnalysis, setPortfolioAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPlayers();
    loadPortfolio();
  }, []);

  // Helper function to normalize text (remove accents)
  const normalizeText = (text) => {
    return text
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  };

  useEffect(() => {
    if (searchTerm) {
      const normalizedSearch = normalizeText(searchTerm);
      const filtered = allPlayers.filter(player => {
        const normalizedName = normalizeText(player.full_name);
        const normalizedTeam = normalizeText(player.team_name);
        return normalizedName.includes(normalizedSearch) || normalizedTeam.includes(normalizedSearch);
      });
      setFilteredPlayers(filtered.slice(0, 10));
    } else {
      setFilteredPlayers([]);
    }
  }, [searchTerm, allPlayers]);

  useEffect(() => {
    if (portfolio.length > 0) {
      analyzePortfolio();
    }
  }, [portfolio]);

  const fetchPlayers = async () => {
    try {
      const response = await axios.get(`${apiUrl}/players`);
      setAllPlayers(response.data);
    } catch (error) {
      console.error('Error fetching players:', error);
    }
  };

  const loadPortfolio = () => {
    const saved = localStorage.getItem('portfolio');
    if (saved) {
      setPortfolio(JSON.parse(saved));
    }
  };

  const savePortfolio = (newPortfolio) => {
    setPortfolio(newPortfolio);
    localStorage.setItem('portfolio', JSON.stringify(newPortfolio));
  };

  const addToPortfolio = (player) => {
    if (!portfolio.find(p => p.id === player.id)) {
      savePortfolio([...portfolio, { ...player, shares: 1 }]);
      setSearchTerm('');
    }
  };

  const removeFromPortfolio = (playerId) => {
    savePortfolio(portfolio.filter(p => p.id !== playerId));
  };

  const updateShares = (playerId, shares) => {
    savePortfolio(portfolio.map(p => 
      p.id === playerId ? { ...p, shares: Math.max(1, shares) } : p
    ));
  };

  const analyzePortfolio = async () => {
    if (portfolio.length === 0) return;
    
    setLoading(true);
    try {
      const playerIds = portfolio.map(p => p.id);
      const response = await axios.post(`${apiUrl}/ai/portfolio-analysis`, {
        player_ids: playerIds
      });
      setPortfolioAnalysis(response.data);
    } catch (error) {
      console.error('Error analyzing portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearPortfolio = () => {
    savePortfolio([]);
    setPortfolioAnalysis(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 via-blue-400 to-purple-400 bg-clip-text text-transparent mb-2">
            📊 Trade Simulator
          </h1>
          <p className="text-neutral-400">Build and analyze your portfolio</p>
        </div>
        {portfolio.length > 0 && (
          <button
            onClick={clearPortfolio}
            className="text-red-400 hover:text-red-300 transition-colors"
          >
            Clear Portfolio
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Add Players Section */}
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-neutral-800/50 to-neutral-900/50 border border-neutral-700/50 rounded-2xl p-6 backdrop-blur-sm">
            <h2 className="text-2xl font-bold mb-4">Add Players</h2>
            
            {/* Search */}
            <div className="relative mb-4">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search players..."
                className="w-full bg-neutral-800 border border-neutral-700 rounded-xl px-4 py-3 text-white placeholder-neutral-500 focus:outline-none focus:border-blue-500"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white"
                >
                  ×
                </button>
              )}
            </div>

            {/* Search Results */}
            {filteredPlayers.length > 0 && (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredPlayers.map(player => (
                  <div
                    key={player.id}
                    className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg hover:bg-neutral-700/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <img
                        src={player.headshot_url || '/default-player.png'}
                        alt={player.full_name}
                        className="w-10 h-10 rounded-full"
                        onError={(e) => { e.target.src = '/default-player.png'; }}
                      />
                      <div>
                        <div className="font-semibold">{player.full_name}</div>
                        <div className="text-xs text-neutral-400">{player.team_name}</div>
                      </div>
                    </div>
                    <button
                      onClick={() => addToPortfolio(player)}
                      disabled={portfolio.find(p => p.id === player.id)}
                      className="bg-blue-600 hover:bg-blue-500 disabled:bg-neutral-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm transition-colors"
                    >
                      {portfolio.find(p => p.id === player.id) ? 'Added' : 'Add'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Portfolio Section */}
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-neutral-800/50 to-neutral-900/50 border border-neutral-700/50 rounded-2xl p-6 backdrop-blur-sm">
            <h2 className="text-2xl font-bold mb-4">Your Portfolio ({portfolio.length})</h2>
            
            {portfolio.length === 0 ? (
              <div className="text-center py-8 text-neutral-400">
                <div className="text-4xl mb-2">📈</div>
                <p>Add players to start building your portfolio</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {portfolio.map(player => (
                  <div
                    key={player.id}
                    className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <img
                        src={player.headshot_url || '/default-player.png'}
                        alt={player.full_name}
                        className="w-10 h-10 rounded-full cursor-pointer hover:opacity-80"
                        onClick={() => onPlayerClick(player.id)}
                        onError={(e) => { e.target.src = '/default-player.png'; }}
                      />
                      <div className="flex-1">
                        <div className="font-semibold">{player.full_name}</div>
                        <div className="text-xs text-neutral-400">{player.team_name}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        min="1"
                        value={player.shares}
                        onChange={(e) => updateShares(player.id, parseInt(e.target.value))}
                        className="w-16 bg-neutral-700 border border-neutral-600 rounded px-2 py-1 text-center text-sm"
                      />
                      <button
                        onClick={() => removeFromPortfolio(player.id)}
                        className="text-red-400 hover:text-red-300 transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Portfolio Analysis */}
      {portfolioAnalysis && (
        <div className="bg-gradient-to-br from-blue-600/10 via-purple-600/10 to-pink-600/10 rounded-2xl p-8 border border-blue-500/20 backdrop-blur-sm">
          <h2 className="text-3xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Portfolio Analysis
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-neutral-800/50 rounded-xl p-6 border border-neutral-700/50">
              <div className="text-sm text-neutral-400 mb-2">Portfolio Risk</div>
              <div className={`text-3xl font-bold ${
                portfolioAnalysis.risk_level === 'High' ? 'text-red-400' :
                portfolioAnalysis.risk_level === 'Medium' ? 'text-yellow-400' :
                'text-green-400'
              }`}>
                {portfolioAnalysis.risk_level}
              </div>
              <div className="text-xs text-neutral-500 mt-1">
                Score: {portfolioAnalysis.risk_score}
              </div>
            </div>

            <div className="bg-neutral-800/50 rounded-xl p-6 border border-neutral-700/50">
              <div className="text-sm text-neutral-400 mb-2">Avg Value Score</div>
              <div className="text-3xl font-bold text-blue-400">
                {portfolioAnalysis.avg_value_score?.toFixed(2)}
              </div>
              <div className="text-xs text-neutral-500 mt-1">
                Trend: {portfolioAnalysis.avg_trend?.toFixed(1)}%
              </div>
            </div>

            <div className="bg-neutral-800/50 rounded-xl p-6 border border-neutral-700/50">
              <div className="text-sm text-neutral-400 mb-2">Diversification</div>
              <div className="text-3xl font-bold text-purple-400">
                {portfolioAnalysis.diversification_score?.toFixed(1)}%
              </div>
              <div className="text-xs text-neutral-500 mt-1">
                {portfolioAnalysis.high_risk_players}H / {portfolioAnalysis.medium_risk_players}M / {portfolioAnalysis.low_risk_players}L
              </div>
            </div>
          </div>

          {/* Individual Player Risk */}
          {portfolioAnalysis.players && portfolioAnalysis.players.length > 0 && (
            <div className="mb-6">
              <h3 className="text-xl font-bold mb-3">Player Risk Breakdown</h3>
              <div className="space-y-2">
                {portfolioAnalysis.players.map((player, i) => (
                  <div key={i} className="bg-neutral-800/50 rounded-lg p-3 border border-neutral-700/50 flex justify-between items-center">
                    <div>
                      <span className="font-semibold">{player.player_name}</span>
                      <span className="text-xs text-neutral-400 ml-2">
                        Value: {player.value_score?.toFixed(1)} | Trend: {player.trend?.toFixed(1)}%
                      </span>
                    </div>
                    <span className={`text-sm font-bold px-3 py-1 rounded-full ${
                      player.individual_risk === 'High' ? 'bg-red-900/50 text-red-300' :
                      player.individual_risk === 'Medium' ? 'bg-yellow-900/50 text-yellow-300' :
                      'bg-green-900/50 text-green-300'
                    }`}>
                      {player.individual_risk} Risk
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {portfolioAnalysis.recommendations && portfolioAnalysis.recommendations.length > 0 && (
            <div className="mt-6">
              <h3 className="text-xl font-bold mb-3">Recommendations</h3>
              <div className="space-y-2">
                {portfolioAnalysis.recommendations.map((rec, i) => (
                  <div key={i} className="bg-neutral-800/50 rounded-lg p-4 border border-neutral-700/50">
                    <p className="text-neutral-300">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default TradeSimulator;
