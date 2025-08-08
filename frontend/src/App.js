import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Alert,
  Snackbar
} from '@mui/material';

// Import components
import Sidebar from './components/Layout/Sidebar';
import Dashboard from './components/Dashboard/Dashboard';
import SendersPage from './components/Senders/SendersPage';
import ReceiversPage from './components/Receivers/ReceiversPage';
import SystemStatus from './components/Status/SystemStatus';
import Settings from './components/Settings/Settings';
import ConnectionStatus from './components/Common/ConnectionStatus';

// Import services
import { socketService } from './services/socketService';
import { apiService } from './services/apiService';

function App() {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [systemStatus, setSystemStatus] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    // Initialize socket connection
    socketService.connect();

    // Set up socket event handlers
    socketService.on('connect', () => {
      setConnectionStatus('connected');
      showNotification('Connected to AudionixConnect server', 'success');
    });

    socketService.on('disconnect', () => {
      setConnectionStatus('disconnected');
      showNotification('Disconnected from server', 'warning');
    });

    socketService.on('reconnecting', () => {
      setConnectionStatus('reconnecting');
    });

    socketService.on('status_update', (data) => {
      setSystemStatus(data);
    });

    socketService.on('error', (error) => {
      showNotification(`System error: ${error.message}`, 'error');
    });

    // Request initial status
    socketService.emit('request_status');

    // Cleanup on unmount
    return () => {
      socketService.disconnect();
    };
  }, []);

  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };

  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: '#1976d2'
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            AudionixConnect
          </Typography>
          <Typography variant="body2" sx={{ mr: 2, opacity: 0.8 }}>
            Professional Audio Streaming Management
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Sidebar 
        open={sidebarOpen} 
        onToggle={handleSidebarToggle}
        systemStatus={systemStatus}
      />

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: 8, // Account for AppBar height
          ml: sidebarOpen ? 0 : '-240px',
          transition: 'margin 0.3s ease'
        }}
      >
        <Container maxWidth="xl">
          <Routes>
            <Route 
              path="/" 
              element={
                <Dashboard 
                  systemStatus={systemStatus}
                  onShowNotification={showNotification}
                />
              } 
            />
            <Route 
              path="/senders" 
              element={
                <SendersPage 
                  onShowNotification={showNotification}
                />
              } 
            />
            <Route 
              path="/receivers" 
              element={
                <ReceiversPage 
                  onShowNotification={showNotification}
                />
              } 
            />
            <Route 
              path="/status" 
              element={
                <SystemStatus 
                  systemStatus={systemStatus}
                  onShowNotification={showNotification}
                />
              } 
            />
            <Route 
              path="/settings" 
              element={
                <Settings 
                  onShowNotification={showNotification}
                />
              } 
            />
          </Routes>
        </Container>
      </Box>

      {/* Connection Status Indicator */}
      <ConnectionStatus status={connectionStatus} />

      {/* Global Notifications */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;
