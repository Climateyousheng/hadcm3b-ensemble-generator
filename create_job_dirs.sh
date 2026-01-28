# create job directories for each ensemble job on bp14 geog-tropical storage
# create symlinks in dump2hold for normal model I/O
user_name=$(whoami)
while IFS= read -r job_id; do
    BRIDGE_DIR="/bp1/geog-tropical/users/$user_name/DUMP2HOLD/um/$job_id"
    DUMP_LINK="/user/home/$user_name/dump2hold/$job_id"

    echo "Creating: $BRIDGE_DIR"
    mkdir -p "$BRIDGE_DIR"

    echo "Linking: $DUMP_LINK -> $BRIDGE_DIR"
    ln -s "$BRIDGE_DIR" "$DUMP_LINK"

# done < logs/xqaRd_generated_ids_20241028.log
done < logs/xqhL_generated_ids_20251121.log









