import React from 'react';
import { 
  Drawer, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Divider,
  Typography,
  Box,
  Chip
} from '@mui/material';
import { 
  Dashboard as DashboardIcon,
  Send as SendIcon,
  CallReceived as ReceiveIcon,
  Assessment as StatusIcon,
  Settings as SettingsIcon,
  Circle as CircleIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 240;

function Sidebar({ open, onToggle, systemStatus }) {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Senders', icon: <SendIcon />, path: '/senders' },
    { text: 'Receivers', icon: <ReceiveIcon />, path: '/receivers' },
    { text: 'System Status', icon: <StatusIcon />, path: '/status' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ];

  const getSystemStatusSummary = () => {
    if (!systemStatus) {
      return { active: 0, total: 0, status: 'unknown' };
    }

    const senders = systemStatus.senders || [];
    const receivers = systemStatus.receivers || [];
    const activeSenders = senders.filter(s => s.active).length;
    const activeReceivers = receivers.filter(r => r.active).length;
    const totalActive = activeSenders + activeReceivers;
    const totalStreams = senders.length + receivers.length;

    let status = 'idle';
    if (totalActive > 0) {
      status = 'active';
    }

    return { active: totalActive, total: totalStreams, status };
  };

  const statusSummary = getSystemStatusSummary();

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          marginTop: '64px', // Account for AppBar
          height: 'calc(100vh - 64px)',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          System Overview
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <CircleIcon 
            sx={{ 
              fontSize: 12, 
              mr: 1,
              color: statusSummary.status === 'active' ? 'success.main' : 'grey.500'
            }} 
          />
          <Typography variant="body2">
            {statusSummary.active}/{statusSummary.total} Active Streams
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip 
            label={`${systemStatus?.senders?.filter(s => s.active).length || 0} Senders`}
            size="small"
            color="primary"
            variant="outlined"
          />
          <Chip 
            label={`${systemStatus?.receivers?.filter(r => r.active).length || 0} Receivers`}
            size="small"
            color="secondary"
            variant="outlined"
          />
        </Box>
      </Box>

      <Divider />

      <List>
        {menuItems.map((item) => (
          <ListItem
            button
            key={item.text}
            selected={location.pathname === item.path}
            onClick={() => navigate(item.path)}
            sx={{
              '&.Mui-selected': {
                backgroundColor: 'primary.main',
                color: 'white',
                '&:hover': {
                  backgroundColor: 'primary.dark',
                },
                '& .MuiListItemIcon-root': {
                  color: 'white',
                },
              },
            }}
          >
            <ListItemIcon>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>

      <Divider sx={{ mt: 'auto' }} />
      
      <Box sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary">
          AudionixConnect v1.0.0
        </Typography>
      </Box>
    </Drawer>
  );
}

export default Sidebar;
