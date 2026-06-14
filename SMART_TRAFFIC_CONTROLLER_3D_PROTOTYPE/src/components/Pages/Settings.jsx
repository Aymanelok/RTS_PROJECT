export default function Settings({ traffic, theme, onThemeToggle }) {
  const { settings, controls } = traffic;

  return (
    <section className="glass-panel p-5">
      <div className="mb-5">
        <p className="panel-title">Settings</p>
        <h2 className="mt-1 text-xl font-black text-white">Simulation Parameters</h2>
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <label className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
          <span className="subtle-label">Theme</span>
          <button className="mt-3 w-full rounded-xl border border-cyan-300/20 bg-cyan-400/10 px-4 py-3 text-left font-bold text-cyan-100" onClick={onThemeToggle} type="button">
            Toggle dark/light mode: {theme}
          </button>
        </label>
        <label className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
          <span className="subtle-label">Green Duration ({settings.greenDuration}s)</span>
          <input className="mt-3 w-full accent-cyan-300" max="15" min="8" onChange={(event) => controls.updateSetting('greenDuration', event.target.value)} type="range" value={settings.greenDuration} />
          <div className="mt-3 flex gap-2">
            <button className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm font-bold text-slate-100" onClick={() => controls.updateSetting('greenDuration', settings.greenDuration - 1)} type="button">
              Decrease green
            </button>
            <button className="rounded-lg border border-cyan-300/20 bg-cyan-400/10 px-3 py-1.5 text-sm font-bold text-cyan-100" onClick={() => controls.updateSetting('greenDuration', settings.greenDuration + 1)} type="button">
              Increase green
            </button>
          </div>
        </label>
        <label className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
          <span className="subtle-label">Yellow Duration ({settings.yellowDuration}s)</span>
          <input className="mt-3 w-full accent-yellow-300" max="5" min="2" onChange={(event) => controls.updateSetting('yellowDuration', event.target.value)} type="range" value={settings.yellowDuration} />
          <div className="mt-3 flex gap-2">
            <button className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm font-bold text-slate-100" onClick={() => controls.updateSetting('yellowDuration', settings.yellowDuration - 1)} type="button">
              Decrease yellow
            </button>
            <button className="rounded-lg border border-yellow-300/20 bg-yellow-400/10 px-3 py-1.5 text-sm font-bold text-yellow-100" onClick={() => controls.updateSetting('yellowDuration', settings.yellowDuration + 1)} type="button">
              Increase yellow
            </button>
          </div>
        </label>
        <label className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
          <span className="subtle-label">Hysteresis Threshold ({settings.hysteresisThreshold} vehicles)</span>
          <input className="mt-3 w-full accent-emerald-300" max="14" min="1" onChange={(event) => controls.updateSetting('hysteresisThreshold', event.target.value)} type="range" value={settings.hysteresisThreshold} />
          <div className="mt-3 flex gap-2">
            <button className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm font-bold text-slate-100" onClick={() => controls.updateSetting('hysteresisThreshold', settings.hysteresisThreshold - 1)} type="button">
              Decrease threshold
            </button>
            <button className="rounded-lg border border-emerald-300/20 bg-emerald-400/10 px-3 py-1.5 text-sm font-bold text-emerald-100" onClick={() => controls.updateSetting('hysteresisThreshold', settings.hysteresisThreshold + 1)} type="button">
              Increase threshold
            </button>
          </div>
        </label>
        <label className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
          <span className="subtle-label">Simulation Speed ({settings.simulationSpeed}x)</span>
          <select className="mt-3 w-full rounded-xl border border-white/10 bg-slate-950 px-4 py-3 text-white" onChange={(event) => controls.setSimulationSpeed(Number(event.target.value))} value={settings.simulationSpeed}>
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={4}>4x</option>
          </select>
        </label>
        <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.035] p-4">
          <span>
            <span className="subtle-label block">Emergency Vehicle Mode</span>
            <span className="mt-1 block text-sm text-slate-300">Allow ambulance priority vehicles to spawn.</span>
          </span>
          <input checked={settings.emergencyMode} className="h-5 w-5 accent-red-400" onChange={(event) => controls.updateSetting('emergencyMode', event.target.checked)} type="checkbox" />
        </label>
      </div>
    </section>
  );
}
