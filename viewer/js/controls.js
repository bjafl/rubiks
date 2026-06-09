export function initControls({ onFirst, onBack, onPlay, onFwd, onLast, onSpeedChange }) {
  document.getElementById('btn-first').addEventListener('click', onFirst);
  document.getElementById('btn-back').addEventListener('click', onBack);
  document.getElementById('btn-play').addEventListener('click', onPlay);
  document.getElementById('btn-fwd').addEventListener('click', onFwd);
  document.getElementById('btn-last').addEventListener('click', onLast);

  const slider   = document.getElementById('speed-slider');
  const speedLbl = document.getElementById('speed-label');
  slider.addEventListener('input', () => {
    const val = (slider.value / 10).toFixed(1);
    speedLbl.textContent = `${val}×`;
    onSpeedChange(parseFloat(val));
  });

  return {
    setPlaying(playing) {
      document.getElementById('btn-play').textContent = playing ? '⏸' : '▶';
    },
    updateProgress(moveIndex, totalMoves, currentMove, algName) {
      const pct = totalMoves > 0 ? (moveIndex / totalMoves) * 100 : 0;
      document.getElementById('progress-bar-fill').style.width = `${pct}%`;
      document.getElementById('progress-label').textContent = `${moveIndex} / ${totalMoves}`;
      const parts = [algName, currentMove].filter(Boolean);
      document.getElementById('status-label').textContent = parts.join('  ') || '–';
    },
  };
}
