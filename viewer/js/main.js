import { createScene }      from './scene.js';
import { buildMegaminx }    from './megaminx.js';
import { updateTopdownSvg } from './svg.js';
import { initControls }     from './controls.js';
import { initLibrary }      from './library.js';
import { createAnimator }   from './animator.js';

const WS_URL = 'ws://localhost:8765';

async function main() {
  const geometry = await (await fetch('/geometry.json')).json();

  const container                                 = document.getElementById('canvas-container');
  const { scene }                                 = createScene(container);
  const { group, updateColors, getMeshesForFace } = buildMegaminx(geometry);
  scene.add(group);

  const animator = createAnimator(scene, geometry, getMeshesForFace);

  let lastState              = null;
  let isPlaying              = false;
  let speed                  = 1.0;
  let playTimer              = null;
  let lastCommandWasBackward = false;

  function stepInterval() { return Math.max(120, 800 / speed); }
  function animDuration()  { return Math.min(stepInterval() * 0.75, 500); }

  function sendCmd(cmd) {
    fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cmd),
    }).catch(console.error);
  }

  function stopPlay() {
    isPlaying = false;
    ctrlApi.setPlaying(false);
    if (playTimer) { clearTimeout(playTimer); playTimer = null; }
  }

  // During auto-play the animation itself provides pacing; the 50ms here is
  // just a small buffer between animation-end and the next HTTP request.
  function scheduleNext() {
    playTimer = setTimeout(() => {
      lastCommandWasBackward = false;
      sendCmd({ type: 'step_forward' });
    }, 50);
  }

  const ctrlApi = initControls({
    onFirst: () => {
      stopPlay();
      lastCommandWasBackward = false;
      sendCmd({ type: 'goto_move', n: 0 });
    },
    onBack: () => {
      if (animator.isAnimating) return;
      stopPlay();
      lastCommandWasBackward = true;
      sendCmd({ type: 'step_backward' });
    },
    onPlay() {
      if (!lastState || lastState.totalMoves === 0) return;
      if (isPlaying) { stopPlay(); return; }
      isPlaying = true;
      ctrlApi.setPlaying(true);
      if (lastState.moveIndex >= lastState.totalMoves) {
        sendCmd({ type: 'goto_move', n: 0 });
        // scheduleNext() will fire from the goto_move state response
      } else {
        scheduleNext();
      }
    },
    onFwd: () => {
      if (animator.isAnimating) return;
      stopPlay();
      lastCommandWasBackward = false;
      sendCmd({ type: 'step_forward' });
    },
    onLast: () => {
      stopPlay();
      lastCommandWasBackward = false;
      if (lastState) sendCmd({ type: 'goto_move', n: lastState.totalMoves });
    },
    onSpeedChange: v => { speed = v; },
  });

  initLibrary({
    onLoadAlg:    name => { stopPlay(); sendCmd({ type: 'load_algorithm', name }); },
    onAnimateSeq: seq  => { stopPlay(); sendCmd({ type: 'animate_sequence', sequence: seq }); },
  });

  function onMessage(msg) {
    if (msg.type === 'state') {
      lastState = msg;
      const svgEl = document.getElementById('topdown-svg');
      if (svgEl) updateTopdownSvg(svgEl, msg, geometry);

      if (msg.currentMove && !animator.isAnimating) {
        // Tick the counter up immediately so user sees the step number change
        // as the face starts rotating rather than after it finishes.
        ctrlApi.updateProgress(msg.moveIndex, msg.totalMoves, msg.currentMove, msg.algName);
        animator.animate(msg.currentMove, animDuration(), lastCommandWasBackward, () => {
          updateColors(msg);
          if (isPlaying) {
            if (msg.moveIndex >= msg.totalMoves) stopPlay();
            else scheduleNext();
          }
        });
      } else {
        // No animation: goto_move jumps, reset, or move already animating (shouldn't happen).
        updateColors(msg);
        ctrlApi.updateProgress(msg.moveIndex, msg.totalMoves, msg.currentMove, msg.algName);
        if (isPlaying) {
          if (msg.moveIndex >= msg.totalMoves) stopPlay();
          else scheduleNext();
        }
      }
    } else if (msg.type === 'loaded') {
      stopPlay();
      ctrlApi.updateProgress(0, msg.moves.length, null, msg.algName);
    } else if (msg.type === 'reset') {
      stopPlay();
      ctrlApi.updateProgress(0, 0, null, null);
    }
  }

  function connect() {
    const ws = new WebSocket(WS_URL);
    ws.onopen    = () => console.log('Megaminx viewer connected');
    ws.onclose   = () => setTimeout(connect, 2000);
    ws.onerror   = e  => console.error('WS error', e);
    ws.onmessage = e  => onMessage(JSON.parse(e.data));
  }
  connect();
}

main().catch(console.error);
