#!/bin/bash

# File containing the experiment IDs
# logfile="./logs/xqab.log"
# logfile="./logs/xqap_generated_ids_20240907.log"
# logfile="./logs/xqaq_generated_ids_20240908.log"
# logfile="./logs/xqar_generated_ids_20240908.log"
logfile="./logs/xqau_generated_ids_20240909.log"

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