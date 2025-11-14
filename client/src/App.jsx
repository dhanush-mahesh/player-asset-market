import { useState, useEffect } from 'react'
import axios from 'axios'
import PlayerList from './components/PlayerList'
import PlayerPage from './components/PlayerPage'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [players, setPlayers] = useState([])
  const [featuredPlayers, setFeaturedPlayers] = useState([]) // <-- NEW STATE
  const [loading, setLoading] = useState(true)
  const [selectedPlayerId, setSelectedPlayerId] = useState(null)

  // Fetch all players AND featured players on load
  useEffect(() => {
    async function fetchInitialData() {
      try {
        // Fetch both endpoints at the same time
        const [playersRes, featuredRes] = await Promise.all([
          axios.get(`${API_URL}/players`),
          axios.get(`${API_URL}/featured-players`)
        ])
        
        setPlayers(playersRes.data)
        setFeaturedPlayers(featuredRes.data) // <-- SET NEW STATE

      } catch (error) {
        console.error("Error fetching initial data:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchInitialData()
  }, [])

  return (
    <div className="min-h-screen w-full">
      <main className="max-w-7xl mx-auto p-4 md:p-8">
        {selectedPlayerId ? (
          <PlayerPage
            playerId={selectedPlayerId}
            onBackClick={() => setSelectedPlayerId(null)}
            apiUrl={API_URL}
          />
        ) : (
          <PlayerList
            allPlayers={players} // Renamed prop for clarity
            featuredPlayers={featuredPlayers} // <-- PASS NEW PROP
            loading={loading}
            onPlayerClick={(id) => setSelectedPlayerId(id)}
            apiUrl={API_URL}
          />
        )}
      </main>
    </div>
  )
}

export default App
