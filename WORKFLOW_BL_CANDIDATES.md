# Workflow: Generate Ensemble Jobs from BL Candidate Parameters

Complete step-by-step guide to convert BL (Broadleaf) candidate parameters to full ensemble jobs.

---

## Prerequisites

- [ ] Access to PUMA2 (via ARCHER2) for UMUI
- [ ] Access to BC4 cluster
- [ ] BL parameter candidates in CSV format
- [ ] This repository cloned on BC4

---

## Phase 1: Vanilla Job Setup (One-time)

### 1.1 Create Vanilla Job in UMUI (PUMA2)

**Connect to PUMA2:**
```bash
ssh <username>@login.archer2.ac.uk
ssh puma2
umui
```

**In UMUI Interface:**

1. **Create New Experiment:**
   - Click: `File` → `New`
   - Choose base configuration (e.g., pre-industrial HadCM3B)
   - Set experiment ID (e.g., `xqaba`)

2. **Configure Run Settings:**
   - `Model Selection` → `Model Configuration`
     - Set run length: 10-30 years (for testing)
     - Set timestep/output frequency

   - `Model Selection` → `Ancillary and Input Files`
     - Configure restart files
     - Set initial conditions

3. **CRITICAL: Add Land Carbon Cycle Modifications:**
   - Navigate to: `Model Selection` → `Modifications`
   - Click `Add` and enter:
     ```
     /user/home/wb19586/um_updates/znamelist_hadcm3m21_land_cc_v2.mod
     ```
   - This mod enables reading parameters from `CNTLATM` namelist

4. **Add Post-Processing Script:**
   - Navigate to: `Post-processing` → `Scripts`
   - Add: `~ssteinig/scripts/land_cc_v2`

5. **Process Job:**
   - Click: `Processing` → `Process`
   - Wait for completion
   - Job created in: `~/umui_jobs/<JOBID>` (e.g., `~/umui_jobs/xqaba`)

### 1.2 Transfer to BC4

```bash
# From BC4 login node
cd ~/scripts/hadcm3b-ensemble-generator

# Copy vanilla job to template directory
rsync -avz -e 'ssh -J <username>@login.archer2.ac.uk' \
  <username>@puma2:~/umui_jobs/<JOBID> \
  vanilla_jobs/

# Example:
# rsync -avz -e 'ssh -J nd20983@login.archer2.ac.uk' \
#   nd20983@puma2:~/umui_jobs/xqaba \
#   vanilla_jobs/
```

### 1.3 Compile Vanilla Job

```bash
# On BC4
cd ~/scripts/hadcm3b-ensemble-generator

# Submit compilation (replace <JOBID> with your job ID)
clustersubmit -s y -r bp14 -P geog003722 vanilla_jobs/<JOBID>

# Monitor compilation
qstat -u $USER

# Wait until job completes (typically 10-30 minutes)
```

### 1.4 Configure Shared Executable

```bash
# Create directory for executables
mkdir -p ~/executables

# Move compiled executable
JOBID=xqaba  # Replace with your job ID
cp ~/umui_runs/$JOBID/bin/$JOBID.exe ~/executables/

# Update SCRIPT file to use shared executable
nano vanilla_jobs/$JOBID/SCRIPT

# Find the line starting with: LOADMODULE=
# Change to: LOADMODULE=/user/home/$USER/executables/$JOBID.exe
# Save and exit (Ctrl+X, Y, Enter)
```

**✓ Vanilla job setup complete!** This only needs to be done once per template.

---

## Phase 2: Prepare BL Candidate Parameters

### 2.1 Create CSV File with BL Parameters

**CSV Format:**
```csv
candidate_id,ALPHA,G_AREA,F0,LAI_MIN,NL0,R_GROW,TLOW,V_CRIT_ALPHA
candidate_1,0.10,0.005,0.880,3.5,0.055,0.20,2.5,0.5
candidate_2,0.08,0.004,0.875,4.0,0.050,0.25,0.0,0.343
candidate_3,0.12,0.006,0.890,3.0,0.060,0.18,-2.5,0.7
```

