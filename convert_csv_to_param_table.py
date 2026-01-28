"""
Convert CSV file with BL parameter values to full param_tables JSON format.

Input CSV format:
  candidate_id,ALPHA,G_AREA,F0,LAI_MIN,NL0,R_GROW,TLOW,V_CRIT_ALPHA
  candidate_1,0.10,0.005,0.88,3.5,0.055,0.20,2.5,0.5
  candidate_2,0.08,0.004,0.90,4.0,0.050,0.25,0.0,0.343
  ...

Note: Parameter names are normalized automatically:
  - V_CRIT or VCRIT → V_CRIT_ALPHA
  - Case-insensitive (vcrit, V_Crit, etc. all work)

Output: JSON file compatible with create_ensemble_jobs.py
"""

import csv
import json
import argparse
from pathlib import Path

# Import the BL expansion logic
from expand_bl_to_pfts import expand_bl_params_to_pfts, default_params


# Parameter name mappings (CSV column name -> internal parameter name)
PARAMETER_NAME_MAP = {
    'V_CRIT': 'V_CRIT_ALPHA',
    'VCRIT': 'V_CRIT_ALPHA',
    'V_CRIT_ALPHA': 'V_CRIT_ALPHA',
    # Add more mappings as needed
}


def normalize_parameter_name(param_name):
    """
    Normalize parameter name to match internal naming convention.

    Args:
        param_name: Parameter name from CSV header

    Returns:
        Normalized parameter name
    """
    param_name = param_name.strip().upper()

    # Check if mapping exists
    if param_name in PARAMETER_NAME_MAP:
        return PARAMETER_NAME_MAP[param_name]

    # Return as-is if no mapping found
    return param_name


def read_csv_candidates(csv_file):
    """
    Read BL parameter candidates from CSV file.

    Expected CSV format:
    - First row: header with parameter names
    - Subsequent rows: candidate values
    - Optional 'candidate_id' column (will be used as identifier)

    Returns:
        List of dictionaries with BL parameter values
    """
    candidates = []
    name_mappings_logged = set()  # Track which mappings we've already logged

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            candidate = {}

            # Extract candidate ID if present
            candidate_id = row.pop('candidate_id', None) or row.pop('id', None)

            # Convert string values to appropriate types
            for key, value in row.items():
                key = key.strip()
                value = value.strip()

                # Skip empty values
                if not value:
                    continue

                # Normalize parameter name
                normalized_key = normalize_parameter_name(key)

                # Log parameter name mapping (only once per unique mapping)
                if normalized_key != key.strip().upper() and key not in name_mappings_logged:
                    print(f"  Note: Mapping '{key}' → '{normalized_key}'")
                    name_mappings_logged.add(key)

                # Convert to float
                try:
                    candidate[normalized_key] = float(value)
                except ValueError:
                    print(f"Warning: Could not convert '{value}' to float for key '{key}' (normalized: {normalized_key})")
                    continue

            if candidate:
                candidate['_id'] = candidate_id  # Store for reference
                candidates.append(candidate)

    return candidates


def create_param_table_from_csv(csv_file, output_file, ensemble_name):
    """
    Convert CSV with BL parameters to full param_table JSON.

    Args:
        csv_file: Path to input CSV file
        output_file: Path to output JSON file
        ensemble_name: Name of ensemble experiment
    """
    print(f"Reading BL candidates from: {csv_file}")
    bl_candidates = read_csv_candidates(csv_file)

    if not bl_candidates:
        print("ERROR: No valid candidates found in CSV file")
        return False

    print(f"Found {len(bl_candidates)} candidates")

    # Expand each BL candidate to full PFT arrays
    full_param_sets = []

    for i, bl_params in enumerate(bl_candidates):
        candidate_id = bl_params.pop('_id', None)

        print(f"\nProcessing candidate {i+1}/{len(bl_candidates)}")
        if candidate_id:
            print(f"  ID: {candidate_id}")
        print(f"  BL params: {list(bl_params.keys())}")

        # Expand to full PFT arrays
        full_params = expand_bl_params_to_pfts(bl_params)

        full_param_sets.append(full_params)

    # Create output JSON in the same format as create_param_table_*.py scripts
    print(f"\nWriting {len(full_param_sets) + 1} parameter sets to: {output_file}")

    with open(output_file, 'w') as f:
        f.write("[\n")

        # First entry: default parameters (ensemble member 0)
        f.write("    {\n")
        for i, (key, value) in enumerate(default_params.items()):
            f.write(f'      "{key}": {json.dumps(value)}')
            if i < len(default_params) - 1:
                f.write(',')
            f.write('\n')
        f.write("    },\n")

        # Subsequent entries: candidate parameter sets
        for idx, params in enumerate(full_param_sets):
            f.write("    {\n")
            for i, (key, value) in enumerate(params.items()):
                f.write(f'      "{key}": {json.dumps(value)}')
                if i < len(params) - 1:
                    f.write(',')
                f.write('\n')
            f.write("    }")
            if idx < len(full_param_sets) - 1:
                f.write(',')
            f.write('\n')

        f.write("]\n")

    print(f"\n✓ Successfully created param_table with {len(full_param_sets)} candidates")
    print(f"  (plus 1 default set = {len(full_param_sets) + 1} total ensemble members)")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Convert CSV with BL parameters to param_table JSON for ensemble generation"
    )
    parser.add_argument(
        "--csv_file",
        type=str,
        required=True,
        help="Path to CSV file with BL parameter candidates"
    )
    parser.add_argument(
        "--output_file",
        type=str,
        help="Path to output JSON file (default: param_tables/<ensemble_name>.json)"
    )
    parser.add_argument(
        "--ensemble_name",
        type=str,
        required=True,
        help="Ensemble experiment name (e.g., xqabc)"
    )

    args = parser.parse_args()

    # Set default output file if not specified
    if not args.output_file:
        output_dir = Path("param_tables")
        output_dir.mkdir(exist_ok=True)
        args.output_file = output_dir / f"{args.ensemble_name}.json"

    # Convert CSV to param_table
    success = create_param_table_from_csv(
        args.csv_file,
        args.output_file,
        args.ensemble_name
    )

    if success:
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print(f"\n1. Review the generated file: {args.output_file}")
        print(f"\n2. Create ensemble jobs:")
        print(f"   python create_ensemble_jobs.py \\")
        print(f"     --vanilla_job ~/hadcm3b-ensemble-generator/vanilla_jobs/<JOBID> \\")
        print(f"     --parameter_file {args.output_file} \\")
        print(f"     --ensemble_exp {args.ensemble_name}")
        print(f"\n3. Set up storage directories and submit jobs")
        print("="*60)


if __name__ == "__main__":
    main()
