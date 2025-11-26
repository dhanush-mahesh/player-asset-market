import { useState, useEffect } from 'react';
import axios from 'axios';

function BettingPicks({ apiUrl }) {
  const [picks, setPicks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBettingPicks();
  }, []);

  const fetchBettingPicks = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${apiUrl}/betting/picks`, {
        params: { todays_games: true }
      });
      setPicks(response.data.picks || []);
    } catch (error) {
      console.error('Error fetching betting picks:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-neutral-400">Loading betting picks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-highlight-dark rounded-lg p-6 border border-neutral-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">Sports Betting Picks</h1>
            <p className="text-neutral-400 mt-1">Real sportsbook lines for today's games</p>
          </div>
          <button 
            onClick={fetchBettingPicks}
            className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-3 rounded-xl hover:from-green-500 hover:to-emerald-500 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>

        <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <div className="font-semibold text-yellow-400 mb-1">Responsible Gambling</div>
              <p className="text-sm text-neutral-300">
                These picks are for informational purposes only. Always gamble responsibly.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold mb-4">Best Props for Today</h2>
        {picks.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {picks.map((pick) => (
              <div
                key={pick.player_id}
                className="bg-gradient-to-br from-green-900/10 to-emerald-900/10 border border-green-700 rounded-lg p-4 hover:border-green-500 transition-colors"
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-bold text-lg">{pick.player_name}</h3>
                    <p className="text-sm text-neutral-400">{pick.team} • {pick.position}</p>
                    {pick.bookmaker && (
                      <p className="text-xs text-blue-400 mt-1">{pick.bookmaker}</p>
                    )}
                  </div>
                  <span className={`text-xs px-2 py-1 rounded font-semibold ${
                    pick.confidence_level === 'HIGH' ? 'bg-green-600 text-white' :
                    pick.confidence_level === 'MEDIUM' ? 'bg-yellow-600 text-white' :
                    'bg-neutral-600 text-white'
                  }`}>
                    {pick.confidence_level}
                  </span>
                </div>

                <div className="bg-highlight-dark rounded-lg p-3 mb-3">
                  <div className="text-sm text-neutral-400 mb-1">{pick.prop_type}</div>
                  <div className="flex items-baseline gap-2 mb-2">
                    <div className="text-2xl font-bold">{pick.line}</div>
                    {pick.bookmaker && (
                      <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded font-semibold">
                        {pick.bookmaker}
                      </span>
                    )}
                  </div>
                  
                  <div className={`text-lg font-bold ${
                    pick.recommendation === 'OVER' ? 'text-green-400' :
                    pick.recommendation === 'UNDER' ? 'text-red-400' :
                    'text-neutral-400'
                  }`}>
                    {pick.recommendation}
                  </div>
                  
                  {pick.over_odds && (
                    <div className="text-xs text-neutral-400 mt-1">
                      Over: {pick.over_odds > 0 ? '+' : ''}{pick.over_odds}
                    </div>
                  )}
                </div>

                <div className="space-y-2 text-sm mb-3">
                  <div className="flex justify-between">
                    <span className="text-neutral-400">Player Avg:</span>
                    <span className="font-semibold">{pick.player_avg}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-neutral-400">Consistency:</span>
                    <div className="flex items-center gap-1">
                      <span className="font-semibold">{pick.consistency}</span>
                      {pick.consistency_explanation && (
                        <span 
                          className="text-xs text-neutral-500 cursor-help" 
                          title={pick.consistency_explanation}
                        >
                          ⓘ
                        </span>
                      )}
                      {pick.matchup_adjusted && (
                        <span className="text-xs bg-blue-600 text-white px-1.5 py-0.5 rounded font-semibold">
                          MATCHUP
                        </span>
                      )}
                    </div>
                  </div>
                  {pick.opponent && (
                    <div className="flex justify-between">
                      <span className="text-neutral-400">Opponent:</span>
                      <span className="font-semibold text-blue-400">{pick.opponent}</span>
                    </div>
                  )}
                </div>

                <div className="pt-3 border-t border-neutral-700">
                  <p className="text-xs text-neutral-400">{pick.reason}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-highlight-dark rounded-lg border border-neutral-700">
            <div className="text-6xl mb-4">🎯</div>
            <h3 className="text-xl font-bold mb-2">No Props Available</h3>
            <p className="text-neutral-400 mb-4">
              Props are usually posted closer to game time, or you may have reached your API limit.
            </p>
            <div className="text-sm text-neutral-500 max-w-md mx-auto">
              <p className="mb-2">Possible reasons:</p>
              <ul className="text-left space-y-1">
                <li>• No NBA games scheduled today</li>
                <li>• Props not posted yet (check closer to game time)</li>
                <li>• Odds API credits exhausted (500/month free tier)</li>
              </ul>
              <p className="mt-4 text-neutral-400">
                The rest of the app (AI Insights, Fantasy, etc.) works without API credits!
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default BettingPicks;
