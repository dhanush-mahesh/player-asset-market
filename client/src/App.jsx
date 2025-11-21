import { useState, useEffect } from 'react'
import axios from 'axios'
import PlayerList from './components/PlayerList'
import PlayerPage from './components/PlayerPage'
import ComparePage from './components/ComparePage'
import AIInsights from './components/AIInsights'
import LiveScores from './components/LiveScores'
import Watchlist from './components/Watchlist'
import TradeSimulator from './components/TradeSimulator'
import ChatBot from './components/ChatBot'

const API_URL = 'http://127.0.0.1:8000'
const COMPARE_LIMIT = 3

function App() {
  const [players, setPlayers] = useState([])
  const [featuredPlayers, setFeaturedPlayers] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedPlayerId, setSelectedPlayerId] = useState(null)
  const [currentView, setCurrentView] = useState('home')
  const [compareIds, setCompareIds] = useState([])
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

  // --- ⭐️ 2. UPDATED TOGGLE FUNCTION FOR ARRAYS ---
  const handleToggleCompare = (playerId) => {
    setCompareIds(prevIds => {
      // Check if player is already in the array
      if (prevIds.includes(playerId)) {
        // Remove them
        return prevIds.filter(id => id !== playerId);
      } else {
        // Add them if we are under the limit
        if (prevIds.length < COMPARE_LIMIT) {
          return [...prevIds, playerId];
        }
      }
      // If limit is reached, just return the old array
      return prevIds;
    })
  }

  // --- ⭐️ 3. UPDATED REPLACE FUNCTION FOR ARRAYS ---
  const handleReplacePlayer = (oldPlayerId, newPlayerId) => {
    setCompareIds(prevIds => {
      // Check if new player is already in the list
      if (prevIds.includes(newPlayerId)) {
        // Just remove the old one
        return prevIds.filter(id => id !== oldPlayerId);
      }
      
      // Swap them by mapping over the array, PRESERVING ORDER
      return prevIds.map(id => {
        if (id === oldPlayerId) {
          return newPlayerId; // This is the swap
        }
        return id;
      });
    });
  };

  const handleClearCompare = () => {
    setCompareIds([]) // Set to empty array
    setViewingCompare(false)
  }

  return (
    <div className="min-h-screen w-full">
      {/* Navigation Bar */}
      {!selectedPlayerId && (
        <nav className="bg-highlight-dark border-b border-neutral-700 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 md:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <img 
                  src="/SportfolioLogo.png" 
                  alt="Sportfolio Logo" 
                  className="h-50 w-40 object-contain cursor-pointer hover:opacity-80 transition-opacity"
                  onClick={() => {
                    setCurrentView('home');
                    setViewingCompare(false);
                  }}
                />
              </div>
              <div className="flex gap-2 items-center">
                <button
                  onClick={() => {
                    setCurrentView('home');
                    setViewingCompare(false);
                  }}
                  className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                    currentView === 'home' && !viewingCompare
                      ? 'bg-blue-600 text-white'
                      : 'text-neutral-400 hover:text-white hover:bg-neutral-700'
                  }`}
                >
                  Home
                </button>
                <button
                  onClick={() => {
                    setCurrentView('watchlist');
                    setViewingCompare(false);
                  }}
                  className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                    currentView === 'watchlist'
                      ? 'bg-blue-600 text-white'
                      : 'text-neutral-400 hover:text-white hover:bg-neutral-700'
                  }`}
                >
                  Watchlist
                </button>
                <button
                  onClick={() => {
                    setCurrentView('live');
                    setViewingCompare(false);
                  }}
                  className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                    currentView === 'live'
                      ? 'bg-blue-600 text-white'
                      : 'text-neutral-400 hover:text-white hover:bg-neutral-700'
                  }`}
                >
                  Live Scores
                </button>
                <button
                  onClick={() => {
                    setCurrentView('simulator');
                    setViewingCompare(false);
                  }}
                  className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                    currentView === 'simulator'
                      ? 'bg-blue-600 text-white'
                      : 'text-neutral-400 hover:text-white hover:bg-neutral-700'
                  }`}
                >
                  Simulator
                </button>
                <button
                  onClick={() => {
                    setCurrentView('ai');
                    setViewingCompare(false);
                  }}
                  className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
                    currentView === 'ai'
                      ? 'bg-blue-600 text-white'
                      : 'text-neutral-400 hover:text-white hover:bg-neutral-700'
                  }`}
                >
                  AI Insights
                </button>
              </div>
            </div>
          </div>
        </nav>
      )}

      <main className="max-w-7xl mx-auto p-4 md:p-8">
        {selectedPlayerId ? (
          <PlayerPage
            playerId={selectedPlayerId}
            onBackClick={() => setSelectedPlayerId(null)}
            apiUrl={API_URL}
          />
        ) : currentView === 'watchlist' ? (
          <Watchlist
            apiUrl={API_URL}
            onPlayerClick={(id) => setSelectedPlayerId(id)}
          />
        ) : currentView === 'simulator' ? (
          <TradeSimulator
            apiUrl={API_URL}
            onPlayerClick={(id) => setSelectedPlayerId(id)}
          />
        ) : currentView === 'live' ? (
          <LiveScores
            apiUrl={API_URL}
            onPlayerClick={(id) => setSelectedPlayerId(id)}
          />
        ) : currentView === 'ai' ? (
          <AIInsights
            apiUrl={API_URL}
            onPlayerClick={(id) => setSelectedPlayerId(id)}
          />
        ) : viewingCompare ? (
          <ComparePage 
            playerIds={compareIds} // Pass the array directly
            onBackClick={() => setViewingCompare(false)}
            onClear={handleClearCompare}
            apiUrl={API_URL}
            allPlayers={players}
            onReplacePlayer={handleReplacePlayer}
          />
        ) : (
          <PlayerList
            allPlayers={players}
            featuredPlayers={featuredPlayers}
            loading={loading}
            onPlayerClick={(id) => setSelectedPlayerId(id)}
            apiUrl={API_URL}
            compareIds={compareIds} // Pass the array
            onToggleCompare={handleToggleCompare}
            compareLimit={COMPARE_LIMIT}
          />
        )}
      </main>
      
      {/* Compare Bar - Only show on home page */}
      {compareIds.length > 0 && !selectedPlayerId && !viewingCompare && currentView === 'home' && (
        <div className="sticky bottom-0 left-0 w-full bg-highlight-dark border-t-2 border-blue-500 shadow-lg p-4">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <p className="text-lg font-semibold">Comparing {compareIds.length} / {COMPARE_LIMIT} players</p>
            <div>
              <button
                onClick={handleClearCompare}
                className="text-neutral-400 hover:text-white mr-4"
              >
                Clear All
              </button>
              <button
                onClick={() => setViewingCompare(true)}
                disabled={compareIds.length < 2}
                className="bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-500
                           disabled:bg-neutral-600 disabled:cursor-not-allowed"
              >
                Compare Now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ChatBot - Always visible */}
      <ChatBot apiUrl={API_URL} />
    </div>
  )
}

export default App
