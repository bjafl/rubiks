import { createScene }      from './scene.js';
import { buildMegaminx }    from './megaminx.js';
import { updateTopdownSvg } from './svg.js';
import { initControls }     from './controls.js';
import { initLibrary }      from './library.js';

const WS_URL = 'ws://localhost:8765';

async function main() {
  const geometry = await (await fetch('/geometry.json')).json();

  const container              = document.getElementById('canvas-container');
  const { scene }              = createScene(container);
  const { group, updateColors } = buildMegaminx(geometry);
  scene.add(group);

  let lastState = null;
  let isPlaying = false;
  let speed     = 1.0;
  let playTimer = null;

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

  function scheduleNext() {
    playTimer = setTimeout(() => sendCmd({ type: 'step_forward' }), Math.max(120, 800 / speed));
  }

  const ctrlApi = initControls({
    onFirst:       () => sendCmd({ type: 'goto_move', n: 0 }),
    onBack:        () => { stopPlay(); sendCmd({ type: 'step_backward' }); },
    onPlay() {
      if (!lastState || lastState.totalMoves === 0) return;
      if (isPlaying) { stopPlay(); return; }
      if (lastState.moveIndex >= lastState.totalMoves) {
        sendCmd({ type: 'goto_move', n: 0 });
      }
      isPlaying = true;
      ctrlApi.setPlaying(true);
      scheduleNext();
    },
    onFwd:         () => { stopPlay(); sendCmd({ type: 'step_forward' }); },
    onLast:        () => lastState && sendCmd({ type: 'goto_move', n: lastState.totalMoves }),
    onSpeedChange: v => { speed = v; },
  });

  initLibrary({
    onLoadAlg:    name => { stopPlay(); sendCmd({ type: 'load_algorithm', name }); },
    onAnimateSeq: seq  => { stopPlay(); sendCmd({ type: 'animate_sequence', sequence: seq }); },
  });

  function onMessage(msg) {
    if (msg.type === 'state') {
      lastState = msg;
      updateColors(msg);
      const svgEl = document.getElementById('topdown-svg');
      if (svgEl) updateTopdownSvg(svgEl, msg, geometry);
      ctrlApi.updateProgress(msg.moveIndex, msg.totalMoves, msg.currentMove, msg.algName);
      if (isPlaying) {
        if (msg.moveIndex >= msg.totalMoves) stopPlay();
        else scheduleNext();
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
