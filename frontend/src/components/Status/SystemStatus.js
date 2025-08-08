import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  LinearProgress,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Speed as CpuIcon,
  Storage as DiskIcon,
  NetworkCheck as NetworkIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { apiService } from '../../services/apiService';

function SystemStatus({ systemStatus, onShowNotification }) {
  const [detailedStatus, setDetailedStatus] = useState(null);
  const [networkStatus, setNetworkStatus] = useState(null);
  const [diagnostics, setDiagnostics] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDetailedStatus();
  }, []);

  const loadDetailedStatus = async () => {
    try {
      setLoading(true);
      
      const [statusResponse, networkResponse, diagnosticsResponse] = await Promise.all([
        apiService.getSystemStatus(),
        apiService.getNetworkStatus(),
        apiService.runDiagnostics()
      ]);

      if (statusResponse.success) {
        setDetailedStatus(statusResponse);
      }
      
      if (networkResponse.success) {
        setNetworkStatus(networkResponse.network);
      }
      
      if (diagnosticsResponse.success) {
        setDiagnostics(diagnosticsResponse.diagnostics);
      }
    } catch (error) {
      onShowNotification(`Failed to load system status: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pass': return 'success';
      case 'warning': return 'warning';
      case 'fail': return 'error';
      default: return 'default';
    }
  };

  const resources = detailedStatus?.resources || {};
  const streamStats = detailedStatus?.streams || {};

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          System Status
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadDetailedStatus}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* System Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CpuIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">CPU Usage</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {resources.cpu?.percent?.toFixed(1) || 0}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={resources.cpu?.percent || 0}
                color={resources.cpu?.percent > 80 ? 'error' : 'primary'}
              />
              <Typography variant="caption" color="textSecondary">
                {resources.cpu?.count || 0} cores
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <MemoryIcon sx={{ mr: 1, color: 'secondary.main' }} />
                <Typography variant="h6">Memory Usage</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {resources.memory?.percent?.toFixed(1) || 0}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={resources.memory?.percent || 0}
                color={resources.memory?.percent > 80 ? 'error' : 'secondary'}
              />
              <Typography variant="caption" color="textSecondary">
                {formatBytes(resources.memory?.used || 0)} / {formatBytes(resources.memory?.total || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <DiskIcon sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">Disk Usage</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {resources.disk?.percent?.toFixed(1) || 0}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={resources.disk?.percent || 0}
                color={resources.disk?.percent > 80 ? 'error' : 'warning'}
              />
              <Typography variant="caption" color="textSecondary">
                {formatBytes(resources.disk?.free || 0)} free
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <NetworkIcon sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Network</Typography>
              </Box>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {streamStats.estimated_bandwidth_mbps?.toFixed(1) || 0}
              </Typography>
              <Typography variant="caption" color="textSecondary" display="block">
                Mbps estimated bandwidth
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {streamStats.total_streams || 0} active streams
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Diagnostics Results */}
      {diagnostics && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  System Diagnostics
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Chip
                    label={`Overall Status: ${diagnostics.overall_status?.toUpperCase()}`}
                    color={getStatusColor(diagnostics.overall_status)}
                    sx={{ mr: 2 }}
                  />
                  <Typography variant="caption" color="textSecondary">
                    Last run: {new Date(diagnostics.timestamp).toLocaleString()}
                  </Typography>
                </Box>
                
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Test</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Details</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {diagnostics.tests?.map((test, index) => (
                        <TableRow key={index}>
                          <TableCell>{test.name}</TableCell>
                          <TableCell>
                            <Chip
                              label={test.status.toUpperCase()}
                              color={getStatusColor(test.status)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {test.error && (
                              <Typography variant="body2" color="error">
                                {test.error}
                              </Typography>
                            )}
                            {test.details && (
                              <Typography variant="body2" color="textSecondary">
                                {JSON.stringify(test.details)}
                              </Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Network Interfaces */}
      {networkStatus && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Network Interfaces
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Interface</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>IPv4 Address</TableCell>
                        <TableCell>MTU</TableCell>
                        <TableCell>Multicast</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {networkStatus.interfaces?.map((iface, index) => (
                        <TableRow key={index}>
                          <TableCell>{iface.name}</TableCell>
                          <TableCell>
                            <Chip
                              label={iface.is_up ? 'UP' : 'DOWN'}
                              color={iface.is_up ? 'success' : 'error'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {iface.addresses?.find(addr => addr.type === 'IPv4')?.address || 'N/A'}
                          </TableCell>
                          <TableCell>{iface.mtu}</TableCell>
                          <TableCell>
                            <Chip
                              label={iface.supports_multicast ? 'YES' : 'NO'}
                              color={iface.supports_multicast ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* System Information */}
      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                System Information
              </Typography>
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Hostname:</strong> {detailedStatus?.system?.hostname || 'Unknown'}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Uptime:</strong> {formatUptime(detailedStatus?.system?.uptime || 0)}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Version:</strong> {detailedStatus?.system?.version || '1.0.0'}
                </Typography>
                <Typography variant="body2">
                  <strong>Platform:</strong> {detailedStatus?.system?.platform?.system || 'Unknown'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Stream Statistics
              </Typography>
              <Box>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Total Senders:</strong> {streamStats.senders?.total || 0} 
                  ({streamStats.senders?.active || 0} active)
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Total Receivers:</strong> {streamStats.receivers?.total || 0} 
                  ({streamStats.receivers?.active || 0} active)
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Total Bandwidth:</strong> {streamStats.estimated_bandwidth_mbps?.toFixed(2) || 0} Mbps
                </Typography>
                <Typography variant="body2">
                  <strong>Active Streams:</strong> {streamStats.total_streams || 0}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default SystemStatus;
