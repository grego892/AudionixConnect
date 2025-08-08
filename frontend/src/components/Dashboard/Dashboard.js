import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Send as SendIcon,
  CallReceived as ReceiveIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon
} from '@mui/icons-material';
import { apiService } from '../../services/apiService';

function Dashboard({ systemStatus, onShowNotification }) {
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const response = await apiService.getStreamOverview();
      if (response.success) {
        setOverview(response.overview);
      }
    } catch (error) {
      onShowNotification(`Failed to load overview: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleStreamAction = async (streamType, streamId, action) => {
    try {
      let response;
      if (streamType === 'sender') {
        if (action === 'start') {
          response = await apiService.startSender(streamId);
        } else {
          response = await apiService.stopSender(streamId);
        }
      } else {
        if (action === 'start') {
          response = await apiService.startReceiver(streamId);
        } else {
          response = await apiService.stopReceiver(streamId);
        }
      }

      if (response.success) {
        onShowNotification(`${streamType} ${action}ed successfully`, 'success');
        loadOverview();
      }
    } catch (error) {
      onShowNotification(`Failed to ${action} ${streamType}: ${error.message}`, 'error');
    }
  };

  const formatAudioLevel = (level) => {
    if (level <= -60) return { value: 0, color: 'grey', text: 'Silent' };
    if (level >= -0.1) return { value: 100, color: 'error', text: 'CLIP!' };
    
    const percentage = ((level + 60) / 60) * 100;
    let color = 'success';
    if (level > -12) color = 'error';
    else if (level > -20) color = 'warning';
    
    return { value: percentage, color, text: `${level.toFixed(1)} dBFS` };
  };

  const getStatusChip = (active, errors = 0) => {
    if (errors > 0) {
      return <Chip icon={<ErrorIcon />} label="Error" color="error" size="small" />;
    }
    if (active) {
      return <Chip icon={<SuccessIcon />} label="Active" color="success" size="small" />;
    }
    return <Chip label="Inactive" color="default" size="small" />;
  };

  if (!systemStatus && !overview) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading dashboard...</Typography>
      </Box>
    );
  }

  const senders = systemStatus?.senders || [];
  const receivers = systemStatus?.receivers || [];
  const activeSenders = senders.filter(s => s.active).length;
  const activeReceivers = receivers.filter(r => r.active).length;
  const totalStreams = senders.length + receivers.length;
  const activeStreams = activeSenders + activeReceivers;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadOverview}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Streams
                  </Typography>
                  <Typography variant="h4">
                    {totalStreams}
                  </Typography>
                </Box>
                <Box sx={{ color: 'primary.main' }}>
                  <SendIcon sx={{ fontSize: 40 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Streams
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {activeStreams}
                  </Typography>
                </Box>
                <Box sx={{ color: 'success.main' }}>
                  <PlayIcon sx={{ fontSize: 40 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Senders
                  </Typography>
                  <Typography variant="h4" color="primary.main">
                    {activeSenders}/{senders.length}
                  </Typography>
                </Box>
                <Box sx={{ color: 'primary.main' }}>
                  <SendIcon sx={{ fontSize: 40 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Receivers
                  </Typography>
                  <Typography variant="h4" color="secondary.main">
                    {activeReceivers}/{receivers.length}
                  </Typography>
                </Box>
                <Box sx={{ color: 'secondary.main' }}>
                  <ReceiveIcon sx={{ fontSize: 40 }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Streams Table */}
      <Grid container spacing={3}>
        {/* Senders */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Audio Senders
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Audio Level</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {senders.map((sender) => {
                      const leftLevel = formatAudioLevel(sender.audio_levels?.left || -60);
                      const rightLevel = formatAudioLevel(sender.audio_levels?.right || -60);
                      
                      return (
                        <TableRow key={sender.id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {sender.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {getStatusChip(sender.active, sender.stats?.errors)}
                          </TableCell>
                          <TableCell>
                            <Box sx={{ minWidth: 120 }}>
                              <Typography variant="caption" display="block">
                                L: {leftLevel.text}
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={leftLevel.value}
                                color={leftLevel.color}
                                sx={{ height: 4, mb: 0.5 }}
                              />
                              <Typography variant="caption" display="block">
                                R: {rightLevel.text}
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={rightLevel.value}
                                color={rightLevel.color}
                                sx={{ height: 4 }}
                              />
                            </Box>
                          </TableCell>
                          <TableCell>
                            <IconButton
                              size="small"
                              color={sender.active ? "error" : "success"}
                              onClick={() => handleStreamAction('sender', sender.id, sender.active ? 'stop' : 'start')}
                            >
                              {sender.active ? <StopIcon /> : <PlayIcon />}
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                    {senders.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography color="textSecondary">
                            No senders configured
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Receivers */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Audio Receivers
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Audio Level</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {receivers.map((receiver) => {
                      const leftLevel = formatAudioLevel(receiver.audio_levels?.left || -60);
                      const rightLevel = formatAudioLevel(receiver.audio_levels?.right || -60);
                      
                      return (
                        <TableRow key={receiver.id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {receiver.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {getStatusChip(receiver.active, receiver.stats?.errors)}
                          </TableCell>
                          <TableCell>
                            <Box sx={{ minWidth: 120 }}>
                              <Typography variant="caption" display="block">
                                L: {leftLevel.text}
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={leftLevel.value}
                                color={leftLevel.color}
                                sx={{ height: 4, mb: 0.5 }}
                              />
                              <Typography variant="caption" display="block">
                                R: {rightLevel.text}
                              </Typography>
                              <LinearProgress
                                variant="determinate"
                                value={rightLevel.value}
                                color={rightLevel.color}
                                sx={{ height: 4 }}
                              />
                            </Box>
                          </TableCell>
                          <TableCell>
                            <IconButton
                              size="small"
                              color={receiver.active ? "error" : "success"}
                              onClick={() => handleStreamAction('receiver', receiver.id, receiver.active ? 'stop' : 'start')}
                            >
                              {receiver.active ? <StopIcon /> : <PlayIcon />}
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                    {receivers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography color="textSecondary">
                            No receivers configured
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;
