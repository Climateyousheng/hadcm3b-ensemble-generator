# Clean up old model output files from bp14 geog-tropical storage
# Removes intermediate restart files and keeps only recent history
user_name=$(whoami)
while IFS= read -r job_id; do
    DATAM_DIR="/bp1/geog-tropical/users/$user_name/DUMP2HOLD/um/$job_id/datam"
    cd "$DATAM_DIR"
    ls *p[abcdf]00*
    rm -f *p[abcdf]00*
    ls -t *da00* | tail -n +21
    ls -t *da00* | tail -n +21 | while read -r file; do rm -f "$file"; done
# done < logs/xqab_generated_ids_20240808.log
# done < logs/xqac_generated_ids_20240815.log
# done < logs/xqap_generated_ids_20240907.log
# done < logs/xqaq_generated_ids_20240908.log
# done < logs/xqar_generated_ids_20240908.log
done < logs/xqau_generated_ids_20240909.log

