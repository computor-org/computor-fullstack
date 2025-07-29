import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Paper,
  IconButton,
  Alert,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  InsertDriveFile as FileIcon,
  Archive as ZipIcon,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import * as yaml from 'js-yaml';

import { ExampleRepository, ExampleUploadRequest } from '../types/examples';
import { apiClient } from '../services/apiClient';

const JSZip = require('jszip');

const uploadSchema = z.object({
  repository_id: z.string().min(1, 'Repository is required'),
  directory: z.string()
    .min(1, 'Directory is required')
    .regex(/^[a-zA-Z0-9._-]+$/, 'Directory must contain only letters, numbers, dots, underscores, and hyphens'),
  version_tag: z.string().min(1, 'Version tag is required'),
});

type UploadFormData = z.infer<typeof uploadSchema>;

interface FileUpload {
  name: string;
  content: string;
}

interface ExampleUploadDialogProps {
  open: boolean;
  repositories: ExampleRepository[];
  onClose: () => void;
  onSuccess: () => void;
}

const ExampleUploadDialog: React.FC<ExampleUploadDialogProps> = ({
  open,
  repositories,
  onClose,
  onSuccess,
}) => {
  const [files, setFiles] = useState<FileUpload[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [directoryAutoDetected, setDirectoryAutoDetected] = useState(false);

  const {
    control,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors },
  } = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema),
    defaultValues: {
      repository_id: '',
      directory: '',
      version_tag: 'v1.0',
    },
  });

  const selectedRepository = repositories.find(r => r.id === watch('repository_id'));

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = event.target.files;
    if (!uploadedFiles) return;

    setError(null);

    const file = uploadedFiles[0]; // Only handle single zip file
    if (!file) return;

    try {
      if (!file.name.endsWith('.zip')) {
        throw new Error('Only ZIP files are supported. Please zip your example directory first.');
      }
      
      await handleZipFile(file);
    } catch (err) {
      setError(`Failed to process ${file.name}: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleZipFile = async (zipFile: File) => {
    const zip = new JSZip();
    const zipContent = await zipFile.arrayBuffer();
    const loadedZip = await zip.loadAsync(zipContent);

    const extractedFiles: FileUpload[] = [];
    let detectedDirectory: string | null = null;

    // First pass: detect directory structure and common root
    const allPaths = Object.keys(loadedZip.files).filter(path => !path.startsWith('__MACOSX/') && !path.includes('/.'));
    
    if (allPaths.length > 0) {
      // Check if all files are in a common directory
      const firstPath = allPaths[0];
      if (firstPath.includes('/')) {
        const possibleRoot = firstPath.split('/')[0];
        const allInSameRoot = allPaths.every(path => path.startsWith(possibleRoot + '/') || path === possibleRoot);
        
        if (allInSameRoot) {
          detectedDirectory = possibleRoot;
        }
      }
      
      // If no common root, try to extract from filename or meta.yaml
      if (!detectedDirectory) {
        // Check if there's a meta.yaml with slug
        const metaPath = allPaths.find(path => path.endsWith('meta.yaml'));
        if (metaPath) {
          try {
            const metaEntry = loadedZip.files[metaPath] as any;
            const metaContent = await metaEntry.async('string');
            const metaData = yaml.load ? yaml.load(metaContent) as any : null;
            if (metaData && metaData.slug) {
              detectedDirectory = metaData.slug;
            }
          } catch (err) {
            console.warn('Failed to parse meta.yaml for directory detection');
          }
        }
      }
      
      // Fallback: use zip filename without extension
      if (!detectedDirectory) {
        detectedDirectory = zipFile.name.replace(/\.zip$/i, '');
      }
    }

    // Second pass: extract files
    for (const [relativePath, zipEntry] of Object.entries(loadedZip.files)) {
      const entry = zipEntry as any;
      if (!entry.dir && !relativePath.startsWith('__MACOSX/') && !relativePath.includes('/.')) {
        try {
          const content = await entry.async('string');
          let fileName = relativePath;
          
          // Remove common directory prefix if detected
          if (detectedDirectory && relativePath.startsWith(detectedDirectory + '/')) {
            fileName = relativePath.substring(detectedDirectory.length + 1);
          }
          
          // Only include supported file types
          if (isSupportedFile(fileName)) {
            extractedFiles.push({
              name: fileName,
              content: content,
            });
          }
        } catch (err) {
          console.warn(`Failed to extract ${relativePath}:`, err);
        }
      }
    }

    if (extractedFiles.length === 0) {
      throw new Error('No supported files found in zip archive');
    }

    // Auto-populate directory field if detected
    if (detectedDirectory) {
      setValue('directory', detectedDirectory);
      setDirectoryAutoDetected(true);
    }

    // Replace existing files with extracted ones
    setFiles(prev => {
      const newFiles = [...prev];
      extractedFiles.forEach(newFile => {
        const existingIndex = newFiles.findIndex(f => f.name === newFile.name);
        if (existingIndex >= 0) {
          newFiles[existingIndex] = newFile;
        } else {
          newFiles.push(newFile);
        }
      });
      return newFiles;
    });
  };

  const isSupportedFile = (fileName: string): boolean => {
    const supportedExtensions = ['.py', '.js', '.java', '.cpp', '.c', '.h', '.txt', '.md', '.yaml', '.yml', '.json'];
    return supportedExtensions.some(ext => fileName.toLowerCase().endsWith(ext));
  };

  const handleRemoveFile = (fileName: string) => {
    setFiles(files.filter(f => f.name !== fileName));
  };

  const onSubmit = async (data: UploadFormData) => {
    if (!selectedRepository) {
      setError('Please select a repository');
      return;
    }

    if (selectedRepository.source_type === 'git') {
      setError('Git repositories do not support direct upload. Use git push instead.');
      return;
    }

    // Validate that meta.yaml is included
    if (!files.some(f => f.name === 'meta.yaml')) {
      setError('meta.yaml file is required');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Convert files array to Record<string, string>
      const filesMap = files.reduce((acc, file) => {
        acc[file.name] = file.content;
        return acc;
      }, {} as Record<string, string>);

      const uploadRequest: ExampleUploadRequest = {
        repository_id: data.repository_id,
        directory: data.directory,
        version_tag: data.version_tag,
        files: filesMap,
      };

      // Make actual API call to upload example
      const result = await apiClient.post('/examples/upload', uploadRequest);
      console.log('Upload successful:', result);

      // Reset form and close dialog
      reset();
      setFiles([]);
      setDirectoryAutoDetected(false);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      reset();
      setFiles([]);
      setError(null);
      setDirectoryAutoDetected(false);
      onClose();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <DialogTitle>
          Upload Example Directory
        </DialogTitle>
        
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Error Alert */}
            {error && (
              <Alert severity="error" onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {/* Upload Progress */}
            {uploading && (
              <Box>
                <Typography variant="body2" gutterBottom>
                  Uploading example...
                </Typography>
                <LinearProgress />
              </Box>
            )}

            {/* Repository Selection */}
            <Controller
              name="repository_id"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.repository_id}>
                  <InputLabel>Repository</InputLabel>
                  <Select {...field} label="Repository" disabled={uploading}>
                    {repositories.filter(r => r.source_type !== 'git').map((repo) => (
                      <MenuItem key={repo.id} value={repo.id}>
                        <Box>
                          <Typography variant="body1">{repo.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {repo.source_type.toUpperCase()} • {repo.source_url}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                  {errors.repository_id && (
                    <Typography variant="caption" color="error">
                      {errors.repository_id.message}
                    </Typography>
                  )}
                </FormControl>
              )}
            />

            {/* Directory and Version */}
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Controller
                name="directory"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Directory"
                    fullWidth
                    error={!!errors.directory}
                    helperText={
                      directoryAutoDetected 
                        ? "Auto-detected from ZIP structure" 
                        : errors.directory?.message || "Directory name for this example"
                    }
                    placeholder="hello-world"
                    disabled={uploading}
                    InputProps={{
                      style: directoryAutoDetected ? { backgroundColor: '#f5f5f5' } : {}
                    }}
                  />
                )}
              />

              <Controller
                name="version_tag"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Version Tag"
                    fullWidth
                    error={!!errors.version_tag}
                    helperText={errors.version_tag?.message}
                    placeholder="v1.0"
                    disabled={uploading}
                  />
                )}
              />
            </Box>

            {/* Zip File Upload */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Example Directory (ZIP Archive)
              </Typography>
              <Button
                variant="contained"
                component="label"
                startIcon={<ZipIcon />}
                disabled={uploading}
                sx={{ mb: 1 }}
              >
                Select ZIP File
                <input
                  type="file"
                  hidden
                  onChange={handleFileUpload}
                  accept=".zip"
                />
              </Button>
              
              {files.length > 0 && (
                <Paper variant="outlined" sx={{ p: 1, maxHeight: 150, overflow: 'auto' }}>
                  {files.map((file, index) => (
                    <Box
                      key={index}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        py: 0.5,
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <FileIcon fontSize="small" />
                        <Typography variant="body2">{file.name}</Typography>
                        <Chip 
                          label={`${file.content.length} chars`} 
                          size="small" 
                          variant="outlined"
                        />
                      </Box>
                      <IconButton
                        size="small"
                        onClick={() => handleRemoveFile(file.name)}
                        disabled={uploading}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  ))}
                </Paper>
              )}
            </Box>

            {/* Instructions */}
            <Alert severity="info">
              <Typography variant="body2">
                <strong>Directory Upload:</strong> Create a ZIP archive of your complete example directory.
                <br />
                <strong>Required:</strong> Your ZIP must contain a <code>meta.yaml</code> file with example metadata.
                <br />
                <strong>Optional:</strong> Include a <code>test.yaml</code> file for automated testing.
                <br />
                <strong>Supported Files:</strong> .py, .js, .java, .cpp, .c, .h, .txt, .md, .yaml, .yml, .json
                <br />
                The system will automatically extract and parse your example files.
              </Typography>
            </Alert>
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose} disabled={uploading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={uploading || !selectedRepository || selectedRepository.source_type === 'git'}
            startIcon={<ZipIcon />}
          >
            {uploading ? 'Uploading...' : 'Upload Directory'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default ExampleUploadDialog;