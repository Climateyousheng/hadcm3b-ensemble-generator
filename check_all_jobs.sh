#!/bin/bash

# File containing the experiment IDs (one job ID per line)
# Use the *_generated_ids_*.log file, NOT the *_ensemble_jobs_generator_*.log file
# logfile="./logs/xqap_generated_ids_20240907.log"
# logfile="./logs/xqaq_generated_ids_20240908.log"
# logfile="./logs/xqar_generated_ids_20240908.log"
logfile="./logs/xqjc_generated_ids_20260128.log"

# Loop through each line in the log file
user_name=$(whoami)
while IFS= read -r experiment_id
do
  data_dir="/user/home/$user_name/dump2hold/$experiment_id/datam"
  # Check if any files exist in data_dir
  if [ -n "$(ls -A "$data_dir")" ]; then
    echo "Files exist in $data_dir"
  else
    echo "clustersubmit $experiment_id"
    clustersubmit -s y -c n -a y -r bp14 -q compute -P geog003722 "$experiment_id"
  fi
done < "$logfile"