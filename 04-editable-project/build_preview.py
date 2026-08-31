import argparse

from build_all import build_contact_sheets, build_individual_previews, select_specs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="all")
    parser.add_argument("--individual", action="store_true")
    args = parser.parse_args()
    specs = select_specs(args.only)
    outputs = (
        build_individual_previews(specs)
        if args.individual
        else build_contact_sheets(specs, args.only)
    )
    for output in outputs:
        print(output)
