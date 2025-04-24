console.log("Script loaded!");


const board = document.getElementById('board');
const movePawnBtn = document.getElementById('movePawnBtn');
const placeFenceBtn = document.getElementById('placeFenceBtn');
const resetBtn = document.getElementById('resetBtn');

let currentMode = 'movePawn';
let selectedPawn = null;
let currentPlayer = 'player1'; 

function initializeBoard() {
    board.innerHTML = '';

    for (let y = 0; y < 9; y++) {
        for (let x = 0; x < 9; x++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.x = x;
            cell.dataset.y = y;
            
            if (x < 8) addFenceSlot(cell, x, y, 'horizontal');
            if (y < 8) addFenceSlot(cell, x, y, 'vertical');
            
            cell.addEventListener('click', () => handleCellClick(x, y));
            board.appendChild(cell);
        }
    }

    for (let y = 0; y < 9; y++) {
        for (let x = 0; x < 9; x++) {
            const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
            const coordLabel = document.createElement('div');
            coordLabel.textContent = `${x},${y}`;
            coordLabel.style.position = 'absolute';
            coordLabel.style.fontSize = '8px';
            coordLabel.style.color = 'rgba(0,0,0,0.5)';
            cell.appendChild(coordLabel);
        }
    }
    
}

function addFenceSlot(cell, x, y, orientation) {
    const fenceSlot = document.createElement('div');
    fenceSlot.classList.add('fence-slot', `fence-slot-${orientation}`);
    fenceSlot.dataset.x = x;
    fenceSlot.dataset.y = y;
    fenceSlot.dataset.orientation = orientation;

    fenceSlot.title = `FenceSlot: ${x},${y} ${orientation}`;
    
    fenceSlot.addEventListener('click', (e) => {
        e.stopPropagation();
        if (currentMode === 'placeFence') {
            placeFence(orientation, x, y);
        }
    });
    
    cell.appendChild(fenceSlot);
}

function createPawn(playerNumber, x, y) {
    const pawn = document.createElement('div');
    pawn.className = `pawn pawn-${playerNumber}`;
    pawn.dataset.player = playerNumber;
    pawn.dataset.x = x;
    pawn.dataset.y = y;
    return pawn;
}

async function handleCellClick(x, y) {
    if (currentMode !== 'movePawn') return;

    const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
    const pawn = cell.querySelector('.pawn');

    if (pawn) {
        if (`player${pawn.dataset.player}` !== currentPlayer) {
            alert("It's not your turn!");
            return;
        }
        
        if (selectedPawn) {
            selectedPawn.element.classList.remove('selected');
        }
        selectedPawn = { element: pawn, x, y };
        pawn.classList.add('selected');
    } 

    else if (selectedPawn) {
        try {
            const response = await fetch(`/api/game/${GAME_ID}/move/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    player_id: `player${selectedPawn.element.dataset.player}`,
                    x: x,
                    y: y
                })
            });
            
            const result = await response.json();
            if (result.success) {
                renderGameState(result.state);
            } else {
                alert(`Move failed: ${result.error || 'Invalid move'}`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to make move');
        } finally {
            if (selectedPawn) {
                selectedPawn.element.classList.remove('selected');
                selectedPawn = null;
            }
        }
    }
}

async function placeFence(orientation, x, y) {
    if (`player${selectedPawn?.element?.dataset.player}` !== currentPlayer) {
        alert(`It's ${currentPlayer}'s turn!`);
        return;
    }
    try {
        const response = await fetch(`/api/game/${GAME_ID}/fence/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player_id: currentPlayer,
                x: x,
                y: y,
                orientation: orientation.charAt(0).toUpperCase()
            })
        });
        
        const result = await response.json();
        if (result.success) {
            renderGameState(result.state);
        } else {
            alert(`Fence placement failed: ${result.error || 'Invalid placement'}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to place fence');
    }
}

console.log("Function definition reached");
function renderGameState(state) {
    console.log("Rendering game state. Fences to render:", state.fences);
    document.querySelectorAll('.pawn, .fence-placed').forEach(el => el.remove());
    
    for (const [playerId, playerData] of Object.entries(state.players)) {
        const playerNum = playerId.replace('player', '');
        const [x, y] = playerData.position;
        const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
        if (cell) {
            const pawn = createPawn(playerNum, x, y);
            cell.appendChild(pawn);
        }
    }
    
    state.fences.forEach(fence => {
        const orientation = fence.orientation.toLowerCase(); 
        const x = parseInt(fence.x);
        const y = parseInt(fence.y);

        console.log(`Attempting to render fence at ${x},${y} (${orientation})`);

        const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
        if (!cell) {
            console.error(`Cell not found at ${x},${y}`);
            return;
        }
    
        // Remove any existing fence in this position
        const existingFence = cell.querySelector(`.fence-placed.fence-${orientation}`);
        if (existingFence) existingFence.remove();
    
        // Create new fence element
        const fenceElement = document.createElement('div');
        fenceElement.className = `fence-placed fence-${orientation}`;
        
        // Add debug information
        fenceElement.dataset.debug = `fence-${x}-${y}-${orientation}`;
        fenceElement.style.backgroundColor = '#ff0000'; // TEMPORARY: Bright red for visibility
        
        cell.appendChild(fenceElement);
        console.log("Fence element created:", fenceElement);
    });

    currentPlayer = state.current_player;
    updatePlayerUI();
}

function updatePlayerUI() {
    console.log(`Current player: ${currentPlayer}`);
    
    // Update indicators
    document.querySelectorAll('.player-indicator').forEach(el => {
        el.classList.toggle('active', el.dataset.player === currentPlayer);
    });
    
    // Enable buttons for current player
    const isCurrentPlayersTurn = true; // Let backend validate
    movePawnBtn.disabled = false;
    placeFenceBtn.disabled = false;
    
    // Visual feedback
    if (currentPlayer === 'player1') {
        document.querySelector('.pawn-1').style.boxShadow = '0 0 10px 2px blue';
        document.querySelector('.pawn-2').style.boxShadow = 'none';
    } else {
        document.querySelector('.pawn-2').style.boxShadow = '0 0 10px 2px red';
        document.querySelector('.pawn-1').style.boxShadow = 'none';
    }
}

function setMode(mode) {
    currentMode = mode;
    movePawnBtn.classList.toggle('active-mode', mode === 'movePawn');
    placeFenceBtn.classList.toggle('active-mode', mode === 'placeFence');
    
    if (selectedPawn) {
        selectedPawn.element.classList.remove('selected');
        selectedPawn = null;
    }
}

async function resetGame() {
    if (confirm('Reset the game to initial state?')) {
        try {
            const response = await fetch(`/api/game/${GAME_ID}/reset/`, {
                method: 'POST'
            });
            const result = await response.json();
            if (result.success) {
                renderGameState(result.state);
                setMode('movePawn');
            }
        } catch (error) {
            console.error('Error resetting game:', error);
        }
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    initializeBoard();
    
    try {
        const response = await fetch(`/api/game/${GAME_ID}/state/`);
        const state = await response.json();
        renderGameState(state);
    } catch (error) {
        console.error('Failed to load game state:', error);
    }
});

movePawnBtn.addEventListener('click', () => setMode('movePawn'));
placeFenceBtn.addEventListener('click', () => setMode('placeFence'));
resetBtn.addEventListener('click', resetGame);