**Important notes:**
- **First row:** Header with parameter names
- **candidate_id:** Optional identifier for each candidate
- **TLOW:** Enter as DELTA values (shift from default), not absolute
- **All other params:** Enter as absolute BL values

**Available parameters:**
| Parameter | Description | Units/Range |
|-----------|-------------|-------------|
| `ALPHA` | Quantum efficiency | 0.04-0.16 |
| `G_AREA` | Leaf growth rate | 0.002-0.008 |
| `F0` | Dark respiration coefficient | 0.80-0.95 |
| `LAI_MIN` | Minimum leaf area index | 1.0-4.0 |
| `NL0` | Top leaf nitrogen | 0.035-0.065 |
| `R_GROW` | Growth respiration fraction | 0.15-0.30 |
| `TLOW` | Lower temperature (DELTA) | -5.0 to +5.0 |
| `V_CRIT_ALPHA` | Critical LAI | 0.0-1.0 |

**Template provided:** `input_params/bl_candidates_template.csv`

### 2.2 Edit CSV with Your Candidates

```bash
# Copy template
cp input_params/bl_candidates_template.csv input_params/my_candidates.csv

# Edit with your data
nano input_params/my_candidates.csv
# Or: vi, emacs, or transfer to local machine for Excel editing

# If editing locally, transfer back to BC4:
# scp my_candidates.csv <username>@bc4login.acrc.bris.ac.uk:~/scripts/hadcm3b-ensemble-generator/input_params/
```

### 2.3 Convert CSV to Parameter Table

```bash
cd ~/scripts/hadcm3b-ensemble-generator

# Set variables
ENSEMBLE_NAME="xqabc"  # Choose your ensemble name (4 chars)
CSV_FILE="input_params/my_candidates.csv"

# Run conversion script
python convert_csv_to_param_table.py \
  --csv_file $CSV_FILE \
  --ensemble_name $ENSEMBLE_NAME

# Output created: param_tables/xqabc.json
```

**What this does:**
- Reads BL parameters from CSV
- Expands each BL parameter to full 5-element PFT arrays
- Applies same perturbation logic as other scripts
- Creates JSON file compatible with `create_ensemble_jobs.py`
- Includes default parameters as ensemble member 0

**Verify output:**
```bash
# Check the generated file
head -30 param_tables/$ENSEMBLE_NAME.json

# Count ensemble members (should be # candidates + 1 default)
grep -c '"ALPHA"' param_tables/$ENSEMBLE_NAME.json
```

---

## Phase 3: Generate and Submit Ensemble Jobs

### Option A: Automated Workflow (Recommended)

```bash
cd ~/scripts/hadcm3b-ensemble-generator

# Run complete workflow
./run_full_ensemble_workflow.sh <ensemble_name> <vanilla_job_id>

# Example:
./run_full_ensemble_workflow.sh xqabc xqaba
```

**The script will:**
1. ✓ Check parameter file exists
2. ✓ Check vanilla job exists
3. ✓ Generate ensemble jobs in `~/umui_jobs/`
4. ✓ Create storage directories on BRIDGE partition
5. ✓ Create symlinks in `dump2hold/`
6. ✓ Ask for submission confirmation
7. ✓ Submit jobs or create submission script

**Interactive prompts:**
- Choose: Submit now / Create script / Exit
- If "Create script": Run later with `./submit_<ensemble>_jobs.sh`

---

### Option B: Manual Step-by-Step

#### 3.1 Generate Ensemble Jobs

```bash
cd ~/scripts/hadcm3b-ensemble-generator

ENSEMBLE_NAME="xqabc"
VANILLA_JOB="xqaba"

python create_ensemble_jobs.py \
  --vanilla_job vanilla_jobs/$VANILLA_JOB \
  --parameter_file param_tables/$ENSEMBLE_NAME.json \
  --ensemble_exp $ENSEMBLE_NAME
```

