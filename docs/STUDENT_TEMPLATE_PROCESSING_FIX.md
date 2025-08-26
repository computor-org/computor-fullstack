# Student Template Processing Complete Rewrite

## Overview
Complete rewrite of `process_example_for_student_template_v2` function to properly handle example content processing for student repositories.

## Content Processing Logic

### 1. Content Directory Processing
**All files from `content/` directory are processed:**

- **`index*.md` files** → Renamed to `README*.md`
  - `content/index.md` → `README.md`
  - `content/index_de.md` → `README_de.md`
  - `content/index_<lang>.md` → `README_<lang>.md`

- **All other files** → Copied preserving structure (minus `content/` prefix)
  - `content/mediaFiles/diagram.png` → `mediaFiles/diagram.png`
  - `content/resources/data.csv` → `resources/data.csv`
  - `content/any_file.txt` → `any_file.txt`

### 2. Additional Files Processing
- Files listed in `additionalFiles` are copied to assignment root
- Uses only the filename (not full path) for output

### 3. Student Submission Files Processing
**NEW APPROACH**: All `studentSubmissionFiles` MUST exist in assignment directory

**Logic**:
1. Build template content map from `studentTemplates`
2. For each file in `studentSubmissionFiles`:
   - If template exists → use template content
   - If no template → create empty file
3. ALL submission files are guaranteed to exist

## Example Processing

### Input Structure:
```
example/
  content/
    index.md
    index_de.md
    mediaFiles/
      diagram.png
      subfolder/
        image.jpg
    resources/
      data.csv
  studentTemplates/
    main.py
  helper.py (additionalFile)
  meta.yaml
```

### meta.yaml:
```yaml
properties:
  studentSubmissionFiles: [main.py, utils.py]
  additionalFiles: [helper.py]
  studentTemplates: [studentTemplates/main.py]
```

### Output (Assignment Directory):
```
assignment/
  README.md (from content/index.md)
  README_de.md (from content/index_de.md)
  mediaFiles/
    diagram.png
    subfolder/
      image.jpg
  resources/
    data.csv
  helper.py (from additionalFiles)
  main.py (from studentTemplates/main.py - has template content)
  utils.py (empty file - no template available)
```

## Key Improvements

### 1. Complete Content Processing
- No longer limited to just `mediaFiles`
- Everything in `content/` is processed appropriately
- Consistent file structure preservation

### 2. Flexible Template Resolution
```python
# Smart template file finding
if template_path in example_files:
    file_content = example_files[template_path]
else:
    # Search by filename with preference for 'studentTemplate' paths
    filename = Path(template_path).name
    for file_path, content in example_files.items():
        if Path(file_path).name == filename:
            if 'studentTemplate' in file_path:
                file_content = content
                break
```

### 3. Guaranteed File Creation
- ALL `studentSubmissionFiles` are created
- Template content used when available
- Empty files created when no template exists
- No files are skipped or missing

### 4. Better Logging
```python
logger.info(f"Created {submission_file} from template")
logger.info(f"Created empty file: {submission_file}")
```

## Process Flow

1. **Content Processing**: Process all `content/` directory files
2. **Additional Files**: Copy `additionalFiles` to root
3. **Template Mapping**: Build map of available template content
4. **Submission Files**: Create ALL `studentSubmissionFiles` (with template content or empty)

This ensures students receive:
- Complete content from examples (README, media, resources)
- Required submission files (with starter code when available)
- Proper file structure for assignment work