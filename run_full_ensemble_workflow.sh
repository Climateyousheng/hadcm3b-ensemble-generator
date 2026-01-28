#!/bin/bash
#
# Complete workflow script to generate and submit ensemble jobs
# Usage: ./run_full_ensemble_workflow.sh <ensemble_name> <vanilla_job_id>
#
# Example: ./run_full_ensemble_workflow.sh xqabc xqaba
#

set -e  # Exit on error

# Check arguments
if [ $# -ne 2 ]; then
    echo "Usage: $0 <ensemble_name> <vanilla_job_id>"
    echo "Example: $0 xqabc xqaba"
    exit 1
fi

ENSEMBLE_NAME=$1
VANILLA_JOB=$2
USER_NAME=$(whoami)

# Paths
REPO_DIR="$HOME/scripts/hadcm3b-ensemble-generator"
PARAM_FILE="$REPO_DIR/param_tables/${ENSEMBLE_NAME}.json"
VANILLA_PATH="$REPO_DIR/vanilla_jobs/$VANILLA_JOB"
LOG_DIR="$REPO_DIR/logs"
DATE_STAMP=$(date +%Y%m%d)
GENERATED_IDS_LOG="$LOG_DIR/${ENSEMBLE_NAME}_generated_ids_${DATE_STAMP}.log"

echo "================================================================"
echo "HadCM3B Ensemble Generation Workflow"
echo "================================================================"
echo "Ensemble name:    $ENSEMBLE_NAME"
echo "Vanilla job:      $VANILLA_JOB"
echo "Parameter file:   $PARAM_FILE"
echo "================================================================"
echo ""

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo "-----------------------------------"

if [ ! -f "$PARAM_FILE" ]; then
    echo "ERROR: Parameter file not found: $PARAM_FILE"
    echo "Please run convert_csv_to_param_table.py first"
    exit 1
fi

if [ ! -d "$VANILLA_PATH" ]; then
    echo "ERROR: Vanilla job not found: $VANILLA_PATH"
    echo "Please copy vanilla job to vanilla_jobs/ directory"
    exit 1
fi

echo "✓ Parameter file exists"
echo "✓ Vanilla job exists"
echo ""

# Step 2: Generate ensemble jobs
echo "Step 2: Generating ensemble jobs..."
echo "-----------------------------------"

cd "$REPO_DIR"

python create_ensemble_jobs.py \
    --vanilla_job "$VANILLA_PATH" \
    --parameter_file "$PARAM_FILE" \
    --ensemble_exp "$ENSEMBLE_NAME"

if [ ! -f "$GENERATED_IDS_LOG" ]; then
    echo "ERROR: Job generation failed - log file not created"
    exit 1
fi

NUM_JOBS=$(wc -l < "$GENERATED_IDS_LOG")
echo "✓ Generated $NUM_JOBS ensemble jobs"
echo ""

# Step 3: Create storage directories
echo "Step 3: Setting up storage directories..."
echo "-----------------------------------"

while IFS= read -r job_id; do
    BRIDGE_DIR="/bp1/geog-tropical/users/$USER_NAME/DUMP2HOLD/um/$job_id"
    DUMP_LINK="/user/home/$USER_NAME/dump2hold/$job_id"

    # Create directory on BRIDGE partition
    if [ ! -d "$BRIDGE_DIR" ]; then
        mkdir -p "$BRIDGE_DIR"
        echo "  Created: $BRIDGE_DIR"
    fi

    # Create symlink in dump2hold
    if [ ! -L "$DUMP_LINK" ]; then
        ln -s "$BRIDGE_DIR" "$DUMP_LINK"
        echo "  Linked: $DUMP_LINK -> $BRIDGE_DIR"
    fi
done < "$GENERATED_IDS_LOG"

echo "✓ Storage directories created"
echo ""

# Step 4: Ask before submission
echo "================================================================"
echo "Ready to submit $NUM_JOBS jobs to BC4 queue"
echo "================================================================"
echo ""
echo "Generated job IDs saved to:"
echo "  $GENERATED_IDS_LOG"
echo ""
echo "Submit options:"
echo "  1. Submit all jobs now"
echo "  2. Create submission script for later"
echo "  3. Exit without submitting"
echo ""
read -p "Choose option [1/2/3]: " SUBMIT_OPTION

case $SUBMIT_OPTION in
    1)
        echo ""
        echo "Step 4: Submitting jobs to queue..."
        echo "-----------------------------------"

        SUBMITTED=0
        while IFS= read -r job_id; do
            echo "  Submitting: $job_id"
            clustersubmit -s y -c n -a y -r bp14 -q compute -P geog003722 "$job_id"
            SUBMITTED=$((SUBMITTED + 1))
        done < "$GENERATED_IDS_LOG"

        echo "✓ Submitted $SUBMITTED jobs"
        echo ""
        ;;
    2)
        SUBMIT_SCRIPT="$REPO_DIR/submit_${ENSEMBLE_NAME}_jobs.sh"
        cat > "$SUBMIT_SCRIPT" <<EOF
#!/bin/bash
# Auto-generated submission script for ensemble: $ENSEMBLE_NAME
# Generated: $(date)

logfile="$GENERATED_IDS_LOG"

while IFS= read -r experiment_id; do
    echo "Submitting: \$experiment_id"
    clustersubmit -s y -c n -a y -r bp14 -q compute -P geog003722 "\$experiment_id"
done < "\$logfile"
EOF
        chmod +x "$SUBMIT_SCRIPT"
        echo "✓ Created submission script: $SUBMIT_SCRIPT"
        echo ""
        echo "To submit jobs later, run:"
        echo "  $SUBMIT_SCRIPT"
        echo ""
        ;;
    3)
        echo ""
        echo "Exiting without submission."
        echo ""
        echo "To submit jobs later, use:"
        echo "  ./submit_all_jobs.sh  (after editing logfile path)"
        echo ""
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac

# Summary
echo "================================================================"
echo "Workflow Complete!"
echo "================================================================"
echo ""
echo "Ensemble name:     $ENSEMBLE_NAME"
echo "Number of jobs:    $NUM_JOBS"
echo "Job IDs saved to:  $GENERATED_IDS_LOG"
echo ""
echo "Useful commands:"
echo "  Check job status:  qstat -u $USER_NAME"
echo "  Monitor jobs:      ./check_all_jobs.sh (after editing logfile)"
echo "  Continue runs:     ./continue_all_jobs.sh (after editing logfile)"
echo "  Clean up data:     ./clean_all_jobs.sh (after editing logfile)"
echo ""
echo "================================================================"
