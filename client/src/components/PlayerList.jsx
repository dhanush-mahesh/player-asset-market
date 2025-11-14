import { useState, useMemo } from 'react'
import { Search, Loader2 } from 'lucide-react'
import MarketMovers from './MarketMovers'

function PlayerList({ allPlayers, featuredPlayers, loading, onPlayerClick, apiUrl }) {
  const [searchQuery, setSearchQuery] = useState("")

  const filteredPlayers = useMemo(() => {
    if (searchQuery === "") {
      return allPlayers
    }
    return allPlayers.filter(player =>
      player.full_name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [searchQuery, allPlayers])

  const displayPlayers = searchQuery === "" 
    ? featuredPlayers
    : filteredPlayers

  return (
    <div className="flex flex-col"> 
      
      <div className="text-center max-w-2xl mx-auto mb-12 mt-8">
        
        <img 
          src="/logo.png" 
          alt="Sportfolio Logo" 
          className="w-24 h-24 mx-auto mb-6 cursor-pointer"
        />

        {/* --- ⭐️ THIS IS THE NEW CREATIVE TEXT ⭐️ --- */}
        <h1 className="text-6xl font-extrabold tracking-tighter text-transparent 
                       bg-clip-text bg-gradient-to-r from-purple-400 via-blue-500 to-green-400 
                       bg-200% animate-text-shimmer mb-4">
          Sportfolio
        </h1>
        
        <p className="text-xl text-neutral-400">
          Go beyond the box score. Trade on the buzz.
        </p>
      </div>

      <MarketMovers onPlayerClick={onPlayerClick} apiUrl={apiUrl} />
      
      <div className="w-full max-w-xl relative mb-12 self-center">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="text-neutral-500" size={24} />
        </div>
        <input
          type="text"
          placeholder="Search for a player (e.g. 'LeBron')..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full p-4 pl-12 bg-highlight-dark text-white border border-highlight-light 
                     rounded-2xl text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 
                     shadow-lg shadow-brand-light/50 transition-all"
        />
      </div>

      {loading && (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="animate-spin text-neutral-500" size={48} />
        </div>
      )}

      {!loading && (
        <div className="w-full">
          <h2 className="text-2xl font-semibold mb-6 text-neutral-300 pl-1">
            {searchQuery ? `Search Results (${filteredPlayers.length})` : "Top 9 Players"}
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayPlayers.map(player => (
              <div
                key={player.player_id || player.id}
                onClick={() => onPlayerClick(player.player_id || player.id)}
                className="group bg-highlight-dark border border-highlight-light rounded-xl 
                           cursor-pointer transition-all duration-300 hover:bg-highlight-light 
                           hover:border-blue-500/50 hover:shadow-xl hover:shadow-blue-500/10 
                           transform hover:-translate-y-1 p-5 flex items-center gap-4"
              >
                <img 
                  src={player.headshot_url} 
                  alt={player.full_name}
                  className="w-16 h-16 rounded-full bg-highlight-light object-cover border-2 border-neutral-700"
                  onError={(e) => e.target.src = 'https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png'}
                />
                
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-1 group-hover:text-blue-400 transition-colors">
                    {player.full_name}
                  </h3>
                  <p className="text-neutral-400 font-medium">{player.team_name} &middot; {player.position || 'N/A'}</p>
                </div>
              </div>
            ))}
          </div>

          {searchQuery === "" && (
            <p className="text-center text-neutral-500 mt-12">
              Start typing to search {allPlayers.length} players...
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default PlayerList