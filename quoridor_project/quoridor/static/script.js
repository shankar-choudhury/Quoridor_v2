const board = document.getElementById('board');
const movePawnBtn = document.getElementById('movePawnBtn');
const placeFenceBtn = document.getElementById('placeFenceBtn');
const resetBtn = document.getElementById('resetBtn');

let currentMode = 'movePawn'; // 'movePawn' or 'placeFence'
let selectedPawn = null;

function initializeBoard() {
    board.innerHTML = '';

    for (let y = 0; y < 9; y++) {
        for (let x = 0; x < 9; x++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.x = x;
            cell.dataset.y = y;

            if (x === 4 && y === 8) {
                const pawn = createPawn('1', x, y);
                cell.appendChild(pawn);
            } else if (x === 4 && y === 0) {
                const pawn = createPawn('2', x, y);
                cell.appendChild(pawn);
            }

            cell.addEventListener('click', () => handleCellClick(x, y));
            board.appendChild(cell);

            // Fence slots
            if (x < 8) {
                const hFence = document.createElement('div');
                hFence.classList.add('fence-slot', 'fence-slot-horizontal');
                hFence.dataset.x = x;
                hFence.dataset.y = y;
                hFence.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (currentMode === 'placeFence') {
                        placeFence('horizontal', x, y);
                    }
                });
                cell.appendChild(hFence);
            }

            if (y < 8) {
                const vFence = document.createElement('div');
                vFence.classList.add('fence-slot', 'fence-slot-vertical');
                vFence.dataset.x = x;
                vFence.dataset.y = y;
                vFence.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (currentMode === 'placeFence') {
                        placeFence('vertical', x, y);
                    }
                });
                cell.appendChild(vFence);
            }
        }
    }
}

function createPawn(playerNumber, x, y) {
    const pawn = document.createElement('div');
    pawn.className = `pawn pawn-${playerNumber}`;
    pawn.dataset.player = playerNumber;
    pawn.dataset.x = x;
    pawn.dataset.y = y;
    return pawn;
}

function handleCellClick(x, y) {
    if (currentMode !== 'movePawn') return;

    const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
    const pawn = cell.querySelector('.pawn');

    if (pawn) {
        if (selectedPawn) {
            selectedPawn.element.classList.remove('selected');
        }
        selectedPawn = { element: pawn, x, y };
        pawn.classList.add('selected');
    } else if (selectedPawn) {
        selectedPawn.element.classList.remove('selected');
        cell.appendChild(selectedPawn.element);

        selectedPawn.element.dataset.x = x;
        selectedPawn.element.dataset.y = y;

        selectedPawn = null;
    }
}

function placeFence(orientation, x, y) {
    const fenceId = `fence-${orientation}-${x}-${y}`;
    if (document.getElementById(fenceId)) return; // prevent duplicate

    const cell = document.querySelector(`.cell[data-x="${x}"][data-y="${y}"]`);
    if (!cell) return;

    const fence = document.createElement('div');
    fence.classList.add('fence-line', `fence-${orientation}`);
    fence.id = fenceId;
    cell.appendChild(fence);
}

// Mode toggle
function setMode(mode) {
    currentMode = mode;

    movePawnBtn.classList.toggle('active-mode', mode === 'movePawn');
    placeFenceBtn.classList.toggle('active-mode', mode === 'placeFence');

    if (selectedPawn) {
        selectedPawn.element.classList.remove('selected');
        selectedPawn = null;
    }
}

movePawnBtn.addEventListener('click', () => setMode('movePawn'));
placeFenceBtn.addEventListener('click', () => setMode('placeFence'));
resetBtn.addEventListener('click', () => {
    if (confirm('Reset the board to initial state?')) {
        initializeBoard();
        setMode('movePawn');
    }
});

initializeBoard();
