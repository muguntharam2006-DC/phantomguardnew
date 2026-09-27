import { useEffect, useMemo, useState } from "react";
import "./App.css";

const initialPowerHistory = [
  60, 85, 72, 110, 95, 130, 118, 145, 125, 160, 140,
];

const initialLimits = [
  {
    id: 1,
    type: "Room",
    name: "Bedroom",
    current: 420,
    limit: 500,
    enabled: true,
    autoOff: false,
    status: "ON",
  },
  {
    id: 2,
    type: "Room",
    name: "Living Room",
    current: 680,
    limit: 800,
    enabled: true,
    autoOff: false,
    status: "ON",
  },
  {
    id: 3,
    type: "Device",
    name: "TV",
    current: 8,
    limit: 150,
    enabled: true,
    autoOff: true,
    status: "STANDBY",
    standbyMinutes: 26,
    standbyLimit: 30,
  },
];

function App() {
  const [powerHistory, setPowerHistory] =
    useState(initialPowerHistory);

  const [limits, setLimits] =
    useState(initialLimits);

  const [showLimitForm, setShowLimitForm] =
    useState(false);

  const [assistantDismissed, setAssistantDismissed] =
    useState(false);

  const [assistantMessage, setAssistantMessage] =
    useState(null);

  const [phantomLoad, setPhantomLoad] =
    useState(true);

  const [newLimit, setNewLimit] = useState({
    type: "Device",
    name: "",
    limit: "",
  });

  /* =====================================================
     CURRENT DEVICE
  ===================================================== */

  const monitoredDevice = useMemo(() => {
    return (
      limits.find(
        (item) =>
          item.type === "Device" &&
          item.name === "TV"
      ) ||
      limits.find(
        (item) => item.type === "Device"
      ) ||
      null
    );
  }, [limits]);

  const currentPower = monitoredDevice
    ? monitoredDevice.current
    : 0;

  const currentStatus = monitoredDevice
    ? monitoredDevice.status
    : "OFF";

  const detectedAppliance =
    monitoredDevice
      ? monitoredDevice.name
      : "None";

  /* =====================================================
     TARIFF
  ===================================================== */

  const tariffPerKwh = 6;

  const currentEnergyPerHour =
    currentPower / 1000;

  const estimatedMonthlyEnergy =
    currentEnergyPerHour * 24 * 30;

  const estimatedMonthlyCost =
    estimatedMonthlyEnergy * tariffPerKwh;

  const phantomPower =
    currentStatus === "STANDBY"
      ? currentPower
      : 0;

  const phantomMonthlyEnergy =
    (phantomPower * 24 * 30) / 1000;

  const phantomMonthlyCost =
    phantomMonthlyEnergy * tariffPerKwh;

  const potentialMonthlySavings =
    currentStatus === "STANDBY"
      ? phantomMonthlyCost
      : 0;

  const energyUsed =
    Math.max(
      0.1,
      currentPower / 1000
    ).toFixed(1);

  /* =====================================================
     DYNAMIC POWER GRAPH
  ===================================================== */

  useEffect(() => {
    const interval = setInterval(() => {
      setPowerHistory((previous) => {
        let nextValue = currentPower;

        if (currentStatus === "ON") {
          const variation =
            Math.floor(Math.random() * 21) - 10;

          nextValue = Math.max(
            0,
            currentPower + variation
          );
        }

        if (currentStatus === "STANDBY") {
          const variation =
            Math.floor(Math.random() * 3) - 1;

          nextValue = Math.max(
            0,
            currentPower + variation
          );
        }

        if (currentStatus === "OFF") {
          nextValue = 0;
        }

        return [
          ...previous.slice(-10),
          nextValue,
        ];
      });
    }, 3000);

    return () => clearInterval(interval);
  }, [currentPower, currentStatus]);

  /* =====================================================
     AUTO OFF
  ===================================================== */

  useEffect(() => {
    const timer = setInterval(() => {
      setLimits((currentLimits) =>
        currentLimits.map((item) => {
          if (
            item.type !== "Device" ||
            item.name !== "TV" ||
            item.status !== "STANDBY" ||
            !item.autoOff
          ) {
            return item;
          }

          const nextMinutes =
            (item.standbyMinutes ?? 0) + 1;

          if (
            nextMinutes >=
            (item.standbyLimit ?? 30)
          ) {
            return {
              ...item,
              status: "OFF",
              current: 0,
              standbyMinutes: nextMinutes,
            };
          }

          return {
            ...item,
            standbyMinutes: nextMinutes,
          };
        })
      );
    }, 10000);

    return () => clearInterval(timer);
  }, []);

  /* =====================================================
     ENERGY ASSISTANT
  ===================================================== */

  useEffect(() => {
    const exceededItem =
      limits.find(
        (item) =>
          item.enabled &&
          item.status !== "OFF" &&
          item.current > item.limit
      );

    const phantomDevice =
      limits.find(
        (item) =>
          item.type === "Device" &&
          item.status === "STANDBY" &&
          item.current > 0
      );

    if (exceededItem) {
      setAssistantMessage({
        type: "limit",
        device: exceededItem.name,
        power: exceededItem.current,
        limit: exceededItem.limit,
        exceededBy:
          exceededItem.current -
          exceededItem.limit,
      });

      return;
    }

    if (phantomDevice) {
      const monthlyWastage =
        (
          (phantomDevice.current *
            24 *
            30) /
          1000
        ).toFixed(1);

      const estimatedCost =
        Math.round(
          Number(monthlyWastage) * 6
        );

      setAssistantMessage({
        type: "phantom",
        device: phantomDevice.name,
        power: phantomDevice.current,
        standbyMinutes:
          phantomDevice.standbyMinutes ?? 0,
        monthlyEnergy:
          monthlyWastage,
        monthlyCost:
          estimatedCost,
      });

      return;
    }

    setAssistantMessage(null);
  }, [limits]);

  /* =====================================================
     LIMIT CONTROLS
  ===================================================== */

  const toggleLimit = (id) => {
    setLimits((currentLimits) =>
      currentLimits.map((item) =>
        item.id === id
          ? {
              ...item,
              enabled: !item.enabled,
            }
          : item
      )
    );
  };

  const toggleAutoOff = (id) => {
    setLimits((currentLimits) =>
      currentLimits.map((item) =>
        item.id === id
          ? {
              ...item,
              autoOff: !item.autoOff,
            }
          : item
      )
    );
  };

  /* =====================================================
     DEVICE CONTROLS
  ===================================================== */

  const turnOffDevice = (id) => {
    setLimits((currentLimits) =>
      currentLimits.map((item) =>
        item.id === id
          ? {
              ...item,
              status: "OFF",
              current: 0,
            }
          : item
      )
    );

    setPhantomLoad(false);
    setAssistantDismissed(false);
  };

  const restoreDevice = (id) => {
    setLimits((currentLimits) =>
      currentLimits.map((item) =>
        item.id === id
          ? {
              ...item,
              status: "ON",
              current:
                item.name === "TV"
                  ? 180
                  : item.current || 100,
              standbyMinutes: 0,
            }
          : item
      )
    );

    setAssistantDismissed(false);
  };

  /* =====================================================
     DEMO SIMULATION
  ===================================================== */

  const simulateStandby = () => {
    setLimits((currentLimits) =>
      currentLimits.map((item) =>
        item.name === "TV"
          ? {
              ...item,
              status: "STANDBY",
              current: 8,
              standbyMinutes: 0,
            }
          : item
      )
    );

    setAssistantDismissed(false);
    setPhantomLoad(true);
  };

  const simulateHighPower = () => {
    setLimits((currentLimits) =>
      currentLimits.map((item) =>
        item.name === "TV"
          ? {
              ...item,
              status: "ON",
              current: 180,
              standbyMinutes: 0,
            }
          : item
      )
    );

    setAssistantDismissed(false);
    setPhantomLoad(false);
  };

  /* =====================================================
     ASSISTANT ACTIONS
  ===================================================== */

  const assistantTurnOff = () => {
    if (!assistantMessage) return;

    const deviceName =
      assistantMessage.device;

    setLimits((currentLimits) =>
      currentLimits.map((item) =>
        item.name === deviceName
          ? {
              ...item,
              status: "OFF",
              current: 0,
            }
          : item
      )
    );

    setPhantomLoad(false);
    setAssistantDismissed(true);
  };

  const ignoreAssistant = () => {
    setAssistantDismissed(true);
  };

  const resetAssistant = () => {
    setAssistantDismissed(false);
  };

  /* =====================================================
     ADD LIMIT
  ===================================================== */

  const addLimit = () => {
    console.log("SAVE LIMIT CLICKED");

    const name =
      String(newLimit.name || "").trim();

    const limitValue =
      String(newLimit.limit || "").trim();

    if (name === "") {
      alert("Please enter a device or room name.");
      return;
    }

    if (limitValue === "") {
      alert("Please enter an energy limit.");
      return;
    }

    const numericLimit =
      Number(limitValue);

    if (
      !Number.isFinite(numericLimit) ||
      numericLimit <= 0
    ) {
      alert("Please enter a valid energy limit greater than 0.");
      return;
    }

    const newItem = {
      id: Date.now(),
      type: newLimit.type,
      name: name,
      current: 0,
      limit: numericLimit,
      enabled: true,
      autoOff: false,
      status: "ON",
    };

    if (newLimit.type === "Device") {
      newItem.standbyMinutes = 0;
      newItem.standbyLimit = 30;
    }

    setLimits((previousLimits) => [
      ...previousLimits,
      newItem,
    ]);

    setNewLimit({
      type: "Device",
      name: "",
      limit: "",
    });

    setShowLimitForm(false);
  };

  const removeLimit = (id) => {
    setLimits((currentLimits) =>
      currentLimits.filter(
        (item) => item.id !== id
      )
    );
  };

  /* =====================================================
     GRAPH
  ===================================================== */

  const graphWidth = 700;
  const graphHeight = 220;

  const maxPower = Math.max(
    200,
    ...powerHistory
  );

  const graphPoints = powerHistory
    .map((value, index) => {
      const x =
        (index /
          (powerHistory.length - 1)) *
        graphWidth;

      const y =
        graphHeight -
        (value / maxPower) *
          (graphHeight - 20);

      return `${x},${y}`;
    })
    .join(" ");

  const getStatusClass = (status) => {
    if (status === "ON") {
      return "on";
    }

    if (status === "STANDBY") {
      return "standby-status";
    }

    return "off";
  };

  /* =====================================================
     UI
  ===================================================== */

  return (
    <div className="app-shell">

      <header className="top-header">
        <div className="brand">
          <div className="brand-mark">
            P
          </div>

          <div>
            <h1>
              PhantomGuard
            </h1>

            <span>
              Smart Energy Monitoring System
            </span>
          </div>
        </div>

        <div className="header-status">
          <span className="status-dot"></span>
          System Online
        </div>
      </header>

      <main className="dashboard">

        <section className="dashboard-title">
          <div>
            <p className="eyebrow">
              ENERGY INTELLIGENCE
            </p>

            <h2>
              Monitor. Detect. Save.
            </h2>

            <p>
              Track energy consumption,
              identify phantom loads and
              manage intelligent energy limits.
            </p>
          </div>
        </section>

        <section className="stats-grid">

          <div className="stat-card">
            <span className="stat-label">
              CURRENT POWER
            </span>

            <strong>
              {currentPower}
              <small> W</small>
            </strong>

            <span className="stat-meta">
              Live simulation
            </span>
          </div>

          <div className="stat-card">
            <span className="stat-label">
              DETECTED APPLIANCE
            </span>

            <strong>
              {detectedAppliance}
            </strong>

            <span className="stat-meta">
              AI monitored
            </span>
          </div>

          <div className="stat-card">
            <span className="stat-label">
              DEVICE STATUS
            </span>

            <strong
              className={
                currentStatus === "OFF"
                  ? "off-text"
                  : "normal-text"
              }
            >
              {currentStatus}
            </strong>

            <span className="stat-meta">
              Software state
            </span>
          </div>

          <div className="stat-card">
            <span className="stat-label">
              ENERGY SIMULATION
            </span>

            <strong>
              {energyUsed}
              <small> kWh</small>
            </strong>

            <span className="stat-meta">
              Simulated reading
            </span>
          </div>

        </section>

        <section className="dashboard-grid">

          <div className="panel graph-panel">

            <div className="panel-header">
              <div>
                <span className="panel-kicker">
                  POWER CONSUMPTION
                </span>

                <h3>
                  Energy usage over time
                </h3>
              </div>

              <span className="live-badge">
                ● LIVE SIMULATION
              </span>
            </div>

            <div className="graph-container">

              <svg
                viewBox={`0 0 ${graphWidth} ${graphHeight}`}
                preserveAspectRatio="none"
                className="power-graph"
              >

                <line
                  x1="0"
                  y1="55"
                  x2={graphWidth}
                  y2="55"
                  className="graph-grid-line"
                />

                <line
                  x1="0"
                  y1="110"
                  x2={graphWidth}
                  y2="110"
                  className="graph-grid-line"
                />

                <line
                  x1="0"
                  y1="165"
                  x2={graphWidth}
                  y2="165"
                  className="graph-grid-line"
                />

                <polyline
                  points={graphPoints}
                  fill="none"
                  className="graph-line"
                />

              </svg>

              <div className="graph-labels">
                <span>-30 min</span>
                <span>-20 min</span>
                <span>-10 min</span>
                <span>Now</span>
              </div>

            </div>
          </div>

          <div className="panel current-load-panel">

            <div className="panel-header">
              <div>
                <span className="panel-kicker">
                  CURRENT LOAD
                </span>

                <h3>
                  Device activity
                </h3>
              </div>
            </div>

            <div className="current-load-value">
              <strong>
                {currentPower}
              </strong>

              <span>
                W
              </span>
            </div>

            <div className="load-device">

              <div className="device-icon">
                TV
              </div>

              <div>
                <strong>
                  {detectedAppliance}
                </strong>

                <span>
                  {currentStatus === "STANDBY"
                    ? "Standby consumption detected"
                    : currentStatus === "OFF"
                    ? "Device turned off"
                    : "Device actively consuming power"}
                </span>
              </div>

            </div>

            <div className="load-status-row">
              <span>Status</span>

              <strong
                className={
                  currentStatus === "OFF"
                    ? "off-status"
                    : ""
                }
              >
                {currentStatus}
              </strong>
            </div>

          </div>

        </section>

        <section className="dashboard-grid">

          <div className="panel phantom-panel">

            <div className="panel-header">
              <div>
                <span className="panel-kicker">
                  PHANTOM LOAD
                </span>

                <h3>
                  Standby energy detection
                </h3>
              </div>

              <span className="risk-badge">
                {phantomLoad &&
                currentStatus === "STANDBY"
                  ? "DETECTED"
                  : "NORMAL"}
              </span>
            </div>

            <div className="phantom-content">

              <div className="phantom-icon">
                ⚡
              </div>

              <div>
                <strong>
                  {phantomLoad &&
                  currentStatus === "STANDBY"
                    ? `${currentPower} W standby load`
                    : "No active phantom load"}
                </strong>

                <p>
                  {phantomLoad &&
                  currentStatus === "STANDBY"
                    ? "The monitored device is consuming power while in standby mode."
                    : "The system currently detects no standby power wastage."}
                </p>
              </div>

            </div>

          </div>

          <div className="panel tariff-panel">

            <div className="panel-header">
              <div>
                <span className="panel-kicker">
                  TARIFF
                </span>

                <h3>
                  Energy cost estimate
                </h3>
              </div>

              <span className="live-badge">
                ₹6 / kWh
              </span>
            </div>

            <div className="tariff-value">
              ₹
              {estimatedMonthlyCost.toFixed(0)}
              <span>
                / month
              </span>
            </div>

            <div className="tariff-row">
              <span>
                Current power
              </span>

              <strong>
                {currentPower} W
              </strong>
            </div>

            <div className="tariff-row">
              <span>
                Monthly energy equivalent
              </span>

              <strong>
                {estimatedMonthlyEnergy.toFixed(1)}
                {" "}kWh
              </strong>
            </div>

            <div className="tariff-row">
              <span>
                Phantom-load cost
              </span>

              <strong>
                ₹
                {phantomMonthlyCost.toFixed(0)}
                / month
              </strong>
            </div>

            <div className="tariff-row">
              <span>
                Potential saving
              </span>

              <strong className="normal-text">
                ₹
                {potentialMonthlySavings.toFixed(0)}
                / month
              </strong>
            </div>

          </div>

        </section>

        <section className="panel assistant-panel">

          <div className="assistant-heading">

            <div className="assistant-icon">
              ✦
            </div>

            <div>
              <span className="panel-kicker">
                INTELLIGENT RECOMMENDATION
              </span>

              <h3>
                Energy Assistant
              </h3>
            </div>

            <span className="assistant-badge">
              RULE-BASED AI
            </span>

          </div>

          <div className="assistant-content">

            {!assistantDismissed &&
            assistantMessage ? (

              <div className="assistant-alert">

                <div className="assistant-alert-icon">
                  !
                </div>

                <div className="assistant-text">

                  <div className="assistant-title-row">
                    <strong>
                      Action recommended
                    </strong>

                    <span>
                      {assistantMessage.type ===
                      "limit"
                        ? "LIMIT ALERT"
                        : "PHANTOM LOAD"}
                    </span>
                  </div>

                  {assistantMessage.type ===
                  "limit" ? (

                    <p>
                      <strong>
                        {assistantMessage.device}
                      </strong>{" "}
                      is consuming{" "}
                      <strong>
                        {assistantMessage.power} W
                      </strong>
                      , exceeding its configured
                      limit of{" "}
                      <strong>
                        {assistantMessage.limit} W
                      </strong>{" "}
                      by{" "}
                      <strong>
                        {assistantMessage.exceededBy} W
                      </strong>.
                    </p>

                  ) : (

                    <p>
                      <strong>
                        {assistantMessage.device}
                      </strong>{" "}
                      is using{" "}
                      <strong>
                        {assistantMessage.power} W
                      </strong>{" "}
                      in standby. Turning it off
                      could reduce approximately{" "}
                      <strong>
                        ₹
                        {assistantMessage.monthlyCost}
                      </strong>{" "}
                      of simulated monthly cost.
                    </p>

                  )}

                  <div className="assistant-actions">

                    <button
                      type="button"
                      className="assistant-turnoff-button"
                      onClick={assistantTurnOff}
                    >
                      Turn Off Device
                    </button>

                    <button
                      type="button"
                      className="assistant-ignore-button"
                      onClick={ignoreAssistant}
                    >
                      Ignore
                    </button>

                  </div>

                </div>

              </div>

            ) : (

              <div className="assistant-safe">

                <div className="assistant-safe-icon">
                  ✓
                </div>

                <div>
                  <strong>
                    Energy usage looks normal
                  </strong>

                  <p>
                    No immediate energy-saving
                    action is currently required.
                  </p>
                </div>

                <button
  type="button"
  className="save-limit-button"
  onClick={() => {
    alert("BUTTON CLICKED");
  }}
>
  Save Limit
</button>

              </div>

            )}

          </div>

        </section>

        {/* =================================================
            ENERGY LIMITS
        ================================================= */}

        <section className="panel limits-panel">

          <div className="panel-header">

            <div>
              <span className="panel-kicker">
                ENERGY MANAGEMENT
              </span>

              <h3>
                Energy Limits
              </h3>

              <p>
                Configure consumption limits for
                rooms and individual devices.
              </p>
            </div>

            <button
              type="button"
              className="add-limit-button"
              onClick={() =>
                setShowLimitForm(
                  (previous) => !previous
                )
              }
            >
              + Add Limit
            </button>

          </div>

          {/* ADD LIMIT FORM */}

          {showLimitForm && (

            <div className="limit-form">

              <div className="form-field">

                <label>
                  Type
                </label>

                <select
                  value={newLimit.type}
                  onChange={(event) =>
                    setNewLimit(
                      (previous) => ({
                        ...previous,
                        type: event.target.value,
                      })
                    )
                  }
                >
                  <option value="Device">
                    Device
                  </option>

                  <option value="Room">
                    Room
                  </option>
                </select>

              </div>

              <div className="form-field">

                <label>
                  Name
                </label>

                <input
                  type="text"
                  placeholder="e.g. AC"
                  value={newLimit.name}
                  onChange={(event) =>
                    setNewLimit(
                      (previous) => ({
                        ...previous,
                        name: event.target.value,
                      })
                    )
                  }
                />

              </div>

              <div className="form-field">

                <label>
                  Limit (W)
                </label>

                <input
                  type="number"
                  placeholder="150"
                  min="1"
                  value={newLimit.limit}
                  onChange={(event) =>
                    setNewLimit(
                      (previous) => ({
                        ...previous,
                        limit: event.target.value,
                      })
                    )
                  }
                />

              </div>

              {/* SAVE BUTTON */}

              <button
                type="button"
                className="save-limit-button"
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  addLimit();
                }}
              >
                Save Limit
              </button>

            </div>

          )}

          {/* LIMIT LIST */}

          <div className="limits-list">

            {limits.map((item) => {

              const percentage =
                item.limit > 0
                  ? Math.min(
                      100,
                      Math.round(
                        (item.current /
                          item.limit) *
                          100
                      )
                    )
                  : 0;

              const exceeded =
                item.enabled &&
                item.status !== "OFF" &&
                item.current >
                  item.limit;

              return (

                <div
                  className={`limit-item ${
                    exceeded
                      ? "limit-exceeded"
                      : ""
                  }`}
                  key={item.id}
                >

                  <div className="limit-main">

                    <div className="limit-icon">
                      {item.type === "Room"
                        ? "⌂"
                        : "▣"}
                    </div>

                    <div className="limit-info">

                      <div className="limit-title">

                        <strong>
                          {item.name}
                        </strong>

                        <span>
                          {item.type}
                        </span>

                        {exceeded && (
                          <small className="limit-exceeded-label">
                            LIMIT EXCEEDED
                          </small>
                        )}

                      </div>

                      <div className="limit-values">
                        <span>
                          {item.current} W
                        </span>

                        <span>
                          / {item.limit} W
                        </span>
                      </div>

                      <div className="limit-bar">

                        <div
                          className={`limit-fill ${
                            exceeded
                              ? "danger"
                              : ""
                          }`}
                          style={{
                            width: `${percentage}%`,
                          }}
                        />

                      </div>

                    </div>

                  </div>

                  <div className="limit-controls">

                    <button
                      type="button"
                      className={
                        item.enabled
                          ? "limit-toggle active"
                          : "limit-toggle"
                      }
                      onClick={() =>
                        toggleLimit(item.id)
                      }
                    >
                      {item.enabled
                        ? "Enabled"
                        : "Disabled"}
                    </button>

                    {item.type ===
                      "Device" && (

                      <button
                        type="button"
                        className="device-action-button"
                        onClick={() =>
                          item.status ===
                          "OFF"
                            ? restoreDevice(
                                item.id
                              )
                            : turnOffDevice(
                                item.id
                              )
                        }
                      >
                        {item.status ===
                        "OFF"
                          ? "Restore"
                          : "Turn Off"}
                      </button>

                    )}

                    <button
                      type="button"
                      className="remove-limit-button"
                      onClick={() =>
                        removeLimit(
                          item.id
                        )
                      }
                    >
                      ×
                    </button>

                  </div>

                  {item.type ===
                    "Device" && (

                    <div className="device-settings">

                      <div className="device-state">

                        <span>
                          State
                        </span>

                        <strong
                          className={`device-status ${getStatusClass(
                            item.status
                          )}`}
                        >
                          {item.status}
                        </strong>

                      </div>

                      {item.status ===
                        "STANDBY" && (

                        <div className="standby-timer">

                          <span>
                            Standby
                          </span>

                          <strong>
                            {item.standbyMinutes ??
                              0}
                            /
                            {item.standbyLimit ??
                              30}{" "}
                            min
                          </strong>

                        </div>

                      )}

                      <div className="auto-off-setting">

                        <span>
                          Auto-Off
                        </span>

                        <button
                          type="button"
                          className={
                            item.autoOff
                              ? "limit-toggle active"
                              : "limit-toggle"
                          }
                          onClick={() =>
                            toggleAutoOff(
                              item.id
                            )
                          }
                        >
                          {item.autoOff
                            ? "ON"
                            : "OFF"}
                        </button>

                      </div>

                    </div>

                  )}

                </div>

              );
            })}

          </div>

        </section>

        {/* DEMO CONTROLS */}

        <section className="demo-controls">

          <div>
            <strong>
              Demo Simulation
            </strong>

            <span>
              Use these controls to demonstrate
              PhantomGuard detection.
            </span>
          </div>

          <div className="demo-buttons">

            <button
              type="button"
              className="demo-high-button"
              onClick={simulateHighPower}
            >
              Simulate High Power
            </button>

            <button
              type="button"
              className="demo-standby-button"
              onClick={simulateStandby}
            >
              Return to Standby
            </button>

          </div>

        </section>

        {/* SOFTWARE NOTICE */}

        <div className="software-notice">

          <span>
            i
          </span>

          <div>

            <strong>
              Software Simulation Mode
            </strong>

            <p>
              PhantomGuard currently simulates
              device power states, energy limits,
              phantom-load detection and
              automatic turn-off logic in software.
              No physical electrical device is
              controlled.
            </p>

          </div>

        </div>

      </main>

      <footer className="footer">
        PhantomGuard · Smart Energy Monitoring
        System
      </footer>

    </div>
  );
}

export default App;