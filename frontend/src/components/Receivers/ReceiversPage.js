import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Grid,
  MenuItem,
  LinearProgress,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  VolumeUp as VolumeIcon,
  SignalWifi4Bar as SignalIcon
} from '@mui/icons-material';
import { apiService } from '../../services/apiService';

function ReceiversPage({ socketService, onShowNotification }) {
  const [receivers, setReceivers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingReceiver, setEditingReceiver] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [receiverToDelete, setReceiverToDelete] = useState(null);
  const [audioLevels, setAudioLevels] = useState({});

  const [formData, setFormData] = useState({
    name: '',
    multicast_address: '',
    port: 5004,
    interface: '',
    protocol: 'livewire_plus',
    audio_format: 'pcm_24',
    channels: 2,
    auto_start: false
  });

  useEffect(() => {
    loadReceivers();

    // Listen for real-time audio level updates
    if (socketService) {
      socketService.on('audio_levels', handleAudioLevels);
      socketService.on('receiver_status_changed', handleReceiverStatusChanged);
    }

    return () => {
      if (socketService) {
        socketService.off('audio_levels', handleAudioLevels);
        socketService.off('receiver_status_changed', handleReceiverStatusChanged);
      }
    };
  }, [socketService]);

  const loadReceivers = async () => {
    try {
      setLoading(true);
      const response = await apiService.getReceivers();
      if (response.success) {
        setReceivers(response.receivers);
      }
    } catch (error) {
      onShowNotification(`Failed to load receivers: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAudioLevels = (data) => {
    setAudioLevels(prev => ({
      ...prev,
      ...data
    }));
  };

  const handleReceiverStatusChanged = (data) => {
    setReceivers(prev => prev.map(receiver => 
      receiver.id === data.receiver_id 
        ? { ...receiver, status: data.status, stats: data.stats }
        : receiver
    ));
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      let response;
      
      if (editingReceiver) {
        response = await apiService.updateReceiver(editingReceiver.id, formData);
      } else {
        response = await apiService.createReceiver(formData);
      }

      if (response.success) {
        await loadReceivers();
        handleCloseDialog();
        onShowNotification(
          `Receiver ${editingReceiver ? 'updated' : 'created'} successfully`,
          'success'
        );
      }
    } catch (error) {
      onShowNotification(
        `Failed to ${editingReceiver ? 'update' : 'create'} receiver: ${error.message}`,
        'error'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!receiverToDelete) return;

    try {
      setLoading(true);
      const response = await apiService.deleteReceiver(receiverToDelete.id);
      if (response.success) {
        await loadReceivers();
        setDeleteDialogOpen(false);
        setReceiverToDelete(null);
        onShowNotification('Receiver deleted successfully', 'success');
      }
    } catch (error) {
      onShowNotification(`Failed to delete receiver: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleStartStop = async (receiver) => {
    try {
      const response = receiver.status === 'running' 
        ? await apiService.stopReceiver(receiver.id)
        : await apiService.startReceiver(receiver.id);

      if (response.success) {
        await loadReceivers();
        onShowNotification(
          `Receiver ${receiver.status === 'running' ? 'stopped' : 'started'} successfully`,
          'success'
        );
      }
    } catch (error) {
      onShowNotification(
        `Failed to ${receiver.status === 'running' ? 'stop' : 'start'} receiver: ${error.message}`,
        'error'
      );
    }
  };

  const handleOpenDialog = (receiver = null) => {
    if (receiver) {
      setEditingReceiver(receiver);
      setFormData({
        name: receiver.name,
        multicast_address: receiver.multicast_address,
        port: receiver.port,
        interface: receiver.interface || '',
        protocol: receiver.protocol,
        audio_format: receiver.audio_format,
        channels: receiver.channels,
        auto_start: receiver.auto_start
      });
    } else {
      setEditingReceiver(null);
      setFormData({
        name: '',
        multicast_address: '',
        port: 5004,
        interface: '',
        protocol: 'livewire_plus',
        audio_format: 'pcm_24',
        channels: 2,
        auto_start: false
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingReceiver(null);
  };

  const handleFormChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'success';
      case 'stopped': return 'default';
      case 'error': return 'error';
      case 'starting': return 'info';
      case 'stopping': return 'warning';
      default: return 'default';
    }
  };

  const formatAudioLevel = (level) => {
    if (typeof level !== 'number') return 0;
    return Math.max(0, Math.min(100, (level + 60) * (100 / 60))); // Convert dB to percentage
  };

  const getAudioLevelColor = (level) => {
    if (level > 90) return 'error';
    if (level > 75) return 'warning';
    return 'primary';
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Audio Receivers
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          disabled={loading}
        >
          Add Receiver
        </Button>
      </Box>

      {/* Receivers Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Address:Port</TableCell>
                  <TableCell>Protocol</TableCell>
                  <TableCell>Format</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Audio Level</TableCell>
                  <TableCell>Statistics</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {receivers.map((receiver) => {
                  const levels = audioLevels[receiver.id];
                  const avgLevel = levels ? 
                    (levels.left + levels.right) / 2 : 0;
                  const levelPercent = formatAudioLevel(avgLevel);
                  
                  return (
                    <TableRow key={receiver.id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <VolumeIcon sx={{ mr: 1, color: 'primary.main' }} />
                          <Typography variant="body2" fontWeight="medium">
                            {receiver.name}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {receiver.multicast_address}:{receiver.port}
                        </Typography>
                        {receiver.interface && (
                          <Typography variant="caption" color="textSecondary">
                            via {receiver.interface}
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={receiver.protocol.toUpperCase()} 
                          size="small" 
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {receiver.audio_format} ({receiver.channels}ch)
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={receiver.status.toUpperCase()} 
                          color={getStatusColor(receiver.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', minWidth: 120 }}>
                          <LinearProgress
                            variant="determinate"
                            value={levelPercent}
                            color={getAudioLevelColor(levelPercent)}
                            sx={{ 
                              width: 80, 
                              height: 6,
                              mr: 1,
                              backgroundColor: 'grey.300'
                            }}
                          />
                          <Typography variant="caption" sx={{ minWidth: 30 }}>
                            {levelPercent.toFixed(0)}%
                          </Typography>
                        </Box>
                        {levels && (
                          <Box sx={{ mt: 0.5 }}>
                            <Typography variant="caption" color="textSecondary">
                              L: {levels.left?.toFixed(1)}dB R: {levels.right?.toFixed(1)}dB
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                      <TableCell>
                        {receiver.stats && (
                          <Box>
                            <Typography variant="caption" display="block">
                              Packets: {receiver.stats.packets_received || 0}
                            </Typography>
                            <Typography variant="caption" display="block">
                              Dropped: {receiver.stats.packets_dropped || 0}
                            </Typography>
                            <Typography variant="caption" display="block">
                              Bitrate: {receiver.stats.bitrate_kbps || 0} kbps
                            </Typography>
                          </Box>
                        )}
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title={receiver.status === 'running' ? 'Stop' : 'Start'}>
                          <IconButton
                            color={receiver.status === 'running' ? 'error' : 'success'}
                            onClick={() => handleStartStop(receiver)}
                            disabled={loading}
                          >
                            {receiver.status === 'running' ? <StopIcon /> : <PlayIcon />}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton
                            color="primary"
                            onClick={() => handleOpenDialog(receiver)}
                            disabled={loading}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            color="error"
                            onClick={() => {
                              setReceiverToDelete(receiver);
                              setDeleteDialogOpen(true);
                            }}
                            disabled={loading}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {receivers.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography color="textSecondary">
                        No receivers configured. Click "Add Receiver" to get started.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingReceiver ? 'Edit Receiver' : 'Add New Receiver'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Receiver Name"
                value={formData.name}
                onChange={(e) => handleFormChange('name', e.target.value)}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Multicast Address"
                value={formData.multicast_address}
                onChange={(e) => handleFormChange('multicast_address', e.target.value)}
                placeholder="239.192.0.1"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Port"
                value={formData.port}
                onChange={(e) => handleFormChange('port', parseInt(e.target.value))}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Network Interface"
                value={formData.interface}
                onChange={(e) => handleFormChange('interface', e.target.value)}
                placeholder="eth0 (optional)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Protocol"
                value={formData.protocol}
                onChange={(e) => handleFormChange('protocol', e.target.value)}
              >
                <MenuItem value="livewire_plus">Livewire+</MenuItem>
                <MenuItem value="aes67">AES67</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Audio Format"
                value={formData.audio_format}
                onChange={(e) => handleFormChange('audio_format', e.target.value)}
              >
                <MenuItem value="pcm_16">PCM 16-bit</MenuItem>
                <MenuItem value="pcm_24">PCM 24-bit</MenuItem>
                <MenuItem value="opus">Opus</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Channels"
                value={formData.channels}
                onChange={(e) => handleFormChange('channels', parseInt(e.target.value))}
                inputProps={{ min: 1, max: 8 }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={loading || !formData.name || !formData.multicast_address}
          >
            {editingReceiver ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Receiver</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete receiver "{receiverToDelete?.name}"? 
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ReceiversPage;
