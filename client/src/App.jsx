import { useState, useEffect, lazy, Suspense } from 'react'
import axios from 'axios'
import PlayerList from './components/PlayerList'
import PlayerPage from './components/PlayerPage'

// Lazy load heavy components
const ComparePage = lazy(() => import('./components/ComparePage'))
const AIInsights = lazy(() => import('./components/AIInsights'))
const LiveScores = lazy(() => import('./components/LiveScores'))
const Watchlist = lazy(() => import('./components/Watchlist'))
const TradeSimulator = lazy(() => import('./components/TradeSimulator'))
const ChatBot = lazy(() => import('./components/ChatBot'))
const BettingPicks = lazy(() => import('./components/BettingPicks'))
const FantasyLineup = lazy(() => import('./components/FantasyLineup'))

// Loading fallback
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
      <p className="text-neutral-400">Loading...</p>
    </div>
  </div>
)

const API_URL = import.meta.env.PROD 
  ? 'https://nba-analytics-api-2sal.onrender.com'  // Production (Render subdomain)
  : 'http://localhost:8000'                         // Development
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
        <nav className="bg-gradient-to-r from-neutral-900 via-neutral-900 to-neutral-800 border-b border-neutral-700/50 sticky top-0 z-50 backdrop-blur-xl shadow-2xl">
          <div className="max-w-7xl mx-auto px-6 md:px-8">
            <div className="flex items-center justify-between h-20">
              {/* Logo */}
              <div className="flex items-center group">
                <img 
                  src="/SportfolioLogo.png" 
                  alt="Sportfolio Logo" 
                  className="h-50 w-40 object-contain cursor-pointer transition-all duration-300 group-hover:scale-105 group-hover:brightness-110"
                  onClick={() => {
                    setCurrentView('home');
                    setViewingCompare(false);
                  }}
                />
              </div>
              
              {/* Navigation Tabs */}
              <NavigationMenu 
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
          <Suspense fallback={<LoadingFallback />}>
            <Watchlist
              apiUrl={API_URL}
              onPlayerClick={(id) => setSelectedPlayerId(id)}
            />
          </Suspense>
        ) : currentView === 'simulator' ? (
          <Suspense fallback={<LoadingFallback />}>
            <TradeSimulator
              apiUrl={API_URL}
              onPlayerClick={(id) => setSelectedPlayerId(id)}
            />
          </Suspense>
        ) : currentView === 'live' ? (
          <Suspense fallback={<LoadingFallback />}>
            <LiveScores
              apiUrl={API_URL}
              onPlayerClick={(id) => setSelectedPlayerId(id)}
            />
          </Suspense>
        ) : currentView === 'ai' ? (
          <Suspense fallback={<LoadingFallback />}>
            <AIInsights
              apiUrl={API_URL}
              onPlayerClick={(id) => setSelectedPlayerId(id)}
            />
          </Suspense>
        ) : currentView === 'betting' ? (
          <Suspense fallback={<LoadingFallback />}>
            <BettingPicks
              apiUrl={API_URL}
              onPlayerClick={(id) => setSelectedPlayerId(id)}
            />
          </Suspense>
        ) : currentView === 'fantasy' ? (
          <Suspense fallback={<LoadingFallback />}>
            <FantasyLineup
              apiUrl={API_URL}
              onPlayerClick={(id) => setSelectedPlayerId(id)}
            />
          </Suspense>
        ) : viewingCompare ? (
          <Suspense fallback={<LoadingFallback />}>
            <ComparePage 
              playerIds={compareIds} // Pass the array directly
              onBackClick={() => setViewingCompare(false)}
              onClear={handleClearCompare}
              apiUrl={API_URL}
              allPlayers={players}
              onReplacePlayer={handleReplacePlayer}
            />
          </Suspense>
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

// Navigation Menu Component - Modern & Professional
function NavigationMenu({ currentView, setCurrentView, setViewingCompare }) {
  const menuItems = [
    { 
      id: 'home', 
      label: 'Home',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      )
    },
    { 
      id: 'watchlist', 
      label: 'Watchlist',
      icon: (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
        </svg>
      )
    },
    { 
      id: 'live', 
      label: 'Live',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )
    },
    { 
      id: 'simulator', 
      label: 'Simulator',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      )
    },
    { 
      id: 'ai', 
      label: 'AI Insights',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      )
    },
    { 
      id: 'betting', 
      label: 'Betting',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    { 
      id: 'fantasy', 
      label: 'Fantasy',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      )
    },
  ];

  const handleSelect = (id) => {
    setCurrentView(id);
    setViewingCompare(false);
  };

  return (
    <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
      {menuItems.map((item) => {
        const isActive = currentView === item.id;
        return (
          <button
            key={item.id}
            onClick={() => handleSelect(item.id)}
            className={`
              group relative px-4 py-2.5 rounded-xl font-semibold text-sm whitespace-nowrap
              transition-all duration-300 ease-out
              flex items-center gap-2
              ${isActive 
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/30 scale-105' 
                : 'text-neutral-400 hover:text-white hover:bg-neutral-800/50'
              }
            `}
          >
            {/* Icon */}
            <span className={`transition-transform duration-300 ${isActive ? 'scale-110' : 'group-hover:scale-110'}`}>
              {item.icon}
            </span>
            
            {/* Label */}
            <span>{item.label}</span>
            
            {/* Active indicator glow */}
            {isActive && (
              <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 opacity-20 blur-xl animate-pulse"></span>
            )}
            
            {/* Hover effect */}
            {!isActive && (
              <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-600/0 to-purple-600/0 group-hover:from-blue-600/10 group-hover:to-purple-600/10 transition-all duration-300"></span>
            )}
          </button>
        );
      })}
    </div>
  );
}

export default App
