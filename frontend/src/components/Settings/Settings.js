import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Chip,
  Alert,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Snackbar
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  RestoreFromTrash as RestoreIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { apiService } from '../../services/apiService';

function Settings({ onShowNotification }) {
  const [config, setConfig] = useState({});
  const [loading, setLoading] = useState(false);
  const [saveDialog, setSaveDialog] = useState(false);
  const [restoreDialog, setRestoreDialog] = useState(false);
  const [importDialog, setImportDialog] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [originalConfig, setOriginalConfig] = useState({});

  useEffect(() => {
    loadConfiguration();
  }, []);

  const loadConfiguration = async () => {
    try {
      setLoading(true);
      const response = await apiService.getConfiguration();
      if (response.success) {
        setConfig(response.config);
        setOriginalConfig(JSON.parse(JSON.stringify(response.config)));
        setHasChanges(false);
      }
    } catch (error) {
      onShowNotification(`Failed to load configuration: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const saveConfiguration = async () => {
    try {
      setLoading(true);
      const response = await apiService.updateConfiguration(config);
      if (response.success) {
        setOriginalConfig(JSON.parse(JSON.stringify(config)));
        setHasChanges(false);
        onShowNotification('Configuration saved successfully', 'success');
        setSaveDialog(false);
      }
    } catch (error) {
      onShowNotification(`Failed to save configuration: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const restoreDefaults = async () => {
    try {
      setLoading(true);
      const response = await apiService.resetConfiguration();
      if (response.success) {
        setConfig(response.config);
        setOriginalConfig(JSON.parse(JSON.stringify(response.config)));
        setHasChanges(false);
        onShowNotification('Configuration restored to defaults', 'success');
        setRestoreDialog(false);
      }
    } catch (error) {
      onShowNotification(`Failed to restore defaults: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const exportConfiguration = () => {
    const dataStr = JSON.stringify(config, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `audionix-config-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    onShowNotification('Configuration exported successfully', 'success');
  };

  const importConfiguration = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importedConfig = JSON.parse(e.target.result);
          setConfig(importedConfig);
          setHasChanges(true);
          onShowNotification('Configuration imported successfully', 'success');
          setImportDialog(false);
        } catch (error) {
          onShowNotification('Failed to parse configuration file', 'error');
        }
      };
      reader.readAsText(file);
    }
  };

  const handleConfigChange = (path, value) => {
    const newConfig = { ...config };
    const keys = path.split('.');
    let current = newConfig;
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) current[keys[i]] = {};
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    setConfig(newConfig);
    setHasChanges(true);
  };

  const getConfigValue = (path) => {
    const keys = path.split('.');
    let current = config;
    
    for (const key of keys) {
      if (!current || typeof current !== 'object') return '';
      current = current[key];
    }
    
    return current || '';
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          System Settings
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadConfiguration}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Reload
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={() => setSaveDialog(true)}
            disabled={loading || !hasChanges}
            color="primary"
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      {/* Change Indicator */}
      {hasChanges && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          You have unsaved changes. Remember to save your configuration.
        </Alert>
      )}

      {/* Configuration Actions */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Configuration Management
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={exportConfiguration}
            >
              Export Config
            </Button>
            <Button
              variant="outlined"
              startIcon={<UploadIcon />}
              component="label"
            >
              Import Config
              <input
                type="file"
                accept=".json"
                hidden
                onChange={(e) => {
                  setImportDialog(true);
                  setTimeout(() => importConfiguration(e), 100);
                }}
              />
            </Button>
            <Button
              variant="outlined"
              startIcon={<RestoreIcon />}
              onClick={() => setRestoreDialog(true)}
              color="warning"
            >
              Restore Defaults
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Audio Settings */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Audio Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Sample Rate (Hz)"
                type="number"
                value={getConfigValue('audio.sample_rate')}
                onChange={(e) => handleConfigChange('audio.sample_rate', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Bit Depth"
                type="number"
                value={getConfigValue('audio.bit_depth')}
                onChange={(e) => handleConfigChange('audio.bit_depth', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Channels"
                type="number"
                value={getConfigValue('audio.channels')}
                onChange={(e) => handleConfigChange('audio.channels', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Buffer Size"
                type="number"
                value={getConfigValue('audio.buffer_size')}
                onChange={(e) => handleConfigChange('audio.buffer_size', parseInt(e.target.value))}
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Network Settings */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Network Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Default Interface"
                value={getConfigValue('network.default_interface')}
                onChange={(e) => handleConfigChange('network.default_interface', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Multicast TTL"
                type="number"
                value={getConfigValue('network.multicast_ttl')}
                onChange={(e) => handleConfigChange('network.multicast_ttl', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="RTP Port Range Start"
                type="number"
                value={getConfigValue('network.rtp_port_range.start')}
                onChange={(e) => handleConfigChange('network.rtp_port_range.start', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="RTP Port Range End"
                type="number"
                value={getConfigValue('network.rtp_port_range.end')}
                onChange={(e) => handleConfigChange('network.rtp_port_range.end', parseInt(e.target.value))}
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Protocol Settings */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Protocol Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={getConfigValue('protocols.livewire_plus.enabled')}
                    onChange={(e) => handleConfigChange('protocols.livewire_plus.enabled', e.target.checked)}
                  />
                }
                label="Enable Livewire+ Protocol"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={getConfigValue('protocols.aes67.enabled')}
                    onChange={(e) => handleConfigChange('protocols.aes67.enabled', e.target.checked)}
                  />
                }
                label="Enable AES67 Protocol"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Livewire+ Channel Base"
                type="number"
                value={getConfigValue('protocols.livewire_plus.channel_base')}
                onChange={(e) => handleConfigChange('protocols.livewire_plus.channel_base', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="AES67 Session Name"
                value={getConfigValue('protocols.aes67.session_name')}
                onChange={(e) => handleConfigChange('protocols.aes67.session_name', e.target.value)}
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Monitoring Settings */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Monitoring Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Update Interval (ms)"
                type="number"
                value={getConfigValue('monitoring.update_interval_ms')}
                onChange={(e) => handleConfigChange('monitoring.update_interval_ms', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="History Size"
                type="number"
                value={getConfigValue('monitoring.history_size')}
                onChange={(e) => handleConfigChange('monitoring.history_size', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={getConfigValue('monitoring.audio_levels')}
                    onChange={(e) => handleConfigChange('monitoring.audio_levels', e.target.checked)}
                  />
                }
                label="Enable Audio Level Monitoring"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={getConfigValue('monitoring.stream_stats')}
                    onChange={(e) => handleConfigChange('monitoring.stream_stats', e.target.checked)}
                  />
                }
                label="Enable Stream Statistics"
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Security Settings */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Security Settings</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={getConfigValue('security.authentication_required')}
                    onChange={(e) => handleConfigChange('security.authentication_required', e.target.checked)}
                  />
                }
                label="Require Authentication"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Session Timeout (minutes)"
                type="number"
                value={getConfigValue('security.session_timeout_minutes')}
                onChange={(e) => handleConfigChange('security.session_timeout_minutes', parseInt(e.target.value))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Maximum Login Attempts"
                type="number"
                value={getConfigValue('security.max_login_attempts')}
                onChange={(e) => handleConfigChange('security.max_login_attempts', parseInt(e.target.value))}
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Dialogs */}
      <Dialog open={saveDialog} onClose={() => setSaveDialog(false)}>
        <DialogTitle>Save Configuration</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to save the current configuration? This will update the system settings.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialog(false)}>Cancel</Button>
          <Button onClick={saveConfiguration} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={restoreDialog} onClose={() => setRestoreDialog(false)}>
        <DialogTitle>Restore Default Configuration</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to restore the default configuration? This will overwrite all current settings.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRestoreDialog(false)}>Cancel</Button>
          <Button onClick={restoreDefaults} variant="contained" color="warning">Restore</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Settings;
