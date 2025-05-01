console.log("Script loaded!");


const board = document.getElementById('board');
const movePawnBtn = document.getElementById('movePawnBtn');
const placeFenceBtn = document.getElementById('placeFenceBtn');
const resetBtn = document.getElementById('resetBtn');

const API_BASE = `http://${window.location.hostname}:8000`;

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
    
    // Store exact coordinates
    fenceSlot.dataset.x = x;
    fenceSlot.dataset.y = y;
    fenceSlot.dataset.orientation = orientation;

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
            const response = await fetch(`${API_BASE}/api/game/${GAME_ID}/move/`, {
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
    if (!currentPlayer) {
        alert("Current player not set!");
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/game/${GAME_ID}/fence/`, {
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

function renderGameState(state) {

    if (state.status === 'FINISHED' && state.winner) {
        console.log("Game finished! Winner:", state.winner);
        const winnerName = state.winner === state.player1_id ? 'Player 2' : 'Player 1';
        showWinnerModal(winnerName);
    }
    document.querySelectorAll('.pawn, .fence-placed').forEach(el => el.remove());
    
    // Render players
    for (const [playerId, playerData] of Object.entries(state.players)) {
        const playerNum = playerId.replace('player', '');
        const [x, y] = playerData.position;
        const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
        if (cell) {
            const pawn = createPawn(playerNum, x, y);
            cell.appendChild(pawn);
        }
    }
    
    // Render fences with corrected positioning
    state.fences?.forEach(fence => {
        const orientation = fence.orientation.toLowerCase();
        const x = parseInt(fence.x);
        const y = parseInt(fence.y);

        const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
        if (cell) {
            const fenceElement = document.createElement('div');
            fenceElement.className = `fence-placed fence-${orientation}`;
            
            if (orientation === 'h') {
                // Horizontal fence - appears between this row and next
                fenceElement.style.cssText = `
                    position: absolute;
                    width: calc(200% + 2px);
                    height: 6px;
                    background-color: #6c757d;
                    z-index: 15;
                    top: 100%;  // Position at bottom of current cell
                    left: 0;
                    transform: translateY(-50%);
                    pointer-events: none;
                `;
            } else {
                // Vertical fence - appears between this column and next
                fenceElement.style.cssText = `
                    position: absolute;
                    height: calc(200% + 2px);
                    width: 6px;
                    background-color: #6c757d;
                    z-index: 15;
                    left: 100%;  // Position at right of current cell
                    top: 0;
                    transform: translateX(-50%);
                    pointer-events: none;
                `;
            }
            
            cell.appendChild(fenceElement);
        }
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
    
    // Visual feedback
    const pawn1 = document.querySelector('.pawn-1');
    const pawn2 = document.querySelector('.pawn-2');
    
    if (pawn1) pawn1.style.boxShadow = currentPlayer === 'player1' ? '0 0 10px 2px blue' : 'none';
    if (pawn2) pawn2.style.boxShadow = currentPlayer === 'player2' ? '0 0 10px 2px red' : 'none';
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

function showWinnerModal(winnerName) {
    console.log("Showing winner modal for:", winnerName);
    
    const modal = document.createElement('div');
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0,0,0,0.8)';
    modal.style.display = 'flex';
    modal.style.justifyContent = 'center';
    modal.style.alignItems = 'center';
    modal.style.zIndex = '1000';
    
    const content = document.createElement('div');
    content.style.backgroundColor = 'white';
    content.style.padding = '2rem';
    content.style.borderRadius = '10px';
    content.innerHTML = `
        <h2>Game Over!</h2>
        <p>${winnerName} wins!</p>
    `;
    
    modal.appendChild(content);
    document.body.appendChild(modal);

    // Disable game controls
    document.querySelectorAll('#movePawnBtn, #placeFenceBtn').forEach(btn => {
        btn.disabled = true;
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    initializeBoard();
    
    try {
        const response = await fetch(`${API_BASE}/api/game/${GAME_ID}/state/`);
        const state = await response.json();
        renderGameState(state);
    } catch (error) {
        console.error('Failed to load game state:', error);
    }
});

movePawnBtn.addEventListener('click', () => setMode('movePawn'));
placeFenceBtn.addEventListener('click', () => setMode('placeFence'));
