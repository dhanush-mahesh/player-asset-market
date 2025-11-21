import { useState, useMemo } from 'react';
import { Search, X } from 'lucide-react';

function CompareSearch({ allPlayers, onCancel, onSelectPlayer, existingPlayerIds, replacingPlayerName }) {
  const [searchQuery, setSearchQuery] = useState('');

  // Helper function to normalize text (remove accents)
  const normalizeText = (text) => {
    return text
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase();
  };

  // Filter the list of all players
  const filteredPlayers = useMemo(() => {
    if (searchQuery === '') {
      return allPlayers;
    }
    const normalizedSearch = normalizeText(searchQuery);
    return allPlayers.filter(player => {
      const normalizedName = normalizeText(player.full_name);
      return normalizedName.includes(normalizedSearch);
    });
  }, [searchQuery, allPlayers]);

  return (
    // This is a modal overlay
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex justify-center items-start pt-20">
      <div className="bg-highlight-dark border border-highlight-light rounded-xl shadow-lg w-full max-w-md">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-highlight-light">
          <h3 className="text-lg font-semibold">Replace {replacingPlayerName}</h3>
          <button
            onClick={onCancel}
            className="text-neutral-400 hover:text-white"
          >
            <X size={20} />
          </button>
        </div>
        
        {/* Search Bar */}
        <div className="p-4">
          <div className="relative">
            <input
              type="text"
              placeholder="Search for a replacement..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full p-3 pl-10 bg-highlight-dark text-white border border-highlight-light rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500" size={18} />
          </div>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto">
          {filteredPlayers.map(player => {
            const isAlreadyInCompare = existingPlayerIds.includes(player.id);
            return (
              <div
                key={player.id}
                onClick={() => !isAlreadyInCompare && onSelectPlayer(player)}
                className={`flex items-center gap-4 p-3 mx-2 rounded-lg cursor-pointer ${
                  isAlreadyInCompare
                    ? 'opacity-30 cursor-not-allowed'
                    : 'hover:bg-highlight-light'
                }`}
              >
                <img 
                  src={player.headshot_url} 
                  alt={player.full_name}
                  className="w-10 h-10 rounded-full bg-highlight-light object-cover border-2 border-neutral-700"
                  onError={(e) => e.target.src = 'https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png'}
                />
                <div>
                  <p className="font-semibold">{player.full_name}</p>
                  <p className="text-sm text-neutral-400">{player.team_name} &middot; {player.position || 'N/A'}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default CompareSearch;