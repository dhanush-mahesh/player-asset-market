import { useState, useEffect } from 'react'
import axios from 'axios'
import PlayerList from './components/PlayerList'
import PlayerPage from './components/PlayerPage'
import ComparePage from './components/ComparePage'

const API_URL = 'http://127.0.0.1:8000'
const COMPARE_LIMIT = 2 // <-- ⭐️ 1. CHANGED LIMIT TO 2

function App() {
  const [players, setPlayers] = useState([])
  const [featuredPlayers, setFeaturedPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedPlayerId, setSelectedPlayerId] = useState(null)
  
  const [compareIds, setCompareIds] = useState(new Set())
  const [viewingCompare, setViewingCompare] = useState(false)

  useEffect(() => {
    async function fetchInitialData() {
      try {
        const [playersRes, featuredRes] = await Promise.all([
          axios.get(`${API_URL}/players`),
          axios.get(`${API_URL}/featured-players`)
        ])
        setPlayers(playersRes.data)
        setFeaturedPlayers(featuredRes.data)
      } catch (error) {
        console.error("Error fetching initial data:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchInitialData()
  }, [])

  // --- ⭐️ 2. UPDATED COMPARE FUNCTION (now checks limit of 3) ---
  const handleToggleCompare = (playerId) => {
    setCompareIds(prevIds => {
      const newIds = new Set(prevIds)
      
      if (newIds.has(playerId)) {
        newIds.delete(playerId)
      } else {
        // Only allow adding if we are under the limit
        if (newIds.size < COMPARE_LIMIT) {
          newIds.add(playerId)
        } else {
          console.log(`Compare limit of ${COMPARE_LIMIT} reached.`)
        }
      }
      return newIds
    })
  }

  const handleClearCompare = () => {
    setCompareIds(new Set())
    setViewingCompare(false)
  }

  return (
    <div className="min-h-screen w-full">
      <main className="max-w-7xl mx-auto p-4 md:p-8">
        {selectedPlayerId ? (
          <PlayerPage
            playerId={selectedPlayerId}
            onBackClick={() => setSelectedPlayerId(null)}
            apiUrl={API_URL}
          />
        ) : viewingCompare ? (
          <ComparePage 
            playerIds={Array.from(compareIds)}
            onBackClick={() => setViewingCompare(false)}
            onClear={handleClearCompare}
            apiUrl={API_URL}
          />
        ) : (
          <PlayerList
            allPlayers={players}
            featuredPlayers={featuredPlayers}
            loading={loading}
            onPlayerClick={(id) => setSelectedPlayerId(id)}
            apiUrl={API_URL}
            compareIds={compareIds}
            onToggleCompare={handleToggleCompare}
            compareLimit={COMPARE_LIMIT} // <-- ⭐️ 3. Pass the limit of 3
          />
        )}
      </main>
      
      {/* Compare Bar */}
      {compareIds.size > 0 && !selectedPlayerId && !viewingCompare && (
        <div className="sticky bottom-0 left-0 w-full bg-highlight-dark border-t-2 border-blue-500 shadow-lg p-4">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            {/* --- ⭐️ 4. UPDATED BAR TEXT --- */}
            <p className="text-lg font-semibold">Comparing {compareIds.size} / {COMPARE_LIMIT} players</p>
            <div>
              <button
                onClick={handleClearCompare}
                className="text-neutral-400 hover:text-white mr-4"
              >
                Clear All
              </button>
              <button
                onClick={() => setViewingCompare(true)}
                // --- ⭐️ 5. DISABLE BUTTON IF LESS THAN 2 PLAYERS ---
                disabled={compareIds.size < 2}
                className="bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-500
                           disabled:bg-neutral-600 disabled:cursor-not-allowed"
              >
                Compare Now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
