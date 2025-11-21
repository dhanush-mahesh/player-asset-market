import { useState, useMemo } from 'react'
import { Search, Loader2, Plus, Check } from 'lucide-react'
import MarketMovers from './MarketMovers'

function PlayerList({ allPlayers, featuredPlayers, loading, onPlayerClick, apiUrl, compareIds, onToggleCompare, compareLimit }) {
  const [searchQuery, setSearchQuery] = useState("")

  // Helper function to normalize text (remove accents)
  const normalizeText = (text) => {
    return text
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  };

  const filteredPlayers = useMemo(() => {
    if (!allPlayers) return [];
    if (searchQuery === "") {
      return allPlayers
    }
    const normalizedSearch = normalizeText(searchQuery);
    return allPlayers.filter(player => {
      const normalizedName = normalizeText(player.full_name);
      return normalizedName.includes(normalizedSearch);
    })
  }, [searchQuery, allPlayers])

  const displayPlayers = searchQuery === "" 
    ? featuredPlayers
    : filteredPlayers
    
  const atCompareLimit = compareIds.length >= compareLimit

  return (
    <div className="flex flex-col"> 
      
      <div className="text-center max-w-2xl mx-auto mb-8 mt-4">
        <h1 className="text-6xl font-extrabold tracking-tighter text-transparent 
                       bg-clip-text bg-gradient-to-r from-purple-400 via-blue-500 to-green-400 
                       bg-200% animate-text-shimmer mb-6">
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
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold text-neutral-300 pl-1">
              {searchQuery ? `Search Results (${filteredPlayers.length})` : "Top 9 Players"}
            </h2>
            
            {/* --- ⭐️ THIS IS THE FIX ⭐️ --- */}
            <p className="text-sm text-neutral-500">
              Select up tp 3 players to compare using the + icon {" "}
              <span className="font-semibold text-neutral-200">
                ({compareIds.length}/{compareLimit})
              </span>
            </p>

          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayPlayers && displayPlayers.map(player => {
              const isComparing = compareIds.includes(player.player_id || player.id)
              
              return (
                <div
                  key={player.player_id || player.id}
                  className="group bg-highlight-dark border border-highlight-light rounded-xl 
                             transition-all duration-300 transform 
                             p-5 flex items-start gap-4
                             hover:bg-highlight-light hover:border-blue-500/50 hover:shadow-xl 
                             hover:shadow-blue-500/10 hover:-translate-y-1"
                >
                  <img 
                    src={player.headshot_url} 
                    alt={player.full_name}
                    className="w-16 h-16 rounded-full bg-highlight-light object-cover border-2 border-neutral-700 cursor-pointer"
                    onClick={() => onPlayerClick(player.player_id || player.id)}
                    onError={(e) => e.target.src = 'https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png'}
                  />
                  
                  <div className="flex-1 cursor-pointer" onClick={() => onPlayerClick(player.player_id || player.id)}>
                    <h3 className="text-xl font-bold text-white mb-1 group-hover:text-blue-400 transition-colors">
                      {player.full_name}
                    </h3>
                    <p className="text-neutral-400 font-medium">{player.team_name} &middot; {player.position || 'N/A'}</p>
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleCompare(player.player_id || player.id);
                    }}
                    disabled={atCompareLimit && !isComparing}
                    className={`p-2 rounded-full transition-colors ${
                      isComparing 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-highlight-light text-neutral-400 hover:bg-neutral-700'
                    } disabled:opacity-30 disabled:cursor-not-allowed`}
                  >
                    {isComparing ? <Check size={16} /> : <Plus size={16} />}
                  </button>
                </div>
              )
            })}
          </div>

          {searchQuery === "" && allPlayers && (
            <p className="text-center text-neutral-500 mt-12">
              Start typing to search all {allPlayers.length} players...
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default PlayerList