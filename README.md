# HadCM3B Land Carbon Cycle Ensemble Generator

This repository contains scripts and workflows to automatically generate ensembles of HadCM3B climate model jobs with perturbed land carbon cycle parameters. The goal is to run hundreds of simulations with different parameter sets to identify optimal configurations for the new HadCM3BL version with a fully coupled carbon cycle.

**Created by**: Sebastian Steinig
**Institution**: University of Bristol
**Purpose**: Land carbon cycle parameter tuning and sensitivity analysis

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Workflow Options](#workflow-options)
- [Parameter Perturbation Logic](#parameter-perturbation-logic)
- [Complete Workflow Guide](#complete-workflow-guide)
- [Scripts Reference](#scripts-reference)
- [File Organization](#file-organization)
- [Troubleshooting](#troubleshooting)
- [Quick Reference Commands](#quick-reference-commands)

---

## Overview

### What This Does

1. **Generates parameter sets** for land carbon cycle tuning (random, single-parameter, or from candidates)
2. **Creates ensemble jobs** by duplicating a vanilla template job
3. **Applies parameters** to job namelists automatically
4. **Manages job submission** and monitoring on BC4 cluster
5. **Handles storage** on BRIDGE partition to avoid disk quota issues

### Key Features

- ✅ **Automated**: Single command can generate and submit hundreds of jobs
- ✅ **Flexible**: Supports random exploration, targeted tuning, or candidate refinement
- ✅ **Scalable**: Handles up to 260 ensemble members per experiment
- ✅ **Safe**: Validates prerequisites and creates backups
- ✅ **Documented**: Comprehensive guides and troubleshooting

---

## Quick Start

### Prerequisites

- Access to PUMA2 (via ARCHER2) for UMUI
- Access to BC4 cluster
- BRIDGE storage access (`/mnt/storage/private/bridge`)
- Python 3.x (available on BC4)

### Basic Workflow

```bash
# 1. Clone repository (on BC4)
cd ~
git clone <repo-url> hadcm3b-ensemble-generator
cd hadcm3b-ensemble-generator

# 2. Create vanilla job in UMUI (see detailed guide below)
# ... UMUI setup on PUMA2 ...

# 3. Transfer and compile vanilla job
rsync -avz -e 'ssh -J <user>@login.archer2.ac.uk' \
  <user>@puma2:~/umui_jobs/<JOBID> vanilla_jobs/
clustersubmit -s y -r bc4 vanilla_jobs/<JOBID>

# 4. Generate parameter sets (choose one method)
python create_param_table_random.py     # Random exploration
# OR
python create_param_table_single.py     # Single-parameter tuning
# OR
python convert_csv_to_param_table.py    # From CSV candidates

# 5. Run complete workflow (automated)
./run_full_ensemble_workflow.sh <ensemble_name> <vanilla_job_id>

# 6. Monitor jobs
qstat -u $USER
```

---

## Workflow Options

### Option 1: Random Parameter Exploration

**Use case**: Initial sensitivity analysis, broad parameter space exploration

**Script**: `create_param_table_random.py`

```python
# Configuration
ensemble_name = "xqau"
N = 256  # Number of ensemble members

# Define parameter ranges (min, max)
perturbed_BL_params = {
    "ALPHA": [0.04, 0.16],
    "G_AREA": [0.002, 0.008],
    "LAI_MIN": [2.0, 4.0],
    "NL0": [0.040, 0.065],
    "R_GROW": [0.15, 0.30],
    "TLOW": [-5.0, 5.0],
    "V_CRIT_ALPHA": [0.3, 1.0],
}
```

**Output**: 256 random parameter sets, each varying ALL parameters simultaneously

**Run**:
```bash
python create_param_table_random.py
# Creates: param_tables/xqau.json + xqau_param_distributions.pdf
```

---

### Option 2: Single-Parameter Sensitivity

**Use case**: Understanding individual parameter impacts, one-at-a-time analysis

**Script**: `create_param_table_single.py`

```python
# Configuration
ensemble_name = "test_single_param_tuning"

# Define discrete values for each parameter
perturbed_BL_params = {
    "F0": [0.8, 0.85, 0.90, 0.95],
    "LAI_MIN": [1.0, 2.0, 3.0, 4.0],
    "NL0": [0.035, 0.045, 0.055, 0.065],
    "R_GROW": [0.150, 0.185, 0.22, 0.30],
    "TLOW": [-5.0, -2.5, 2.5, 5.0],
    "V_CRIT_ALPHA": [0.0, 0.25, 0.5, 0.75, 1.0],
}
```

**Output**: ~20-30 parameter sets (sum of discrete values), varying ONE parameter at a time

**Run**:
```bash
python create_param_table_single.py
# Creates: param_tables/test_single_param_tuning.json + PDF
```

---

### Option 3: Soil Carbon Refinement

**Use case**: Refining promising candidates by tuning soil parameters (Q10, KAPS)

**Script**: `create_param_table_csoil_from_candidates.py`

```python
# Configuration
ensemble_name = "xqac_csoil"
default_params_file = "./input_params/top_random_candidates_parameters.json"
N = 50  # Variations per candidate

# Soil parameter ranges
perturbed_BL_params = {
    "Q10": [1.5, 2.5],
    "KAPS": [2.5e-009, 7.5e-009],
}
```

**Input**: JSON file with previous "good" candidates (from validation analysis)

**Output**: N perturbed variations for each input candidate

**Run**:
```bash
python create_param_table_csoil_from_candidates.py
# Creates: param_tables/xqac_csoil.json + PDF
```

---

### Option 4: From CSV Candidates (NEW)

**Use case**: Running specific BL parameter sets (e.g., literature values, expert choices)

**Step 1: Create CSV file**

```csv
candidate_id,ALPHA,G_AREA,F0,LAI_MIN,NL0,R_GROW,TLOW,V_CRIT_ALPHA
candidate_1,0.10,0.005,0.880,3.5,0.055,0.20,2.5,0.5
candidate_2,0.08,0.004,0.875,4.0,0.050,0.25,0.0,0.343
candidate_3,0.12,0.006,0.890,3.0,0.060,0.18,-2.5,0.7
```

**Important**:
- `TLOW`: Enter as **delta** values (e.g., 2.5 = shift by +2.5°C)
- All other parameters: **absolute BL values**

**Step 2: Convert to parameter table**

```bash
python convert_csv_to_param_table.py \
  --csv_file input_params/my_candidates.csv \
  --ensemble_name xqabc
```

**Output**: Full PFT parameter arrays for each candidate

**Template**: `input_params/bl_candidates_template.csv`

---

## Parameter Perturbation Logic

All scripts use **consistent transformation rules** to convert Broadleaf (BL) parameter values to full 5-element Plant Functional Type (PFT) arrays:

### PFT Array Structure

```
[BL, NL, C3_grass, C4_grass, Shrub]
[0]  [1]  [2]       [3]       [4]
```

### Transformation Rules

| Parameter Type | Rule | Example |
|----------------|------|---------|
| **ALPHA, G_AREA, F0, NL0** | **Pro-rata**: Calculate δ = new_BL - default_BL, apply to all PFTs | new_BL=0.10, default_BL=0.08 → δ=0.02 → [0.10, 0.10, 0.10, 0.07, 0.10] |
| **LAI_MIN** | **Trees only**: Apply to indices 0-1, keep grass/shrubs at 1.0 | new_BL=3.5 → [3.5, 3.5, 1.0, 1.0, 1.0] |
| **R_GROW, V_CRIT_ALPHA, Q10, KAPS** | **Uniform**: Apply same value to all PFTs | new_value=0.20 → [0.20, 0.20, 0.20, 0.20, 0.20] |
| **TLOW & TUPP** | **Co-varying deltas**: Add delta to all PFT defaults (auto-adjusts TUPP when TLOW changes) | delta=+2.5 → TLOW=[2.5, -2.5, 2.5, 15.5, 2.5] |

### Default Parameters

From "acang" (MetOffice C4MIP run, 2006):

```python
default_params = {
    "ALPHA": [0.08, 0.08, 0.08, 0.05, 0.08],      # Quantum efficiency
    "G_AREA": [0.004, 0.004, 0.10, 0.10, 0.05],   # Leaf growth rate
    "F0": [0.875, 0.875, 0.900, 0.800, 0.900],    # Dark respiration
    "LAI_MIN": [4.0, 4.0, 1.0, 1.0, 1.0],         # Minimum LAI
    "NL0": [0.050, 0.030, 0.060, 0.030, 0.030],   # Top leaf nitrogen
    "R_GROW": [0.25, 0.25, 0.25, 0.25, 0.25],     # Growth respiration
    "TLOW": [0.0, -5.0, 0.0, 13.0, 0.0],          # Lower temperature
    "TUPP": [36.0, 31.0, 36.0, 45.0, 36.0],       # Upper temperature
    "V_CRIT_ALPHA": [0.343],                       # Critical LAI
}
```

### Reverse Operation: BL Expansion

**Script**: `expand_bl_to_pfts.py`

Convert BL values back to full PFT arrays:

```python
from expand_bl_to_pfts import expand_bl_params_to_pfts

bl_params = {
    "ALPHA": 0.10,
    "NL0": 0.055,
    "R_GROW": 0.20,
}

full_params = expand_bl_params_to_pfts(bl_params)
# Returns: Full 5-element arrays for all parameters
```

---

## Complete Workflow Guide

### Phase 1: Vanilla Job Setup (One-Time)

#### Step 1: Create Vanilla Job in UMUI (PUMA2)

```bash
# Connect to PUMA2
ssh <username>@login.archer2.ac.uk
ssh puma2
umui
```

**In UMUI Interface:**

1. **Create new experiment**
   - File → New
   - Set experiment ID (e.g., `xqaba`)
   - Configure run length, restart files, output fields

2. **CRITICAL: Add land carbon cycle modifications**
   - Navigate to: `Model Selection` → `Modifications`
   - Add: `/user/home/wb19586/um_updates/znamelist_hadcm3m21_land_cc_v2.mod`
   - Add post-processing script: `~ssteinig/scripts/land_cc_v2`

3. **Process job**
   - Click: `Processing` → `Process`
   - Job created in: `~/umui_jobs/<JOBID>`

**Why this matters**: The mod enables reading parameters from `CNTLATM` namelist instead of hardcoded values.

#### Step 2: Transfer to BC4

```bash
# From BC4
rsync -avz -e 'ssh -J <username>@login.archer2.ac.uk' \
  <username>@puma2:~/umui_jobs/<JOBID> \
  ~/hadcm3b-ensemble-generator/vanilla_jobs/
```

#### Step 3: Compile Vanilla Job

```bash
cd ~/hadcm3b-ensemble-generator

# Submit compilation
clustersubmit -s y -r bc4 vanilla_jobs/<JOBID>

# Monitor: qstat -u $USER
# Wait ~10-30 minutes
```

#### Step 4: Configure Shared Executable

```bash
# Create directory
mkdir -p ~/executables

# Move executable
cp ~/umui_runs/<JOBID>/bin/<JOBID>.exe ~/executables/

# Update SCRIPT file
nano vanilla_jobs/<JOBID>/SCRIPT
# Change: LOADMODULE=/user/home/$USER/executables/<JOBID>.exe
```

**Why this matters**: All ensemble members share one executable, saving compilation time and disk space.

---

### Phase 2: Generate Parameter Sets

Choose one method from [Workflow Options](#workflow-options) above.

**Common outputs**:
- `param_tables/<ensemble_name>.json` - Parameter sets
- `param_tables/<ensemble_name>_param_distributions.pdf` - Visualizations

**Verify output**:
```bash
# Check parameter file
head -30 param_tables/<ensemble_name>.json

# Count ensemble members
grep -c '"ALPHA"' param_tables/<ensemble_name>.json

# View distributions
open param_tables/<ensemble_name>_param_distributions.pdf
```

---

### Phase 3: Generate and Submit Ensemble Jobs

#### Option A: Automated Workflow (Recommended)

```bash
cd ~/hadcm3b-ensemble-generator

./run_full_ensemble_workflow.sh <ensemble_name> <vanilla_job_id>

# Example:
./run_full_ensemble_workflow.sh xqabc xqaba
```

**Interactive prompts**:
1. Validates prerequisites
2. Generates ensemble jobs
3. Creates storage directories
4. Asks: Submit now / Create script / Exit

**Outputs**:
- Jobs in: `~/umui_jobs/<ensemble_name>a`, `<ensemble_name>b`, ...
- Logs in: `logs/<ensemble_name>_generated_ids_<date>.log`

---

#### Option B: Manual Step-by-Step

**Step 1: Generate Jobs**

```bash
python create_ensemble_jobs.py \
  --vanilla_job vanilla_jobs/<JOBID> \
  --parameter_file param_tables/<ensemble_name>.json \
  --ensemble_exp <ensemble_name>
```

**What this does**:
1. Reads parameter JSON file
2. For each parameter set:
   - Generates unique job ID (e.g., `xqabca`, `xqabcb`, ...)
   - Duplicates vanilla job directory
   - Updates `CNTLATM` namelist with new parameters using `sed`
   - Logs job ID and parameters

**Step 2: Create Storage Directories**

```bash
LOGFILE="logs/<ensemble_name>_generated_ids_$(date +%Y%m%d).log"

while IFS= read -r job_id; do
    # Create on BRIDGE partition (large storage)
    mkdir -p "/mnt/storage/private/bridge/um_output/$USER/$job_id"

    # Create symlink in dump2hold (standard I/O location)
    ln -s "/mnt/storage/private/bridge/um_output/$USER/$job_id" \
          "/user/home/$USER/dump2hold/$job_id"
done < "$LOGFILE"
```

**Why this matters**: BC4 home directories have strict quotas; BRIDGE partition provides large storage.

**Step 3: Submit Jobs**

```bash
while IFS= read -r job_id; do
    clustersubmit -s y -c n -a y -r bc4 -q cpu -w 12:00:00 "$job_id"
done < "$LOGFILE"
```

**Options explained**:
- `-s y`: Submit to queue
- `-c n`: Continue from restart = NO (fresh run)
- `-a y`: Archive outputs
- `-r bc4`: BC4 cluster
- `-q cpu`: CPU queue
- `-w 12:00:00`: 12-hour walltime

---

### Phase 4: Monitor and Manage

#### Check Job Status

```bash
# All your jobs
qstat -u $USER

# Specific job details
qstat -f <JOBID>

# Check output generation
LOGFILE="logs/<ensemble>_generated_ids_<date>.log"
while IFS= read -r job_id; do
    DATA_DIR="/user/home/$USER/dump2hold/$job_id/datam"
    if [ -n "$(ls -A $DATA_DIR 2>/dev/null)" ]; then
        echo "✓ $job_id: Running/Complete"
    else
        echo "✗ $job_id: No output yet"
    fi
done < "$LOGFILE"
```

#### Continue Failed/Incomplete Jobs

```bash
# Edit script
nano continue_all_jobs.sh
# Update: logfile="./logs/<ensemble>_generated_ids_YYYYMMDD.log"

# Run continuation
./continue_all_jobs.sh
```

**Note**: Uses `-c y` flag (continue from restart files)

#### Clean Up Large Files

```bash
# Edit script
nano clean_all_jobs.sh
# Update logfile path

# Run cleanup
./clean_all_jobs.sh
```

**What this does**:
- Removes partial dump files (`*p[abcdf]00*`)
- Keeps only 20 most recent atmosphere dumps (`*da00*`)

---

### Phase 5: Post-Processing

Once jobs finish, transfer to BRIDGE servers for validation:

```bash
# On BRIDGE server
cd ~/hadcm3b-ensemble-validator

# Process results, generate validation plots, identify best candidates
# See: https://github.com/sebsteinig/hadcm3b-ensemble-validator
```

---

## Scripts Reference

### Core Scripts

| Script | Purpose | Inputs | Outputs |
|--------|---------|--------|---------|
| `create_param_table_random.py` | Generate random parameter sets | Ensemble name, N, param ranges | JSON + PDF |
| `create_param_table_single.py` | One-at-a-time sensitivity | Ensemble name, discrete values | JSON + PDF |
| `create_param_table_csoil_from_candidates.py` | Soil carbon refinement | Candidate JSON, N, soil ranges | JSON + PDF |
| `convert_csv_to_param_table.py` | CSV to parameter table | CSV file, ensemble name | JSON |
| `create_ensemble_jobs.py` | Generate ensemble jobs | Vanilla job, param JSON, ensemble name | Job directories + logs |
| `expand_bl_to_pfts.py` | BL to full PFT expansion | BL parameter dict | Full PFT arrays |

### Workflow Scripts

| Script | Purpose |
|--------|---------|
| `run_full_ensemble_workflow.sh` | Automated end-to-end workflow |
| `create_job_dirs.sh` | Create BRIDGE storage + symlinks |
| `submit_all_jobs.sh` | Submit all ensemble jobs |
| `check_all_jobs.sh` | Check status, resubmit failed |
| `continue_all_jobs.sh` | Continue from restart files |
| `clean_all_jobs.sh` | Clean up partial/old dumps |
| `create_ensemble_runs.sh` | Alternative submission using create_ensemble |

### Helper Functions

**File**: `helpers.py`

| Function | Purpose |
|----------|---------|
| `generate_ensemble_jobid()` | Generate unique job IDs (supports 260 variations) |
| `duplicate_job()` | Copy vanilla job, update all references |
| `setup_logging()` | Configure logging for job generation |
| `create_json_file()` | Format and save parameter JSON |
| `plot_param_distributions()` | Create distribution PDFs |

---

## File Organization

```
hadcm3b-ensemble-generator/
├── README.md                              # This file
├── WORKFLOW_BL_CANDIDATES.md              # Detailed guide for CSV workflow
├── Codes_explanation.md                   # Code documentation
│
├── Core Parameter Generation Scripts
├── create_param_table_random.py           # Random exploration
├── create_param_table_single.py           # Single-parameter tuning
├── create_param_table_csoil_from_candidates.py  # Soil refinement
├── convert_csv_to_param_table.py          # CSV converter (NEW)
├── expand_bl_to_pfts.py                   # BL expansion utility (NEW)
│
├── Job Management Scripts
├── create_ensemble_jobs.py                # Generate ensemble jobs
├── run_full_ensemble_workflow.sh          # Automated workflow (NEW)
├── create_job_dirs.sh                     # Storage setup
├── submit_all_jobs.sh                     # Submit jobs
├── check_all_jobs.sh                      # Monitor status
├── continue_all_jobs.sh                   # Continue runs
├── clean_all_jobs.sh                      # Cleanup
├── create_ensemble_runs.sh                # Alternative submission
│
├── helpers.py                             # Core utilities
│
├── Input Data
├── input_params/
│   ├── bl_candidates_template.csv         # CSV template (NEW)
│   ├── TOP20_LAND_CC_params_for_benchmarking.json
│   └── top_random_candidates_parameters.json
│
├── Generated Data
├── param_tables/                          # Generated parameter sets
│   ├── <ensemble_name>.json
│   └── <ensemble_name>_param_distributions.pdf
│
├── logs/                                  # Execution logs
│   ├── <ensemble>_generated_ids_<date>.log
│   ├── <ensemble>_updated_parameters_<date>.json
│   └── <ensemble>_ensemble_jobs_generator_<date>.log
│
└── vanilla_jobs/                          # Template jobs
    ├── xpzna/
    ├── xqaba/
    ├── xqaca/
    └── xqapa/

~/umui_jobs/                               # Generated ensemble jobs
├── <vanilla_job>/                         # Template
├── <ensemble>a/                           # Member 0 (default params)
├── <ensemble>b/                           # Member 1
└── ...

/mnt/storage/private/bridge/um_output/$USER/  # Actual job output
├── <ensemble>a/
├── <ensemble>b/
└── ...

/user/home/$USER/dump2hold/                # Symlinks to BRIDGE storage
├── <ensemble>a -> /mnt/.../
├── <ensemble>b -> /mnt/.../
└── ...
```

---

## Troubleshooting

### Problem: "Key not found in CNTLATM"

**Symptoms**: Job generation warns about missing parameters

**Solution**:
```bash
# Check vanilla job has land carbon cycle mod
grep "ALPHA=" vanilla_jobs/<JOBID>/CNTLATM

# Should show: ALPHA=0.08,0.08,0.08,0.05,0.08
# If missing, recreate vanilla job in UMUI with proper mod:
# /user/home/wb19586/um_updates/znamelist_hadcm3m21_land_cc_v2.mod
```

---

### Problem: Jobs fail immediately after submission

**Symptoms**: Jobs exit within minutes, no output generated

**Solution**:
```bash
# Check error log
cat ~/umui_runs/<JOBID>/*.err

# Common causes:
# 1. Wrong executable path
nano ~/umui_jobs/<JOBID>/SCRIPT
# Verify: LOADMODULE=/user/home/$USER/executables/<JOBID>.exe

# 2. Missing input files
ls -la ~/umui_jobs/<JOBID>/
# Check INITHIS, restart files

# 3. Disk quota exceeded
quota -s
df -h /user/home/$USER
df -h /mnt/storage/private/bridge/um_output/$USER
```

---

### Problem: CSV conversion fails

**Symptoms**: "No valid candidates found" or conversion errors

**Solution**:
```bash
# Check CSV format
head input_params/my_candidates.csv

# Common issues:
# 1. Wrong delimiter (must be comma, not tab/semicolon)
# 2. Extra spaces in values
# 3. Missing header row
# 4. Non-numeric values

# Validate CSV:
python3 -c "
import csv
with open('input_params/my_candidates.csv') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        print(f'Row {i}: {row}')
"
```

---

### Problem: "Permission denied" on BRIDGE partition

**Symptoms**: Cannot create directories in `/mnt/storage/private/bridge`

**Solution**:
```bash
# Check access
ls -la /mnt/storage/private/bridge/um_output/$USER/

# If directory doesn't exist, request access:
# Email: hpc-help@bristol.ac.uk
# Subject: Request BRIDGE storage access for HadCM3B ensembles
```

---

### Problem: Job ID generation exceeds 260 limit

**Symptoms**: "Index must be between 0 and 259"

**Solution**:
```bash
# Split into multiple ensembles
# Instead of 300 members in "xqabc":
# - xqabc: 260 members (indices 0-259)
# - xqade: 40 members (indices 0-39)

# Or use --singleJob flag (creates numbered variations)
python create_ensemble_jobs.py \
  --vanilla_job vanilla_jobs/<JOBID> \
  --parameter_file param_tables/<ensemble>.json \
  --ensemble_exp <ensemble> \
  --singleJob
# Creates: xqabc_000, xqabc_001, xqabc_002, ...
```

---

### Problem: Compilation fails

**Symptoms**: `clustersubmit` compilation job fails

**Solution**:
```bash
# Check compilation log
cat ~/umui_runs/<JOBID>/*.comp.out

# Common causes:
# 1. Missing source files
ls -la vanilla_jobs/<JOBID>/

# 2. Fortran compilation errors (usually from UMUI issues)
# Recreate vanilla job in UMUI

# 3. Module loading issues
# Check: vanilla_jobs/<JOBID>/SCRIPT
# Ensure proper module loads for BC4
```

---

## Quick Reference Commands

### Job Management

```bash
# Check job status
qstat -u $USER

# Check specific job
qstat -f <JOBID>

# Cancel job
qdel <JOBID>

# Cancel all ensemble jobs
qstat -u $USER | grep <ensemble> | awk '{print $1}' | xargs qdel

# Check queue info
qstat -Q

# Check node availability
pbsnodes -a
```

### File Operations

```bash
# Count ensemble members
wc -l logs/<ensemble>_generated_ids_*.log

# View generated parameters
cat logs/<ensemble>_updated_parameters_*.json | less

# Check parameter file
jq '.[0]' param_tables/<ensemble>.json  # First member
jq 'length' param_tables/<ensemble>.json  # Total members

# Check disk usage
du -sh ~/umui_jobs/<ensemble>*
du -sh /mnt/storage/private/bridge/um_output/$USER/<ensemble>*

# Find large files
find /mnt/storage/private/bridge/um_output/$USER/<ensemble>* -type f -size +1G
```

### Monitoring

```bash
# Check output generation
for job in $(cat logs/<ensemble>_ids.log); do
    ls /user/home/$USER/dump2hold/$job/datam/ 2>/dev/null | wc -l
done

# Check latest output timestamp
for job in $(cat logs/<ensemble>_ids.log); do
    echo -n "$job: "
    ls -lt /user/home/$USER/dump2hold/$job/datam/ | head -2 | tail -1
done

# Monitor disk usage over time
watch -n 60 "du -sh /mnt/storage/private/bridge/um_output/$USER/<ensemble>*"
```

### Batch Operations

```bash
# Resubmit all failed jobs (exit code != 0)
for job in $(cat logs/<ensemble>_ids.log); do
    if ! qstat -f $job 2>/dev/null | grep -q "Exit_status = 0"; then
        echo "Resubmitting: $job"
        clustersubmit -s y -c y -a y -r bc4 -q veryshort -w 6:00:00 "$job"
    fi
done

# Archive completed jobs
for job in $(cat logs/<ensemble>_ids.log); do
    if qstat -f $job 2>/dev/null | grep -q "Exit_status = 0"; then
        tar -czf ${job}_output.tar.gz /user/home/$USER/dump2hold/$job/datam/
    fi
done
```

---

## Parameter Reference

### Available Land Carbon Cycle Parameters

| Parameter | Description | Units | Typical Range | Default (BL) |
|-----------|-------------|-------|---------------|--------------|
| **ALPHA** | Quantum efficiency (photosynthesis) | mol CO₂/mol photons | 0.04-0.16 | 0.08 |
| **G_AREA** | Leaf area growth rate | m²/m²/day | 0.002-0.008 | 0.004 |
| **F0** | Dark respiration coefficient at 25°C | μmol CO₂/m²/s | 0.80-0.95 | 0.875 |
| **LAI_MIN** | Minimum leaf area index | m²/m² | 1.0-4.0 | 4.0 (trees) |
| **NL0** | Top leaf nitrogen concentration | kg N/kg C | 0.035-0.065 | 0.050 |
| **R_GROW** | Growth respiration fraction | fraction | 0.15-0.30 | 0.25 |
| **TLOW** | Lower temperature threshold | °C | -5 to +5 (delta) | 0.0 |
| **TUPP** | Upper temperature threshold | °C | Auto-adjusted | 36.0 |
| **V_CRIT_ALPHA** | Critical LAI for albedo | m²/m² | 0.0-1.0 | 0.343 |
| **Q10** | Temperature sensitivity (soil) | dimensionless | 1.5-2.5 | 2.0 |
| **KAPS** | Soil carbon decomposition rate | s⁻¹ | 2.5e-9 to 7.5e-9 | 5.0e-9 |

---

## Job ID Generation Algorithm

Supports **260 unique IDs** from 4-character ensemble name:

```python
# Example: ensemble_name = "xqab"

# Indices 0-25: lowercase suffix (xqaba-xqabz)
# Indices 26-51: Capitalize 1st char (Xqaba-Xqabz)
# Indices 52-77: Capitalize 2nd char (xQaba-xQabz)
# ... and so on through all case combinations

# Maximum: 10 case patterns × 26 letters = 260 unique IDs
```

**Example progression**:
```
0: xqaba    26: Xqaba    52: xQaba    78: xqAba
1: xqabb    27: Xqabb    53: xQabb    79: xqAbb
...
25: xqabz   51: Xqabz    77: xQabz    103: xqAbz
```

---

## Best Practices

### 1. Ensemble Naming

- Use 4-character names (lowercase)
- Reserve namespace in UMUI before starting
- Use descriptive names: `xqab` (land params), `xqac` (soil params)

### 2. Parameter Ranges

- Start with conservative ranges around defaults
- Review literature for parameter constraints
- Validate physically reasonable combinations

### 3. Storage Management

- Always use BRIDGE partition for large ensembles
- Clean up partial dumps regularly
- Archive completed runs to tape storage

### 4. Job Submission

- Test with small ensemble first (N=10)
- Monitor first few jobs before submitting all
- Use `veryshort` queue for testing (6 hours)
- Use `cpu` queue for production runs (12-24 hours)

### 5. Validation

- Transfer results to BRIDGE servers regularly
- Run validation checks while jobs are still running
- Identify failures early to adjust parameters

---

## Citation

If you use this workflow in your research, please cite:

```
Steinig, S., et al. (2024). HadCM3B Land Carbon Cycle Ensemble Generator.
University of Bristol. https://github.com/sebsteinig/hadcm3b-ensemble-generator
```

---

## Support

For questions or issues:

- **Technical support**: hpc-help@bristol.ac.uk
- **Scientific questions**: Contact Sebastian Steinig
- **Bug reports**: Create GitHub issue

---

## Related Resources

- **Validation**: https://github.com/sebsteinig/hadcm3b-ensemble-validator
- **UMUI Documentation**: https://cms.ncas.ac.uk/umui/
- **BC4 Guide**: https://www.acrc.bris.ac.uk/protected/bc4-docs/
- **HadCM3B**: https://www.metoffice.gov.uk/research/approach/modelling-systems/unified-model

---

**Last updated**: 2026-01-27
**Version**: 2.0 (with CSV workflow support)
