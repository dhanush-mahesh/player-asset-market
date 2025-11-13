import { useState, useEffect } from 'react'
import axios from 'axios'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js'

// Register the components Chart.js needs
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

// This is the base URL for your API
const API_URL = 'http://127.0.0.1:8000'

function PlayerDetail({ playerId, onBackClick }) {
  const [player, setPlayer] = useState(null)
  const [stats, setStats] = useState([])
  const [news, setNews] = useState([])
  const [valueHistory, setValueHistory] = useState([])
  const [loading, setLoading] = useState(true)

  // This hook fetches all data for the selected player
  useEffect(() => {
    async function fetchPlayerData() {
      setLoading(true)
      try {
        // 1. Get player's main info
        const infoRes = await axios.get(`${API_URL}/player/${playerId}`)
        setPlayer(infoRes.data)

        // 2. Get player's recent stats
        const statsRes = await axios.get(`${API_URL}/player/${playerId}/stats`)
        setStats(statsRes.data)
        
        // 3. Get player's news
        const newsRes = await axios.get(`${API_URL}/player/${playerId}/news`)
        setNews(newsRes.data)

        // 4. Get player's value history (this will be empty for now, which is fine)
        const valueRes = await axios.get(`${API_URL}/player/${playerId}/value_history`)
        setValueHistory(valueRes.data)

      } catch (error) {
        console.error("Error fetching player details:", error)
      } finally {
        setLoading(false)
      }
    }

    if (playerId) {
      fetchPlayerData()
    }
  }, [playerId]) // Re-run this effect if the playerId prop changes

  if (loading) {
    return <p>Loading player details...</p>
  }

  if (!player) {
    return <p>Player not found.</p>
  }

  // --- Chart Data & Options ---
  // (This is a placeholder until your player_value_index table has data)
  const chartData = {
    labels: valueHistory.length ? valueHistory.map(d => d.value_date) : ['Day 1', 'Day 2', 'Day 3'],
    datasets: [
      {
        label: 'Player Value Index',
        data: valueHistory.length ? valueHistory.map(d => d.value_score) : [50, 52, 51],
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
    ],
  }
  
  // --- Rendered Page ---
  return (
    <div style={{ padding: '20px' }}>
      <button onClick={onBackClick} style={{ marginBottom: '20px' }}>
        &larr; Back to Player List
      </button>

      {/* Player Header */}
      <h1>{player.full_name}</h1>
      <h3>{player.team_name} ({player.position})</h3>
      <hr />

      {/* Main Content Area (Chart + News) */}
      <div style={{ display: 'flex', gap: '20px' }}>
        
        {/* Left Side: "Stock Chart" */}
        <div style={{ flex: 2 }}>
          <h3>Value Index Chart</h3>
          <p>(Note: This is placeholder data until Phase 2, Stage 3 is built)</p>
          <Line data={chartData} />
        </div>

        {/* Right Side: "Market Buzz" News Feed */}
        <div style={{ flex: 1 }}>
          <h3>Market Buzz (News)</h3>
          {news.length > 0 ? (
            news.map((article, index) => (
              <div key={index} style={{ border: '1px solid #333', padding: '10px', margin: '5px' }}>
                <p>{article.headline_text}</p>
                <small>Score: {article.sentiment_score.toFixed(2)}</small>
              </div>
            ))
          ) : (
            <p>No recent news found for this player.</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default PlayerDetail