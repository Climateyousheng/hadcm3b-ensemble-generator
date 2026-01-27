"""
Expand BL (Broadleaf) parameter values to full PFT (Plant Functional Type) arrays.

Given parameter values for the Broadleaf PFT, this script generates the complete
parameter sets for all 5 PFTs using the same perturbation logic as the ensemble
generation scripts.
"""

import json

# Optional: use helpers if available
try:
    from helpers import create_json_file
    HAS_HELPERS = True
except ImportError:
    HAS_HELPERS = False


# Default parameter set from "acang" (MetOffice C4MIP run from 2006)
default_params = {
    "ALPHA": [0.08, 0.08, 0.08, 0.05, 0.08],
    "G_AREA": [0.004, 0.004, 0.10, 0.10, 0.05],
    "F0": [0.875, 0.875, 0.900, 0.800, 0.900],
    "LAI_MIN": [4.0, 4.0, 1.0, 1.0, 1.0],
    "NL0": [0.050, 0.030, 0.060, 0.030, 0.030],
    "R_GROW": [0.25, 0.25, 0.25, 0.25, 0.25],
    "TLOW": [0.0, -5.0, 0.0, 13.0, 0.0],
    "TUPP": [36.0, 31.0, 36.0, 45.0, 36.0],
    "V_CRIT_ALPHA": [0.343],
}


def perturb_list(defaults, key, new_bl_param):
    """
    Apply BL parameter value to generate full PFT array.

    Args:
        defaults: Default parameter array for all PFTs
        key: Parameter name
        new_bl_param: New value for BL (or delta for temperature params)

    Returns:
        List of parameter values for all 5 PFTs
    """
    perturbed_list = defaults.copy()

    if key in ["F0", "NL0", "ALPHA", "G_AREA"]:
        # Pro-rata: calculate delta from BL default, apply to all PFTs
        delta_bl = new_bl_param - defaults[0]
        for i in range(len(defaults)):
            perturbed_list[i] += delta_bl

    elif key == "LAI_MIN":
        # Apply to tree PFTs only (indices 0-1), keep grass/shrubs at 1.0
        perturbed_list[0] = new_bl_param
        perturbed_list[1] = new_bl_param

    elif key in ["R_GROW", "V_CRIT_ALPHA"]:
        # Apply same value to all PFTs
        perturbed_list = [new_bl_param for _ in perturbed_list]

    elif key in ["TLOW", "TUPP"]:
        # Add delta to all PFT defaults
        perturbed_list = [default + new_bl_param for default in perturbed_list]

    perturbed_list = [round(value, 5) for value in perturbed_list]
    return perturbed_list


def expand_bl_params_to_pfts(bl_params, defaults=default_params):
    """
    Expand BL parameter values to full PFT parameter set.

    Args:
        bl_params: Dictionary of BL parameter values
                   For TLOW/TUPP, provide delta values (not absolute)
        defaults: Default parameter set to use as reference

    Returns:
        Dictionary with full PFT arrays for all parameters
    """
    expanded_params = {}

    for key, bl_value in bl_params.items():
        if key not in defaults:
            print(f"Warning: '{key}' not found in defaults, skipping")
            continue

        expanded_params[key] = perturb_list(defaults[key], key, bl_value)

        # Co-vary TLOW and TUPP
        if key == "TLOW" and "TUPP" not in bl_params:
            expanded_params["TUPP"] = perturb_list(defaults["TUPP"], "TUPP", bl_value)

    # Add any parameters not specified (keep at defaults)
    for key in defaults:
        if key not in expanded_params:
            expanded_params[key] = defaults[key].copy()

    return expanded_params


def main():
    """
    Example usage: expand BL parameter values to full PFT arrays.
    """
    # Example: specify BL parameter values
    # For TLOW/TUPP, provide DELTA values (e.g., -2.5 means shift by -2.5)
    bl_input_params = {
        "ALPHA": 0.10,        # absolute BL value
        "G_AREA": 0.005,      # absolute BL value
        "LAI_MIN": 3.5,       # absolute value for trees
        "NL0": 0.055,         # absolute BL value
        "R_GROW": 0.20,       # uniform value for all PFTs
        "TLOW": 2.5,          # delta to add to all PFTs
        "V_CRIT_ALPHA": 0.5,  # single value
    }

    print("Input BL parameters:")
    print(json.dumps(bl_input_params, indent=2))
    print("\n" + "="*60 + "\n")

    # Expand to full PFT arrays
    full_params = expand_bl_params_to_pfts(bl_input_params)

    print("Expanded parameters for all 5 PFTs:")
    print(json.dumps(full_params, indent=2))

    # Optional: save to file
    if HAS_HELPERS:
        output_file = "./param_tables/expanded_from_bl.json"
        create_json_file(output_file, [full_params], default_params)
        print(f"\nSaved to '{output_file}'")
    else:
        # Simple JSON save without helpers
        output_file = "./param_tables/expanded_from_bl.json"
        with open(output_file, 'w') as f:
            json.dump([full_params], f, indent=2)
        print(f"\nSaved to '{output_file}' (basic format)")


if __name__ == "__main__":
    main()
