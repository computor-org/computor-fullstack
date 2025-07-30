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
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  FormHelperText,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  InsertDriveFile as FileIcon,
  Archive as ZipIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import * as yaml from 'js-yaml';

import { ExampleRepositoryGet, ExampleUploadRequest } from '../types/generated/examples';
import { apiClient } from '../services/apiClient';

const JSZip = require('jszip');

const uploadSchema = z.object({
  repository_id: z.string().min(1, 'Repository is required'),
  version_tag: z.string().min(1, 'Version tag is required'),
});

type UploadFormData = z.infer<typeof uploadSchema>;

interface FileUpload {
  name: string;
  content: string;
}

interface DetectedExample {
  directory: string;
  title: string;
  description?: string;
  slug: string;
  files: FileUpload[];
  metaYaml: string;
  testYaml?: string;
}

interface ExampleUploadDialogProps {
  open: boolean;
  repositories: ExampleRepositoryGet[];
  onClose: () => void;
  onSuccess: () => void;
}

const ExampleUploadDialog: React.FC<ExampleUploadDialogProps> = ({
  open,
  repositories,
  onClose,
  onSuccess,
}) => {
  const [detectedExamples, setDetectedExamples] = useState<DetectedExample[]>([]);
  const [selectedExamples, setSelectedExamples] = useState<Set<string>>(new Set());
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [zipProcessing, setZipProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ current: number; total: number } | null>(null);

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
      version_tag: 'v1.0',
    },
  });

  const selectedRepository = repositories.find(r => r.id === watch('repository_id'));

  // Auto-select first repository when dialog opens
  React.useEffect(() => {
    if (open && repositories.length > 0 && !watch('repository_id')) {
      setValue('repository_id', repositories[0].id);
    }
  }, [open, repositories, setValue, watch]);

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
    setZipProcessing(true);
    setError(null);
    
    try {
      const zip = new JSZip();
      const zipContent = await zipFile.arrayBuffer();
      const loadedZip = await zip.loadAsync(zipContent);

      // Find all directories that contain meta.yaml files
      const allPaths = Object.keys(loadedZip.files).filter(path => 
        !path.startsWith('__MACOSX/') && !path.includes('/.')
      );
      
      const metaYamlPaths = allPaths.filter(path => path.endsWith('meta.yaml'));
      
      if (metaYamlPaths.length === 0) {
        throw new Error('No meta.yaml files found in the ZIP archive. Please ensure your example directories contain meta.yaml files.');
      }

      const examples: DetectedExample[] = [];

      // Process each directory with meta.yaml
      for (const metaPath of metaYamlPaths) {
        try {
          // Get directory name from meta.yaml path
          const directoryPath = metaPath.replace('/meta.yaml', '');
          const directoryName = directoryPath.includes('/') ? 
            directoryPath.split('/').pop()! : directoryPath;

          // Read meta.yaml content
          const metaEntry = loadedZip.files[metaPath] as any;
          const metaContent = await metaEntry.async('string');
          const metaData = yaml.load(metaContent) as any;

          if (!metaData) {
            console.warn(`Failed to parse meta.yaml in ${directoryPath}`);
            continue;
          }

          // Find all files in this directory
          const directoryFiles: FileUpload[] = [];
          const directoryPrefix = directoryPath === directoryName ? directoryName + '/' : directoryPath + '/';

          for (const [filePath, zipEntry] of Object.entries(loadedZip.files)) {
            const entry = zipEntry as any;
            if (!entry.dir && filePath.startsWith(directoryPrefix) && 
                !filePath.startsWith('__MACOSX/') && !filePath.includes('/.')) {
              
              const relativePath = filePath.substring(directoryPrefix.length);
              
              // Skip meta.yaml and test.yaml as they're handled separately
              if (relativePath === 'meta.yaml' || relativePath === 'test.yaml') {
                continue;
              }

              // Only include supported file types
              if (isSupportedFile(relativePath)) {
                try {
                  const content = await entry.async('string');
                  directoryFiles.push({
                    name: relativePath,
                    content: content,
                  });
                } catch (err) {
                  console.warn(`Failed to extract ${filePath}:`, err);
                }
              }
            }
          }

          // Check for test.yaml
          let testYaml: string | undefined;
          const testYamlPath = directoryPrefix + 'test.yaml';
          if (loadedZip.files[testYamlPath]) {
            try {
              const testEntry = loadedZip.files[testYamlPath] as any;
              testYaml = await testEntry.async('string');
            } catch (err) {
              console.warn(`Failed to read test.yaml in ${directoryPath}`);
            }
          }

          // Create detected example
          examples.push({
            directory: directoryName,
            title: metaData.title || directoryName.replace(/[-_]/g, ' '),
            description: metaData.description,
            slug: metaData.slug || directoryName,
            files: directoryFiles,
            metaYaml: metaContent,
            testYaml: testYaml,
          });

        } catch (err) {
          console.warn(`Failed to process directory for ${metaPath}:`, err);
        }
      }

      if (examples.length === 0) {
        throw new Error('No valid examples found. Please ensure your directories contain proper meta.yaml files.');
      }

      setDetectedExamples(examples);
      
      // Auto-select all examples
      const allSlugs = new Set(examples.map(ex => ex.slug));
      setSelectedExamples(allSlugs);

    } catch (err) {
      throw err;
    } finally {
      setZipProcessing(false);
    }
  };

  const isSupportedFile = (fileName: string): boolean => {
    const supportedExtensions = ['.py', '.js', '.java', '.cpp', '.c', '.h', '.txt', '.md', '.yaml', '.yml', '.json'];
    return supportedExtensions.some(ext => fileName.toLowerCase().endsWith(ext));
  };

  const handleExampleToggle = (slug: string) => {
    const newSelected = new Set(selectedExamples);
    if (newSelected.has(slug)) {
      newSelected.delete(slug);
    } else {
      newSelected.add(slug);
    }
    setSelectedExamples(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedExamples.size === detectedExamples.length) {
      setSelectedExamples(new Set());
    } else {
      const allSlugs = new Set(detectedExamples.map(ex => ex.slug));
      setSelectedExamples(allSlugs);
    }
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

    if (detectedExamples.length === 0) {
      setError('No examples detected. Please upload a ZIP file with directories containing meta.yaml files.');
      return;
    }

    if (selectedExamples.size === 0) {
      setError('Please select at least one example to upload.');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadProgress({ current: 0, total: selectedExamples.size });

    try {
      const uploadPromises = [];
      const selectedExamplesList = detectedExamples.filter(ex => selectedExamples.has(ex.slug));
      let completedCount = 0;
      
      // Create upload promises with example information for better error tracking
      for (const example of selectedExamplesList) {
        // Convert files array to Record<string, string>
        const filesMap: Record<string, string> = {};
        for (const file of example.files) {
          filesMap[file.name] = file.content;
        }
        
        // Add meta.yaml and test.yaml
        filesMap['meta.yaml'] = example.metaYaml;
        if (example.testYaml) {
          filesMap['test.yaml'] = example.testYaml;
        }

        const uploadRequest: ExampleUploadRequest = {
          repository_id: data.repository_id,
          directory: example.directory,
          version_tag: data.version_tag,
          files: filesMap,
        };

        uploadPromises.push({
          example,
          promise: apiClient.post('/examples/upload', uploadRequest).then(result => {
            completedCount++;
            setUploadProgress({ current: completedCount, total: selectedExamplesList.length });
            return result;
          })
        });
      }

      // Wait for all uploads to complete with better error handling
      const results = await Promise.allSettled(uploadPromises.map(up => up.promise));
      
      // Check results and provide detailed feedback
      const successful = results.filter(r => r.status === 'fulfilled').length;
      const failed = results.filter(r => r.status === 'rejected').length;
      
      if (failed > 0) {
        // Collect error details
        const failedExamples = [];
        for (let i = 0; i < results.length; i++) {
          if (results[i].status === 'rejected') {
            const reason = (results[i] as PromiseRejectedResult).reason;
            failedExamples.push(`${uploadPromises[i].example.title}: ${reason.message || reason}`);
          }
        }
        
        if (successful > 0) {
          // Partial success
          setError(`Uploaded ${successful} of ${selectedExamplesList.length} examples. Failed: ${failedExamples.join('; ')}`);
        } else {
          // All failed
          throw new Error(`All uploads failed. ${failedExamples.join('; ')}`);
        }
      }
      
      console.log(`Successfully uploaded ${successful} examples`);

      // Reset form and close dialog only if at least some uploads succeeded
      if (successful > 0) {
        reset();
        setDetectedExamples([]);
        setSelectedExamples(new Set());
        onSuccess();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      reset();
      setDetectedExamples([]);
      setSelectedExamples(new Set());
      setError(null);
      setUploadProgress(null);
      onClose();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      slotProps={{
        paper: {
          sx: { height: '80vh' }
        }
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
                            {repo.source_type?.toUpperCase() || 'UNKNOWN'} • {repo.source_url}
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

            {/* Version Tag */}
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
              
              {zipProcessing && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2" gutterBottom>
                    Processing ZIP file...
                  </Typography>
                  <LinearProgress />
                </Box>
              )}
              
              {/* Detected Examples */}
              {detectedExamples.length > 0 && (
                <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="subtitle2">
                      Detected Examples ({detectedExamples.length})
                    </Typography>
                    <Button
                      size="small"
                      onClick={handleSelectAll}
                      disabled={uploading}
                    >
                      {selectedExamples.size === detectedExamples.length ? 'Deselect All' : 'Select All'}
                    </Button>
                  </Box>
                  
                  <List dense>
                    {detectedExamples.map((example, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemIcon>
                          <Checkbox
                            checked={selectedExamples.has(example.slug)}
                            onChange={() => handleExampleToggle(example.slug)}
                            disabled={uploading}
                          />
                        </ListItemIcon>
                        <ListItemIcon>
                          <FolderIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box>
                              <Typography variant="body2" component="span" sx={{ fontWeight: 'medium' }}>
                                {example.title}
                              </Typography>
                              <Chip 
                                label={example.directory} 
                                size="small" 
                                variant="outlined"
                                sx={{ ml: 1, fontFamily: 'monospace' }}
                              />
                            </Box>
                          }
                          secondary={
                            <Box sx={{ mt: 0.5 }}>
                              {example.description && (
                                <Typography variant="caption" color="text.secondary" display="block">
                                  {example.description}
                                </Typography>
                              )}
                              <Typography variant="caption" color="text.secondary">
                                {example.files.length} files • Slug: {example.slug}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              )}
            </Box>

            {/* Upload Progress */}
            {uploading && uploadProgress && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Uploading examples: {uploadProgress.current} of {uploadProgress.total}
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(uploadProgress.current / uploadProgress.total) * 100} 
                />
              </Box>
            )}

            {/* Instructions */}
            <Alert severity="info">
              <Typography variant="body2">
                <strong>Automatic Detection:</strong> Upload a ZIP archive containing one or more example directories.
                <br />
                <strong>Required:</strong> Each example directory must contain a <code>meta.yaml</code> file with metadata.
                <br />
                <strong>Optional:</strong> Include a <code>test.yaml</code> file for automated testing.
                <br />
                <strong>Supported Files:</strong> .py, .js, .java, .cpp, .c, .h, .txt, .md, .yaml, .yml, .json
                <br />
                The system will automatically detect all examples and let you choose which ones to upload.
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
            disabled={uploading || !selectedRepository || selectedRepository.source_type === 'git' || selectedExamples.size === 0}
            startIcon={<ZipIcon />}
          >
            {uploading 
              ? `Uploading ${selectedExamples.size} example${selectedExamples.size === 1 ? '' : 's'}...` 
              : `Upload ${selectedExamples.size} Example${selectedExamples.size === 1 ? '' : 's'}`
            }
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default ExampleUploadDialog;