**Output:**
- Jobs created in: `~/umui_jobs/xqabca`, `xqabcb`, `xqabcc`, ...
- Log files in: `logs/`
  - `<ensemble>_generated_ids_<date>.log` (list of job IDs)
  - `<ensemble>_updated_parameters_<date>.json` (parameter record)
  - `<ensemble>_ensemble_jobs_generator_<date>.log` (execution log)

#### 3.2 Create Storage Directories

```bash
# Set log file path
LOGFILE="logs/${ENSEMBLE_NAME}_generated_ids_$(date +%Y%m%d).log"

# Create directories and symlinks
while IFS= read -r job_id; do
    # Create job directory on BRIDGE partition (large storage)
    mkdir -p "/mnt/storage/private/bridge/um_output/$USER/$job_id"

    # Create symlink in dump2hold (standard I/O location)
    ln -s "/mnt/storage/private/bridge/um_output/$USER/$job_id" \
          "/user/home/$USER/dump2hold/$job_id"

    echo "Setup: $job_id"
done < "$LOGFILE"
```

#### 3.3 Submit Jobs to Queue

```bash
# Submit all jobs
while IFS= read -r job_id; do
    echo "Submitting: $job_id"
    clustersubmit -s y -c n -a y -r bp14 -q compute -P geog003722 "$job_id"
done < "$LOGFILE"

# Options explained:
# -s y : Submit to queue
# -c n : Continue from restart = NO (fresh run)
# -a y : Archive outputs
# -r bc4 : BC4 cluster
# -q cpu : CPU queue
# -w 12:00:00 : 12-hour walltime
```

---

## Phase 4: Monitor and Manage Jobs

### 4.1 Check Job Status

```bash
# Check your jobs in queue
qstat -u $USER

# Check specific job
qstat -f <JOBID>

# Check if jobs are producing output
LOGFILE="logs/${ENSEMBLE_NAME}_generated_ids_$(date +%Y%m%d).log"

while IFS= read -r job_id; do
    DATA_DIR="/user/home/$USER/dump2hold/$job_id/datam"
    if [ -n "$(ls -A $DATA_DIR 2>/dev/null)" ]; then
        echo "✓ $job_id: Running/Complete"
    else
        echo "✗ $job_id: No output yet"
    fi
done < "$LOGFILE"
```

### 4.2 Continue Failed/Incomplete Jobs

```bash
# Edit continue script
nano continue_all_jobs.sh

# Update logfile path at top:
# logfile="./logs/${ENSEMBLE_NAME}_generated_ids_YYYYMMDD.log"

# Run continuation
./continue_all_jobs.sh
```

### 4.3 Clean Up Large Files (During Run)

```bash
# Edit clean script
nano clean_all_jobs.sh

# Update logfile path at line 15

# Run cleanup (removes partial dumps, keeps only 20 recent)
./clean_all_jobs.sh
```

---

## Phase 5: Post-Processing (After Completion)

Once jobs finish, use the **hadcm3b-ensemble-validator** repository:

```bash
# On BRIDGE server
cd ~/hadcm3b-ensemble-validator

# Transfer output files
# Process results
# Generate validation plots
# Identify best candidates
```

---

## Quick Reference Commands

```bash
# Check compilation status
qstat -u $USER | grep -i comp

# Check running jobs
qstat -u $USER | grep -i run

# Count ensemble members
wc -l logs/<ensemble>_generated_ids_*.log

# View job parameters
cat logs/<ensemble>_updated_parameters_*.json | less

# Cancel all jobs in ensemble
qstat -u $USER | grep <ensemble> | awk '{print $1}' | xargs qdel

# Check disk usage
du -sh /mnt/storage/private/bridge/um_output/$USER/<ensemble>*
```

---

## Troubleshooting

### Problem: CSV conversion fails

**Solution:**
```bash
# Check CSV format
head input_params/my_candidates.csv

# Ensure:
# - No extra spaces
# - Comma-separated (not tab or semicolon)
# - Header row present
# - Numeric values only (no text in data rows)
```

