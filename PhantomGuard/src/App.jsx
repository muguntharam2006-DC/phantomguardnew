import { useState } from "react";
import "./App.css";

const powerHistory = [
  { time: "09:00", power: 62 },
  { time: "09:15", power: 68 },
  { time: "09:30", power: 72 },
  { time: "09:45", power: 110 },
  { time: "10:00", power: 125 },
  { time: "10:15", power: 118 },
  { time: "10:30", power: 132 },
  { time: "10:45", power: 128 },
  { time: "11:00", power: 9 },
  { time: "11:15", power: 8 },
  { time: "11:30", power: 8 },
];

function App() {
  const [phantomLoad, setPhantomLoad] = useState(true);

  return (
    <div className="app">

      {/* HEADER */}
      <header className="header">
        <div className="brand">
          <div className="logo">⚡</div>

          <div>
            <h1>PhantomGuard</h1>
            <p>Smart Energy Monitoring System</p>
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot"></span>
          System Active
        </div>
      </header>

      <main className="dashboard">

        {/* TITLE */}
        <section className="page-title">
          <h2>Energy Dashboard</h2>
          <p>
            Monitor appliance usage and identify phantom energy consumption.
          </p>
        </section>

        {/* STAT CARDS */}
        <section className="stats-grid">

          <div className="stat-card">
            <div className="stat-icon teal">⚡</div>
            <div>
              <p>Voltage</p>
              <h3>230 V</h3>
              <span className="normal">● Normal</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon blue">◉</div>
            <div>
              <p>Current Power</p>
              <h3>8 W</h3>
              <span className="normal">● Monitoring</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon purple">▣</div>
            <div>
              <p>Detected Appliance</p>
              <h3>TV</h3>
              <span className="standby">● Standby</span>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon yellow">⚡</div>
            <div>
              <p>Energy Used</p>
              <h3>2.4 kWh</h3>
              <span className="normal">● Today</span>
            </div>
          </div>

        </section>

        {/* GRAPH + CURRENT LOAD */}
        <section className="main-grid">

          {/* POWER GRAPH */}
          <div className="panel graph-panel">

            <div className="panel-header">
              <div>
                <h2>Power Usage</h2>
                <p>Recent power consumption</p>
              </div>

              <div className="live-badge">
                <span></span>
                Live
              </div>
            </div>

            <div className="graph">

              <div className="y-axis">
                <span>150W</span>
                <span>100W</span>
                <span>50W</span>
                <span>0W</span>
              </div>

              <div className="graph-area">

                <div className="grid-line"></div>
                <div className="grid-line"></div>
                <div className="grid-line"></div>
                <div className="grid-line"></div>

                <svg
                  className="graph-svg"
                  viewBox="0 0 800 260"
                  preserveAspectRatio="none"
                >
                  <polyline
                    points="
                      0,150
                      70,140
                      140,132
                      210,75
                      280,45
                      350,58
                      420,30
                      490,42
                      560,230
                      650,235
                      800,235
                    "
                    fill="none"
                    stroke="#0f766e"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />

                  <polyline
                    points="
                      0,150
                      70,140
                      140,132
                      210,75
                      280,45
                      350,58
                      420,30
                      490,42
                      560,230
                      650,235
                      800,235
                    "
                    fill="none"
                    stroke="#0f766e"
                    strokeWidth="12"
                    opacity="0.08"
                  />
                </svg>

                <div className="x-axis">
                  {powerHistory.map((item) => (
                    <span key={item.time}>{item.time}</span>
                  ))}
                </div>

              </div>

            </div>

          </div>

          {/* CURRENT LOAD */}
          <div className="panel appliance-panel">

            <div className="panel-header">
              <div>
                <h2>Current Load</h2>
                <p>Detected appliance</p>
              </div>

              <span className="power-symbol">⏻</span>
            </div>

            <div className="appliance-main">

              <div className="appliance-icon">
                ▣
              </div>

              <h3>TV</h3>

              <p>Standby Mode</p>

              <div className="power-value">
                8 W
              </div>

            </div>

            <div className="appliance-info">

              <div>
                <span>Status</span>
                <strong className="warning-text">
                  Standby
                </strong>
              </div>

              <div>
                <span>Power Factor</span>
                <strong>0.65</strong>
              </div>

            </div>

          </div>

        </section>

        {/* BOTTOM */}
        <section className="bottom-grid">

          {/* PHANTOM */}
          <div className="panel phantom-panel">

            <div className="panel-header">
              <div>
                <h2>Phantom Load Detection</h2>
                <p>Standby energy monitoring</p>
              </div>

              <span className="warning-symbol">⚠</span>
            </div>

            {phantomLoad ? (
              <div className="phantom-content">

                <div className="alert-box">

                  <div className="alert-symbol">
                    ⚠
                  </div>

                  <div>
                    <strong>
                      Phantom Load Detected
                    </strong>

                    <p>
                      TV is consuming 8 W while in standby mode.
                    </p>
                  </div>

                </div>

                <div className="phantom-details">

                  <div>
                    <span>Current standby power</span>
                    <strong>8 W</strong>
                  </div>

                  <div>
                    <span>Estimated monthly wastage</span>
                    <strong>₹42</strong>
                  </div>

                </div>

                <button
                  className="cutoff-button"
                  onClick={() => setPhantomLoad(false)}
                >
                  ⏻
                  Simulate Power Cutoff
                </button>

              </div>
            ) : (
              <div className="safe-state">

                <div className="safe-icon">
                  ✓
                </div>

                <h3>No Phantom Load</h3>

                <p>
                  The detected standby load has been disconnected.
                </p>

                <button
                  className="restore-button"
                  onClick={() => setPhantomLoad(true)}
                >
                  Restore Simulation
                </button>

              </div>
            )}

          </div>

          {/* TARIFF */}
          <div className="panel tariff-panel">

            <div className="panel-header">

              <div>
                <h2>Tariff Guard</h2>
                <p>Electricity consumption estimate</p>
              </div>

              <span className="rupee-symbol">₹</span>

            </div>

            <div className="bill-display">
              <span>Estimated Bill</span>
              <h3>₹486</h3>
            </div>

            <div className="tariff-progress">

              <div className="progress-label">
                <span>Monthly Consumption</span>
                <strong>124 kWh</strong>
              </div>

              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: "62%" }}
                ></div>
              </div>

              <div className="progress-range">
                <span>0 kWh</span>
                <span>200 kWh</span>
              </div>

            </div>

            <div className="tariff-warning">
              <span>⚠</span>

              <span>
                Monitor consumption to avoid moving into a higher
                tariff slab.
              </span>
            </div>

          </div>

        </section>

      </main>

      <footer>
        PhantomGuard • Smart Energy Monitoring Prototype
      </footer>

    </div>
  );
}

export default App;