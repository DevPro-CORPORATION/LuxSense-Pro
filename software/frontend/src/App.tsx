import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { WorkspaceTab, TelemetryPacket, CalibrationProfile } from './types';
import { bridge } from './bridge/bridgeClient';
import { ThemeProvider } from './context/ThemeContext';
import { Header } from './components/common/Header';
import { Sidebar } from './components/common/Sidebar';
import { StartupPOST } from './components/common/StartupPOST';
import { LiveMonitorWorkspace } from './components/monitor/LiveMonitorWorkspace';
import { ScientificWorkspace } from './components/scientific/ScientificWorkspace';
import { AnalyticsWorkspace } from './components/analytics/AnalyticsWorkspace';
import { CalibrationLaboratory } from './components/calibration/CalibrationLaboratory';
import { HardwareSetupWorkspace } from './components/hardware/HardwareSetupWorkspace';
import { SettingsWorkspace } from './components/settings/SettingsWorkspace';
import { TechnicalInfoWorkspace } from './components/techinfo/TechnicalInfoWorkspace';
import { TeamWorkspace } from './components/team/TeamWorkspace';

export const App: React.FC = () => {
  const [showStartup, setShowStartup] = useState<boolean>(true);
  const [currentTab, setCurrentTab] = useState<WorkspaceTab>('monitor');
  const [currentPacket, setCurrentPacket] = useState<TelemetryPacket | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('SYNCHRONIZING TELEMETRY STREAM');
  const [statusColor, setStatusColor] = useState<string>('#21D789');
  const [hardwareState, setHardwareState] = useState<string>('CONNECTING');
  const [isConnected, setIsConnected] = useState<boolean>(true);
  const [calibration, setCalibration] = useState<CalibrationProfile | null>(null);
  const [updateAvailable, setUpdateAvailable] = useState<boolean>(false);

  useEffect(() => {
    // Initial calibration profile load
    bridge.getCalibration().then((cal) => {
      setCalibration(cal);
    }).catch(console.error);

    bridge.getHardwareState().then((st) => {
      if (st) setHardwareState(st);
    }).catch(() => {});

    // Subscribe to real-time telemetry packets
    const unsubTelemetry = bridge.onTelemetry((packet) => {
      setCurrentPacket(packet);
      setIsConnected(true);
      setHardwareState('LIVE MEASUREMENT');
    });

    // Subscribe to status updates
    const unsubStatus = bridge.onStatus((msg, col) => {
      setStatusMessage(msg);
      setStatusColor(col);
    });

    // Subscribe to explicit hardware acquisition state
    const unsubHardwareState = bridge.onHardwareState((st) => {
      setHardwareState(st);
      if (st === 'LIVE MEASUREMENT') {
        setIsConnected(true);
      } else if (st === 'DISCONNECTED' || st === 'SENSOR ERROR') {
        setIsConnected(false);
      }
    });

    // Subscribe to update notifications
    const unsubUpdate = bridge.onUpdateResult((res) => {
      if (res && res.available) {
        setUpdateAvailable(true);
      }
    });

    return () => {
      unsubTelemetry();
      unsubStatus();
      unsubHardwareState();
      unsubUpdate();
    };
  }, []);

  return (
    <ThemeProvider>
      <div className="flex flex-col h-screen w-screen bg-chassis-900 text-[#DFE2E8] font-sans overflow-hidden select-none">
        {/* Cinematic Startup POST sequence */}
        <AnimatePresence>
          {showStartup && (
            <StartupPOST onComplete={() => setShowStartup(false)} />
          )}
        </AnimatePresence>

        {/* Main Instrument Shell */}
        <Header 
          currentPacket={currentPacket}
          statusMessage={statusMessage}
          statusColor={statusColor}
          hardwareState={hardwareState}
          isConnected={isConnected}
        />

        <div className="flex flex-1 h-[calc(100vh-3rem)] overflow-hidden">
          {/* Navigation Sidebar */}
          <Sidebar 
            currentTab={currentTab} 
            onSelectTab={setCurrentTab}
            updateAvailable={updateAvailable}
          />

          {/* Dynamic Workspace Container */}
          <main className="flex-1 flex flex-col h-full overflow-hidden bg-chassis-900 relative">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentTab}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.18, ease: 'easeOut' }}
                className="w-full h-full flex flex-col overflow-hidden"
              >
                {currentTab === 'monitor' && (
                  <LiveMonitorWorkspace 
                    packet={currentPacket} 
                    calibration={calibration} 
                    hardwareState={hardwareState}
                  />
                )}

                {currentTab === 'scientific' && (
                  <ScientificWorkspace 
                    currentPacket={currentPacket}
                  />
                )}

                {currentTab === 'analytics' && (
                  <AnalyticsWorkspace />
                )}

                {currentTab === 'calibration' && (
                  <CalibrationLaboratory 
                    currentPacket={currentPacket}
                    onCalibrationSaved={(newCal) => setCalibration(newCal)}
                  />
                )}

                {currentTab === 'hardware' && (
                  <HardwareSetupWorkspace 
                    hardwareState={hardwareState}
                    isConnected={isConnected}
                    onNavigateToTab={setCurrentTab}
                  />
                )}

                {currentTab === 'settings' && (
                  <SettingsWorkspace 
                    onUpdateAvailableChange={(avail) => setUpdateAvailable(avail)}
                  />
                )}

                {currentTab === 'techinfo' && (
                  <TechnicalInfoWorkspace />
                )}

                {currentTab === 'team' && (
                  <TeamWorkspace />
                )}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>
    </ThemeProvider>
  );
};
export default App;