### Problem: Job generation fails with "Key not found"

**Solution:**
```bash
# Check that vanilla job has land carbon cycle mod enabled
grep "ALPHA=" vanilla_jobs/<JOBID>/CNTLATM

# Should show: ALPHA=0.08,0.08,0.08,0.05,0.08
# If missing, recreate vanilla job in UMUI with proper mod
```

### Problem: Jobs fail immediately after submission

**Solution:**
```bash
# Check job error log
cat ~/umui_runs/<JOBID>/*.err

# Common issues:
# - Executable path wrong in SCRIPT file
# - Missing input files
# - Disk quota exceeded
```

### Problem: "Permission denied" on BRIDGE partition

**Solution:**
```bash
# Check BRIDGE access
ls -la /mnt/storage/private/bridge/um_output/$USER/

# Request access if needed:
# Email: hpc-help@bristol.ac.uk
```

---

## Example Complete Workflow

```bash
# 1. Setup (one-time)
cd ~/scripts/hadcm3b-ensemble-generator
# ... create vanilla job in UMUI ...
# ... transfer and compile ...

# 2. Prepare candidates
nano input_params/top20_candidates.csv
# ... enter your BL parameters ...

# 3. Convert to param table
python convert_csv_to_param_table.py \
  --csv_file input_params/top20_candidates.csv \
  --ensemble_name xqdef

# 4. Generate and submit
./run_full_ensemble_workflow.sh xqdef xqaba

# 5. Monitor
qstat -u $USER

# 6. Continue if needed
# ... edit continue_all_jobs.sh logfile path ...
./continue_all_jobs.sh

# 7. Post-process (after completion)
cd ~/hadcm3b-ensemble-validator
# ... validation workflow ...
```

---

## File Organization

```
hadcm3b-ensemble-generator/
├── vanilla_jobs/
│   └── xqaba/              # Template job
├── input_params/
│   ├── bl_candidates_template.csv
│   └── my_candidates.csv   # Your BL parameters
├── param_tables/
│   └── xqabc.json          # Generated full parameters
├── logs/
│   ├── xqabc_generated_ids_20260127.log
│   ├── xqabc_updated_parameters_20260127.json
│   └── xqabc_ensemble_jobs_generator_20260127.log
└── scripts...

~/umui_jobs/
├── xqaba/                  # Vanilla template
├── xqabca/                 # Ensemble member 0 (default)
├── xqabcb/                 # Ensemble member 1 (candidate 1)
├── xqabcc/                 # Ensemble member 2 (candidate 2)
└── ...

/mnt/storage/private/bridge/um_output/$USER/
├── xqabca/                 # Actual output location
├── xqabcb/
└── ...

/user/home/$USER/dump2hold/
├── xqabca -> /mnt/.../xqabca  # Symlinks
├── xqabcb -> /mnt/.../xqabcb
└── ...
```

---

## Summary Checklist

**Before Starting:**
- [ ] Have BL candidate parameters ready
- [ ] Vanilla job created in UMUI with land carbon cycle mod
- [ ] Vanilla job compiled on BC4
- [ ] BRIDGE storage access confirmed

**Parameter Preparation:**
- [ ] CSV file created with BL parameters
- [ ] CSV converted to param_table JSON
- [ ] Parameter table reviewed and validated

**Job Generation:**
- [ ] Ensemble jobs generated in ~/umui_jobs/
- [ ] Storage directories created on BRIDGE
- [ ] Symlinks created in dump2hold/
- [ ] Jobs submitted to queue

**Monitoring:**
- [ ] Jobs running successfully
- [ ] Output files being generated
- [ ] Disk usage monitored
- [ ] Failed jobs resubmitted if needed

**Post-Processing:**
- [ ] Jobs completed
- [ ] Results transferred for validation
- [ ] Best candidates identified

---

For questions or issues, contact: hpc-help@bristol.ac.uk
