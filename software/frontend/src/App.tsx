import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { WorkspaceTab, TelemetryPacket, CalibrationProfile } from './types';
import { bridge, DeviceStatus } from './bridge/bridgeClient';
import { ThemeProvider } from './context/ThemeContext';
import { Header } from './components/common/Header';
import { Sidebar } from './components/common/Sidebar';
import { StartupPOST } from './components/common/StartupPOST';
import { PostUpdateChangelogModal, ChangelogData } from './components/common/PostUpdateChangelogModal';
import { NotificationToastContainer, ToastNotification } from './components/common/NotificationToast';
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
  const [deviceStatus, setDeviceStatus] = useState<DeviceStatus | null>(null);
  const [notifications, setNotifications] = useState<ToastNotification[]>([]);
  const [calibration, setCalibration] = useState<CalibrationProfile | null>(null);
  const [updateAvailable, setUpdateAvailable] = useState<boolean>(false);
  const [pendingChangelog, setPendingChangelog] = useState<ChangelogData | null>(null);
  const [appVersion, setAppVersion] = useState<string>('2.3.2');

  const addNotification = useCallback((notif: Omit<ToastNotification, 'id'>) => {
    const id = Date.now().toString() + Math.random().toString(36).substring(2, 7);
    setNotifications(prev => [...prev.slice(-4), { ...notif, id }]);
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  useEffect(() => {
    // Dynamic version retrieval from installed binary
    bridge.getAppVersion().then((v) => {
      if (v) setAppVersion(v);
    }).catch(console.error);

    // Initial device status load
    bridge.getDeviceStatus().then((st) => {
      if (st) setDeviceStatus(st);
    }).catch(console.error);

    // Check if an update was recently installed and needs changelog acknowledgement
    bridge.checkPendingChangelog().then((res) => {
      if (res && res.show) {
        setPendingChangelog(res);
      }
    }).catch(console.error);

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
      } else if (st === 'DISCONNECTED') {
        setIsConnected(false);
      }
    });

    // Subscribe to explicit dual device status (Arduino Online vs Sensor Active)
    const unsubDeviceStatus = bridge.onDeviceStatus((st) => {
      setDeviceStatus(st);
      if (st.arduino_online && st.sensor_active) {
        setIsConnected(true);
      } else if (!st.arduino_online) {
        setIsConnected(false);
      }
    });

    // Subscribe to system and firmware notifications
    const unsubAppNotif = bridge.onAppNotification((type, title, message) => {
      addNotification({ type, title, message });
    });

    const unsubFwDone = bridge.onFirmwareFlashCompleted((success, message, statusType) => {
      const finalStatus = statusType || (success ? 'SUCCESS' : 'FAILED');
      const type = finalStatus === 'SUCCESS' ? 'success' : finalStatus === 'WARNING' ? 'warning' : 'error';
      const title = finalStatus === 'SUCCESS' 
        ? 'Firmware Flash Successful' 
        : finalStatus === 'WARNING' 
        ? 'Firmware Flash Warning' 
        : 'Firmware Flash Failed';
      addNotification({
        type,
        title,
        message,
        actionLabel: finalStatus === 'FAILED' ? 'Open Recovery' : undefined,
        onAction: finalStatus === 'FAILED' ? () => setCurrentTab('settings') : undefined,
        durationMs: finalStatus === 'FAILED' ? 15000 : 8000
      });
    });

    // Subscribe to update notifications
    const unsubUpdate = bridge.onUpdateResult((res) => {
      if (res && res.available) {
        setUpdateAvailable(true);
        addNotification({
          type: 'info',
          title: 'Update Available',
          message: `LuxSense Pro v${res.version || res.tag_name} is available. Visit Settings to review and install.`
        });
      }
    });

    return () => {
      unsubTelemetry();
      unsubStatus();
      unsubHardwareState();
      unsubDeviceStatus();
      unsubAppNotif();
      unsubFwDone();
      unsubUpdate();
    };
  }, [addNotification]);

  const handleAcknowledgeChangelog = () => {
    if (pendingChangelog) {
      bridge.acknowledgeUpdate(pendingChangelog.current_version).catch(console.error);
    }
    setPendingChangelog(null);
  };

  return (
    <ThemeProvider>
      <div className="flex flex-col h-screen w-screen bg-chassis-900 text-[#DFE2E8] font-sans overflow-hidden select-none">
        {/* Floating App Notification Toast System */}
        <NotificationToastContainer 
          notifications={notifications} 
          onDismiss={removeNotification} 
        />

        {/* Cinematic Startup POST sequence */}
        <AnimatePresence>
          {showStartup && (
            <StartupPOST onComplete={() => setShowStartup(false)} />
          )}
        </AnimatePresence>

        {/* Post-Update Changelog Card & Release Experience */}
        {!showStartup && pendingChangelog && (
          <PostUpdateChangelogModal 
            data={pendingChangelog}
            onAcknowledge={handleAcknowledgeChangelog}
          />
        )}

        {/* Main Instrument Shell */}
        <Header 
          currentPacket={currentPacket}
          statusMessage={statusMessage}
          statusColor={statusColor}
          hardwareState={hardwareState}
          isConnected={isConnected}
          appVersion={appVersion}
          deviceStatus={deviceStatus}
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

