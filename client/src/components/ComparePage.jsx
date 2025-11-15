import { useState, useEffect } from 'react'
import axios from 'axios'
import { ArrowLeft, Loader2, X } from 'lucide-react'
import PlayerChart from './Chart'

// --- ⭐️ NEW, SAFE HELPER FUNCTION ---
const getStat = (player, statKey) => {
  try {
    if (player && player.season_stats && player.season_stats[statKey] != null) {
      return player.season_stats[statKey];
    }
  } catch (e) {
    console.error("Error getting stat:", e);
  }
  return null; // Return null for 'N/A' or errors
};

// --- ⭐️ NEW HELPER FOR RENDERING ---
// This safely renders the stat and adds the highlight
const StatCell = ({ value, isBetter, toFixed = 1 }) => {
  let displayValue = 'N/A';
  
  if (typeof value === 'number' && !isNaN(value)) {
    displayValue = value.toFixed(toFixed);
  } else if (value) {
    displayValue = value;
  }

  return (
    <td className={`p-3 text-lg font-medium text-center ${isBetter ? 'text-green-400 font-bold' : ''}`}>
      {displayValue}
    </td>
  );
};

function ComparePage({ playerIds, onBackClick, onClear, apiUrl }) {
  const [playerData, setPlayerData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    window.scrollTo(0, 0)
    
    async function fetchCompareData() {
      try {
        const response = await axios.post(`${apiUrl}/players/compare`, {
          player_ids: playerIds
        })
        setPlayerData(Object.values(response.data))
      } catch (error) {
        console.error("Error fetching compare data:", error)
      } finally {
        setLoading(false)
      }
    }
    
    if (playerIds.length === 2) { // Only fetch if we have 2 players
      fetchCompareData()
    } else {
      onBackClick() // Go back if we don't have 2
    }
  }, [playerIds, apiUrl, onBackClick])

  if (loading || !playerData || playerData.length < 2) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="animate-spin text-neutral-500" size={48} />
      </div>
    )
  }

  // --- ⭐️ NEW COMPARISON LOGIC ---
  // This code now runs safely because we know we have 2 players
  const player1 = playerData[0];
  const player2 = playerData[1];

  // Helper to compare stats (higher is better, except for TOV)
  const compareStats = (statKey, lowerIsBetter = false) => {
    const val1 = getStat(player1, statKey);
    const val2 = getStat(player2, statKey);
    
    // Convert to numbers for comparison, handling null/N/A
    const num1 = (typeof val1 === 'number') ? val1 : -9999;
    const num2 = (typeof val2 === 'number') ? val2 : -9999;
    
    let p1_isBetter = false;
    let p2_isBetter = false;
    
    if (lowerIsBetter) {
      if (num1 !== -9999 && num2 !== -9999) { // Only compare if both are valid
        p1_isBetter = num1 < num2;
        p2_isBetter = num2 < num1;
      } else if (num1 !== -9999) {
        p1_isBetter = true; // Has data while other doesn't
      } else if (num2 !== -9999) {
        p2_isBetter = true; // Has data while other doesn't
      }
    } else {
      if (num1 !== -9999 && num2 !== -9999) {
        p1_isBetter = num1 > num2;
        p2_isBetter = num2 > num1;
      } else if (num1 !== -9999) {
        p1_isBetter = true;
      } else if (num2 !== -9999) {
        p2_isBetter = true;
      }
    }

    return { val1, val2, p1_isBetter, p2_isBetter };
  };

  const statsToCompare = [
    { label: "Games Played", key: "games_played", fixed: 0 },
    { label: "MIN", key: "minutes_avg", fixed: 1 },
    { label: "PTS", key: "points_avg", fixed: 1 },
    { label: "REB", key: "rebounds_avg", fixed: 1 },
    { label: "AST", key: "assists_avg", fixed: 1 },
    { label: "STL", key: "steals_avg", fixed: 1 },
    { label: "BLK", key: "blocks_avg", fixed: 1 },
    { label: "TOV", key: "turnovers_avg", fixed: 1, lowerIsBetter: true }, // Turnovers are special
  ];


  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={onBackClick}
          className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors"
        >
          <ArrowLeft size={18} />
          Back to Player List
        </button>
        <button
          onClick={onClear}
          className="flex items-center gap-2 text-red-400 hover:text-red-300"
        >
          <X size={18} />
          Clear Comparison
        </button>
      </div>

      <h1 className="text-5xl font-bold mb-8">Player Comparison</h1>
      
      <div className="overflow-x-auto">
        <table className="w-full min-w-max">
          {/* Headshots */}
          <thead>
            <tr className="border-b-2 border-highlight-light">
              <th className="p-3 text-left w-1/3">Player</th>
              {/* This map is safe because we check playerData.length */}
              {playerData.map(player => (
                <th key={player.info.id} className="p-3 w-1/3">
                  <img 
                    src={player.info.headshot_url} 
                    alt={player.info.full_name}
                    className="w-24 h-24 rounded-full bg-highlight-light object-cover border-2 border-neutral-700 mx-auto"
                    onError={(e) => e.target.src = 'https://cdn.nba.com/headshots/nba/latest/1040x760/fallback.png'}
                  />
                  <p className="text-xl font-bold mt-2">{player.info.full_name}</p>
                  <p className="text-neutral-400">{player.info.team_name} &middot; {player.info.position}</p>
                </th>
              ))}
            </tr>
          </thead>
          
          {/* --- ⭐️ RENDER STATS MANUALLY WITH HIGHLIGHTS --- */}
          <tbody>
            {statsToCompare.map(stat => {
              const { val1, val2, p1_isBetter, p2_isBetter } = compareStats(stat.key, stat.lowerIsBetter);
              return (
                <tr className="border-b border-highlight-light" key={stat.key}>
                  <td className="p-3 text-sm font-semibold text-neutral-400">{stat.label}</td>
                  <StatCell value={val1} isBetter={p1_isBetter} toFixed={stat.fixed} />
                  <StatCell value={val2} isBetter={p2_isBetter} toFixed={stat.fixed} />
                </tr>
              );
            })}
          </tbody>
          
          {/* Value Charts */}
          <tbody>
            <tr className="border-b border-highlight-light">
              <td className="p-3 text-sm font-semibold text-neutral-400">Value Chart</td>
              {playerData.map(player => (
                <td key={player.info.id} className="p-3 h-64">
                  <PlayerChart valueHistory={player.value_history} />
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ComparePage