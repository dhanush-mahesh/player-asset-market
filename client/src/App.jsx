import { useState, useEffect } from 'react'
import axios from 'axios'
import PlayerDetail from './PlayerDetail' // <-- Import the new component

function App() {
  const [allPlayers, setAllPlayers] = useState([])
  const [filteredPlayers, setFilteredPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedPlayerId, setSelectedPlayerId] = useState(null)

  // This useEffect hook runs once to get ALL players for the search
  useEffect(() => {
    async function fetchPlayers() {
      try {
        const response = await axios.get('http://127.0.0.1:8000/players')
        setAllPlayers(response.data)
        setFilteredPlayers(response.data) // Initially, show all players
      } catch (error) {
        console.error("Error fetching players:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchPlayers()
  }, [])

  // This useEffect hook runs every time the search query changes
  useEffect(() => {
    if (searchQuery === "") {
      setFilteredPlayers(allPlayers)
    } else {
      const filtered = allPlayers.filter(player =>
        player.full_name.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredPlayers(filtered)
    }
  }, [searchQuery, allPlayers])

  // --- Render Logic ---

  // If a player is selected, show the PlayerDetail component
  if (selectedPlayerId) {
    return (
      <PlayerDetail 
        playerId={selectedPlayerId} 
        onBackClick={() => setSelectedPlayerId(null)} // Pass a function to go back
      />
    )
  }

  // Otherwise, show the main search list
  return (
    <div style={{ padding: '20px' }}>
      <h1>Player Asset Market</h1>
      <hr />
      
      {loading && <p>Loading players...</p>}

      <div>
        <h2>All Players ({filteredPlayers.length})</h2>
        
        {/* This is your "Searchbar.js" component from your plan */}
        <input
          type="text"
          placeholder="Search for a player..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ width: '100%', padding: '10px', fontSize: '16px', marginBottom: '10px' }}
        />
        
        {/* This is the list of players */}
        <div style={{ height: '600px', overflowY: 'scroll', border: '1px solid #333' }}>
          {filteredPlayers.map(player => (
            <div 
              key={player.id} 
              style={{ borderBottom: '1px solid #222', padding: '10px', cursor: 'pointer' }}
              onClick={() => setSelectedPlayerId(player.id)} // <-- Set the selected player on click
            >
              <p style={{ margin: 0 }}><strong>{player.full_name}</strong> ({player.position || 'N/A'})</p>
              <small>{player.team_name}</small>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default App
