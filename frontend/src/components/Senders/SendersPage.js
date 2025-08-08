import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Grid
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { apiService } from '../../services/apiService';

function SendersPage({ onShowNotification }) {
  const [senders, setSenders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSender, setEditingSender] = useState(null);
  const [senderForm, setSenderForm] = useState(apiService.getDefaultSenderConfig());

  useEffect(() => {
    loadSenders();
  }, []);

  const loadSenders = async () => {
    try {
      setLoading(true);
      const response = await apiService.getSenders();
      if (response.success) {
        setSenders(response.senders);
      }
    } catch (error) {
      onShowNotification(`Failed to load senders: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAddSender = () => {
    setEditingSender(null);
    setSenderForm(apiService.getDefaultSenderConfig());
    setDialogOpen(true);
  };

  const handleEditSender = (sender) => {
    setEditingSender(sender);
    setSenderForm(sender);
    setDialogOpen(true);
  };

  const handleSaveSender = async () => {
    try {
      const errors = apiService.validateSenderConfig(senderForm);
      if (errors.length > 0) {
        onShowNotification(`Validation errors: ${errors.join(', ')}`, 'error');
        return;
      }

      let response;
      if (editingSender) {
        response = await apiService.updateSender(editingSender.id, senderForm);
      } else {
        response = await apiService.createSender(senderForm);
      }

      if (response.success) {
        onShowNotification(
          `Sender ${editingSender ? 'updated' : 'created'} successfully`,
          'success'
        );
        setDialogOpen(false);
        loadSenders();
      }
    } catch (error) {
      onShowNotification(`Failed to save sender: ${error.message}`, 'error');
    }
  };

  const handleDeleteSender = async (senderId) => {
    if (!window.confirm('Are you sure you want to delete this sender?')) {
      return;
    }

    try {
      const response = await apiService.deleteSender(senderId);
      if (response.success) {
        onShowNotification('Sender deleted successfully', 'success');
        loadSenders();
      }
    } catch (error) {
      onShowNotification(`Failed to delete sender: ${error.message}`, 'error');
    }
  };

  const handleToggleSender = async (sender) => {
    try {
      let response;
      if (sender.active) {
        response = await apiService.stopSender(sender.id);
      } else {
        response = await apiService.startSender(sender.id);
      }

      if (response.success) {
        onShowNotification(
          `Sender ${sender.active ? 'stopped' : 'started'} successfully`,
          'success'
        );
        loadSenders();
      }
    } catch (error) {
      onShowNotification(`Failed to toggle sender: ${error.message}`, 'error');
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Audio Senders
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadSenders}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddSender}
          >
            Add Sender
          </Button>
        </Box>
      </Box>

      {/* Senders Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Input</TableCell>
              <TableCell>Output</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Codec</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {senders.map((sender) => (
              <TableRow key={sender.id}>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {sender.name}
                  </Typography>
                  {sender.description && (
                    <Typography variant="caption" color="textSecondary" display="block">
                      {sender.description}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {sender.input?.multicast_address}:{sender.input?.port}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {sender.output?.destination_address}:{sender.output?.destination_port}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={sender.active ? 'Active' : 'Inactive'}
                    color={sender.active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={sender.codec?.type?.toUpperCase() || 'PCM'}
                    variant="outlined"
                    size="small"
                  />
                </TableCell>
                <TableCell align="center">
                  <IconButton
                    size="small"
                    color={sender.active ? 'error' : 'success'}
                    onClick={() => handleToggleSender(sender)}
                    title={sender.active ? 'Stop' : 'Start'}
                  >
                    {sender.active ? <StopIcon /> : <PlayIcon />}
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleEditSender(sender)}
                    title="Edit"
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDeleteSender(sender.id)}
                    title="Delete"
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {senders.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="textSecondary">
                    No senders configured. Click "Add Sender" to create one.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingSender ? 'Edit Sender' : 'Add New Sender'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Name"
                value={senderForm.name}
                onChange={(e) => setSenderForm({ ...senderForm, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Description"
                value={senderForm.description}
                onChange={(e) => setSenderForm({ ...senderForm, description: e.target.value })}
              />
            </Grid>
            
            {/* Input Configuration */}
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
                Input Configuration
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Multicast Address"
                value={senderForm.input?.multicast_address || ''}
                onChange={(e) => setSenderForm({
                  ...senderForm,
                  input: { ...senderForm.input, multicast_address: e.target.value }
                })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Port"
                type="number"
                value={senderForm.input?.port || ''}
                onChange={(e) => setSenderForm({
                  ...senderForm,
                  input: { ...senderForm.input, port: parseInt(e.target.value) }
                })}
                required
              />
            </Grid>

            {/* Output Configuration */}
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
                Output Configuration
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Destination Address"
                value={senderForm.output?.destination_address || ''}
                onChange={(e) => setSenderForm({
                  ...senderForm,
                  output: { ...senderForm.output, destination_address: e.target.value }
                })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Destination Port"
                type="number"
                value={senderForm.output?.destination_port || ''}
                onChange={(e) => setSenderForm({
                  ...senderForm,
                  output: { ...senderForm.output, destination_port: parseInt(e.target.value) }
                })}
                required
              />
            </Grid>

            {/* Codec Configuration */}
            <Grid item xs={12}>
              <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
                Codec Configuration
              </Typography>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                label="Codec Type"
                value={senderForm.codec?.type || 'pcm'}
                onChange={(e) => setSenderForm({
                  ...senderForm,
                  codec: { ...senderForm.codec, type: e.target.value }
                })}
              >
                <MenuItem value="pcm">PCM (Uncompressed)</MenuItem>
                <MenuItem value="opus">Opus</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                label="Sample Rate"
                value={senderForm.codec?.sample_rate || 48000}
                onChange={(e) => setSenderForm({
                  ...senderForm,
                  codec: { ...senderForm.codec, sample_rate: parseInt(e.target.value) }
                })}
              >
                <MenuItem value={44100}>44.1 kHz</MenuItem>
                <MenuItem value={48000}>48 kHz</MenuItem>
                <MenuItem value={96000}>96 kHz</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                label="Bit Depth"
                value={senderForm.codec?.bit_depth || 24}
                onChange={(e) => setSenderForm({
                  ...senderForm,
                  codec: { ...senderForm.codec, bit_depth: parseInt(e.target.value) }
                })}
              >
                <MenuItem value={16}>16-bit</MenuItem>
                <MenuItem value={24}>24-bit</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveSender} variant="contained">
            {editingSender ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default SendersPage;
