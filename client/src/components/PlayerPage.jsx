import { useState, useEffect } from 'react'
import axios from 'axios'
import { ArrowLeft, Loader2, Newspaper, TrendingUp, BarChartHorizontal, CheckSquare } from 'lucide-react'
import PlayerChart from './Chart'
import StatCard from './StatCard'
// --- ⭐️ REMOVED UpcomingSchedule import ---

function PlayerPage({ playerId, onBackClick, apiUrl }) {
  const [player, setPlayer] = useState(null)
  const [stats, setStats] = useState([])
  const [news, setNews] = useState([])
  const [valueHistory, setValueHistory] = useState([])
  const [seasonStats, setSeasonStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    window.scrollTo(0, 0)
    
    async function fetchPlayerData() {
      setLoading(true)
      try {
        // --- ⭐️ THIS IS THE FIX ⭐️ ---
        // The list of variables now matches the list of API calls.
        const [infoRes, statsRes, newsRes, valueRes, seasonStatsRes] = await Promise.all([
          axios.get(`${apiUrl}/player/${playerId}`),
          axios.get(`${apiUrl}/player/${playerId}/stats`),
          axios.get(`${apiUrl}/player/${playerId}/news`),
          axios.get(`${apiUrl}/player/${playerId}/value_history`),
          axios.get(`${apiUrl}/player/${playerId}/season_stats`)
        ])
        
        setPlayer(infoRes.data)
        setStats(statsRes.data)
        setNews(newsRes.data)
        setValueHistory(valueRes.data)
        setSeasonStats(seasonStatsRes.data)

      } catch (error) {
        console.error("Error fetching player details:", error)
      } finally {
        setLoading(false)
      }
    }

    if (playerId) {
      fetchPlayerData()
    }
  }, [playerId, apiUrl])

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="animate-spin text-neutral-500" size={48} />
      </div>
    )
  }

  if (!player) {
    return <p>Player not found.</p>
  }

  const latestValue = valueHistory.length > 0 ? valueHistory[valueHistory.length - 1]?.value_score : null;

  return (
    <div>
      {/* ... (Header is unchanged) ... */}
      <div className="flex justify-between items-center mb-6">
        <img 
          src="/logo.png" 
          alt="Sportfolio Logo" 
          className="w-12 h-12 cursor-pointer" 
          onClick={onBackClick}
        />
        <button
          onClick={onBackClick}
          className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={18} />
          Back to Player List
        </button>
      </div>
      <div className="flex justify-between items-center mb-8">
         <div>
          <h1 className="text-5xl font-bold">{player.full_name}</h1>
          <p className="text-2xl text-neutral-400">{player.team_name} &middot; {player.position || 'N/A'}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-neutral-500">Current Value</p>
          <p className="text-5xl font-bold text-green-400">
            {latestValue ? latestValue.toFixed(2) : 'N/A'}
          </p>
        </div>
      </div>


      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          
          <div className="bg-highlight-dark border border-highlight-light rounded-lg p-6">
             <h2 className="flex items-center gap-2 text-2xl font-semibold mb-4">
              <TrendingUp size={24} />
              Value Index Chart
            </h2>
            <div className="h-96">
              <PlayerChart valueHistory={valueHistory} />
            </div>
          </div>
          
          <div className="bg-highlight-dark border border-highlight-light rounded-lg p-6">
            <h2 className="flex items-center gap-2 text-2xl font-semibold mb-4">
              <BarChartHorizontal size={24} />
              Most Recent Game
            </h2>
            {stats.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <StatCard label="Points" value={stats[0].points} />
                <StatCard label="Rebounds" value={stats[0].rebounds} />
                <StatCard label="Assists" value={stats[0].assists} />
                <StatCard label="Steals" value={stats[0].steals} />
                <StatCard label="Blocks" value={stats[0].blocks} />
                <StatCard label="TOVs" value={stats[0].turnovers} />
              </div>
            ) : (
              <p className="text-neutral-400">No recent game stats found.</p>
            )}
          </div>
          
          <div className="bg-highlight-dark border border-highlight-light rounded-lg p-6">
            <h2 className="flex items-center gap-2 text-2xl font-semibold mb-4">
              <CheckSquare size={24} />
              Season Averages (Per Game)
            </h2>
            {seasonStats ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-highlight-light">
                      <th className="p-2 text-neutral-400">Season</th>
                      <th className="p-2 text-neutral-400">GP</th>
                      <th className="p-2 text-neutral-400">MIN</th>
                      <th className="p-2 text-neutral-400">PTS</th>
                      <th className="p-2 text-neutral-400">REB</th>
                      <th className="p-2 text-neutral-400">AST</th>
                      <th className="p-2 text-neutral-400">STL</th>
                      <th className="p-2 text-neutral-400">BLK</th>
                      <th className="p-2 text-neutral-400">TOV</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="font-medium">
                      <td className="p-2">{seasonStats.season}</td>
                      <td className="p-2">{seasonStats.games_played}</td>
                      <td className="p-2">{seasonStats.minutes_avg.toFixed(1)}</td>
                      <td className="p-2">{seasonStats.points_avg.toFixed(1)}</td>
                      <td className="p-2">{seasonStats.rebounds_avg.toFixed(1)}</td>
                      <td className="p-2">{seasonStats.assists_avg.toFixed(1)}</td>
                      <td className="p-2">{seasonStats.steals_avg.toFixed(1)}</td>
                      <td className="p-2">{seasonStats.blocks_avg.toFixed(1)}</td>
                      <td className="p-2">{seasonStats.turnovers_avg.toFixed(1)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-neutral-400">No season stats found for this player yet.</p>
            )}
          </div>
          
        </div>

        <div className="lg:col-span-1 space-y-6">
           <div className="bg-highlight-dark border border-highlight-light rounded-lg p-6">
            <h2 className="flex items-center gap-2 text-2xl font-semibold mb-4">
              <Newspaper size={24} />
              Market Buzz
            </h2>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {news.length > 0 ? (
                news.map((article, index) => (
                  <div key={index} className="border-b border-highlight-light pb-4 last:border-b-0">
                    <p className="font-medium">{article.headline_text}</p>
                    <p className={`text-sm ${article.sentiment_score > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      Sentiment Score: {article.sentiment_score.toFixed(2)}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-neutral-400">No recent news found.</p>
              )}
            </div>
          </div>
          
          {/* --- ⭐️ REMOVED BROKEN SCHEDULE COMPONENT --- */}
        </div>
      </div>
    </div>
  )
}

export default PlayerPage