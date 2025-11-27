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
import BettingPicks from './components/BettingPicks'
import FantasyLineup from './components/FantasyLineup'

const API_URL = 'https://nba-analytics-api-2sal.onrender.com'
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
              <NavigationDropdown 
                currentView={currentView}
                setCurrentView={setCurrentView}
                setViewingCompare={setViewingCompare}
              />
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
        ) : currentView === 'betting' ? (
          <BettingPicks
            apiUrl={API_URL}
            onPlayerClick={(id) => setSelectedPlayerId(id)}
          />
        ) : currentView === 'fantasy' ? (
          <FantasyLineup
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

// Navigation Dropdown Component
function NavigationDropdown({ currentView, setCurrentView, setViewingCompare }) {
  const [isOpen, setIsOpen] = useState(false);

  const menuItems = [
    { id: 'home', label: 'Home', icon: '' },
    { id: 'watchlist', label: 'Watchlist', icon: '⭐' },
    { id: 'live', label: 'Live Scores', icon: '' },
    { id: 'simulator', label: 'Trade Simulator', icon: '' },
    { id: 'ai', label: 'AI Insights', icon: '' },
    { id: 'betting', label: 'Betting Picks', icon: '' },
    { id: 'fantasy', label: 'Fantasy Lineup', icon: '' },
  ];

  const currentItem = menuItems.find(item => item.id === currentView) || menuItems[0];

  const handleSelect = (id) => {
    setCurrentView(id);
    setViewingCompare(false);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-500 transition-colors"
      >
        <span>{currentItem.icon}</span>
        <span>{currentItem.label}</span>
        <svg 
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-56 bg-highlight-dark border border-neutral-700 rounded-lg shadow-xl z-20">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                  currentView === item.id
                    ? 'bg-blue-600 text-white'
                    : 'text-neutral-300 hover:bg-neutral-700'
                } ${item.id === menuItems[0].id ? 'rounded-t-lg' : ''} ${
                  item.id === menuItems[menuItems.length - 1].id ? 'rounded-b-lg' : ''
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-semibold">{item.label}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default App
