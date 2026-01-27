## Codes explanation

### Purpose
The README describes how to generate hundreds of model runs with different tuning parameters so that promising configurations can be identified for future coupled climate‑carbon simulations. It outlines the overall workflow: create a vanilla UMUI job, compile once, generate parameter tables, create ensemble jobs, and submit them for execution.

### Key scripts
helpers.py – Contains support functions. Highlights include:

generate_ensemble_jobid for producing unique job IDs from an experiment name and index.

duplicate_job to copy a template UM job and edit its configuration for the new ID.

Logging utilities and helpers for creating JSON parameter files and plotting distributions.

create_param_table_random.py – Generates random parameter sets from specified ranges and saves them as JSON, also plotting distributions.

create_param_table_single.py – Varies one parameter at a time for sensitivity studies.

create_param_table_csoil_from_candidates.py – Builds soil‑carbon parameter sets using previously identified candidate values.

create_ensemble_jobs.py – Reads a parameter file and duplicates the vanilla job for each parameter set. It logs generated IDs and updates the job’s namelists with new values. The main logic for each run is shown here.

Shell scripts (submit_all_jobs.sh, check_all_jobs.sh, continue_all_jobs.sh, etc.) automate job submission and monitoring, while run_benchmarking_suite.sh provides a structured benchmarking workflow.

### Data
Numerous JSON files under param_tables/ and input_params/ hold example parameter sets. Directories in vanilla_jobs/ contain template UMUI job files that serve as starting points for ensemble members.

### Overall
In short, this repository streamlines creation, customization, and submission of large ensembles of HadCM3B model runs, focusing on tuning land carbon cycle parameters and managing the resulting jobs. The provided Python helper utilities and shell scripts implement the workflow described in the README.

### helpers.py

Provides utilities for generating ensemble job IDs, duplicating a UMUI job, logging, creating JSON tables, and plotting parameter distributions.

generate_ensemble_jobid ensures a unique job ID from an experiment name and index. It varies the case of characters in the experiment name and appends a letter so up to 260 IDs can be produced. The logic maps different index ranges to different capitalization patterns (lines 25‑82)

duplicate_job copies an existing job directory to ~/umui_jobs/<new_runid>. It checks the IDs, backs up key files, then uses sed to update JOBID/RUNID references in them (lines 89‑167)

setup_logging builds a log directory, prepares time‑stamped log files, and returns handles for the logger plus log file names (lines 171‑231)

create_json_file writes a list of parameter sets to JSON with custom formatting, and plot_param_distributions creates per‑parameter histograms saved to a PDF (lines 244‑330)

### create_ensemble_jobs.py

The main script for generating ensemble jobs. It sets up logging and reads a JSON parameter file (lines 10‑45)

For each parameter set, it chooses a new job ID—either sequential “<expid>_<number>” or via generate_ensemble_jobid—and logs that ID (lines 52‑60)

It then duplicates the template job using duplicate_job. After reading the job’s CNTLATM namelist, it replaces lines matching each parameter with the new values using sed. Any missing keys trigger a warning (lines 62‑104)

Updated parameters are saved to a log JSON file; at the end the script reports how many ensemble members were created and where logs are stored (lines 106‑114)

Command‑line arguments accept the template job path, parameter JSON path, ensemble name, and an optional --singleJob switch (lines 116‑144)

Overall, helpers.py supplies core utilities for job ID generation, directory duplication, logging, JSON output, and visualization. create_ensemble_jobs.py orchestrates the ensemble creation workflow by duplicating the vanilla job for each parameter set, editing its namelist with the new values, and recording all IDs and parameters for later reference.