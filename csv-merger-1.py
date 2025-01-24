import csv
import re

def reverse_name_order(name):
    """Reverse the order of a name formatted as 'LASTNAME, FIRSTNAME' and strip trailing periods."""
    parts = [part.strip().rstrip(".") for part in name.split(",")]
    if len(parts) == 2:
        return f"{parts[1]} {parts[0]}"
    return name.strip().rstrip(".")

# Prompt user for file names
dspace_csv = input("Enter the name of the DSpace export CSV (including .csv extension): ")
datacite_csv = input("Enter the name for the output Datacite CSV (including .csv extension): ")

# Define transformations
uri_patterns = ["http://hdl.handle.net/10613", "http://hdl.handle.net/10170"]

def map_type(dspace_type):
    """Map DSpace types to Datacite types."""
    type_mapping = {
        "Archival Material": "Text",
        "Illustration": "Image",
        "Image": "Image",
        "Magazine Article": "Text",
        "Paper": "Text",
    }
    return type_mapping.get(dspace_type, "Text") # Default to "Text" if no mapping is found

# Read the DSpace export CSV
with open(dspace_csv, mode="r", encoding="utf-8") as dspace_file:
    dspace_reader = csv.DictReader(dspace_file)
    
    # Define the output fieldnames for the Datacite template
    datacite_fieldnames = [
        "title", "year", "type", "description",
        "creator1", "creator1_type", "creator1_given", "creator1_family",
        "creator2", "creator2_type", "creator2_given", "creator2_family",
        "publisher", "source"
    ]

    # Prepare the output rows
    datacite_rows = []
    input_row_count = 0
    output_row_count = 0

    for row in dspace_reader:
        input_row_count += 1

        # Extract fields for the Datacite template
        title = row.get("dc.title[en]", row.get("dc.title", row.get("dc.title[]", ""))).strip()
        year = row.get("dc.date.issued[]", row.get("dc.date.issued[en]", row.get("dc.date.issued", ""))).strip()
        type_field = map_type(row.get("dc.type[en]", row.get("dc.type", row.get("dc.type[]", ""))).strip())
        description = row.get("dc.description.abstract[en]", row.get("dc.description", row.get("dc.description[]", ""))).strip()
        publisher = row.get("dc.publisher[en]", "").strip()

        # Extract source from URI if it matches one of the patterns
        source = ""
        for uri_field in ["dc.identifier.uri[]", "dc.identifier.uri", "dc.identifier.uri[en]"]:
            if uri_field in row and any(pattern in row[uri_field] for pattern in uri_patterns):
                source = row[uri_field].split("||")[0].strip()
                break

        # Handle contributors dynamically (author > other > editor > advisor)
        contributors = []

        def get_field_data(row, base_field_name):
            """Retrieve the first non-empty field value from variations of a base field name."""
            for suffix in ["[en]", "[]", ""]:
                value = row.get(f"{base_field_name}{suffix}", "").strip()
                if value:
                    return value
            return ""

        for field_group in ["author", "other", "editor", "advisor"]:
            # Retrieve data for the current contributor group
            field_data = get_field_data(row, f"dc.contributor.{field_group}")
            if field_data:
                contributors.extend([
                    re.sub(r"::.*", "", name).strip().rstrip(".")  # Remove metadata (::...) and trailing periods
                    for name in field_data.split("||") if name.strip()
                ])

        # Assign creator1 and creator2
        if len(contributors) == 0:
            creator1, creator2 = "Unknown", ""
        else:
            creator1 = reverse_name_order(contributors[0])
            creator2 = reverse_name_order(contributors[1]) if len(contributors) > 1 else ""

        # Split creator names into given and family parts
        def split_name(name):
            parts = name.split()
            if len(parts) > 1:
                return " ".join(parts[:-1]), parts[-1]
            return "", name  # Single name goes to family

        creator1_given, creator1_family = split_name(creator1 if creator1 != "Unknown" else "")
        creator2_given, creator2_family = split_name(creator2)

        # Add the transformed row to the Datacite output
        datacite_rows.append({
            "title": title,
            "year": year,
            "type": type_field,
            "description": description,
            "creator1": creator1,
            "creator1_type": "Personal" if creator1 != "Unknown" else "",
            "creator1_given": creator1_given,
            "creator1_family": creator1_family,
            "creator2": creator2,
            "creator2_type": "Personal" if creator2 else "",
            "creator2_given": creator2_given,
            "creator2_family": creator2_family,
            "publisher": publisher,
            "source": source
        })
        output_row_count += 1

# Write the transformed rows to the Datacite CSV
with open(datacite_csv, mode="w", encoding="utf-8", newline="") as datacite_file:
    writer = csv.DictWriter(datacite_file, fieldnames=datacite_fieldnames)
    writer.writeheader()
    writer.writerows(datacite_rows)

print(f"Transformed data has been saved to {datacite_csv}")
print(f"Rows in input file: {input_row_count}")
print(f"Rows in output file: {output_row_count}")
