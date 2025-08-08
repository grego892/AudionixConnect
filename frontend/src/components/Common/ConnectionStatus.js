import React from 'react';
import { Box, Typography, Chip } from '@mui/material';
import { 
  CheckCircle as ConnectedIcon,
  Error as DisconnectedIcon,
  Sync as ReconnectingIcon
} from '@mui/icons-material';

function ConnectionStatus({ status }) {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: <ConnectedIcon sx={{ fontSize: 16 }} />,
          text: 'Connected',
          color: 'success',
          className: 'connection-connected'
        };
      case 'disconnected':
        return {
          icon: <DisconnectedIcon sx={{ fontSize: 16 }} />,
          text: 'Disconnected',
          color: 'error',
          className: 'connection-disconnected'
        };
      case 'reconnecting':
        return {
          icon: <ReconnectingIcon sx={{ fontSize: 16, animation: 'spin 1s linear infinite' }} />,
          text: 'Reconnecting...',
          color: 'warning',
          className: 'connection-reconnecting'
        };
      default:
        return {
          icon: <DisconnectedIcon sx={{ fontSize: 16 }} />,
          text: 'Unknown',
          color: 'default',
          className: 'connection-disconnected'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Box
      className={`connection-status ${config.className}`}
      sx={{
        position: 'fixed',
        top: 20,
        right: 20,
        zIndex: 9999,
      }}
    >
      <Chip
        icon={config.icon}
        label={config.text}
        color={config.color}
        size="small"
        sx={{
          fontWeight: 500,
          boxShadow: 2,
        }}
      />
    </Box>
  );
}

export default ConnectionStatus;
