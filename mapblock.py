def map_type(dspace_type):
    """Map DSpace types to Datacite types."""
    type_mapping = {
        "Archival Material": "Text",
        "Illustration": "Image",
        "Image": "Image",
        "Magazine Article": "Text",
        "Paper": "Text",
        #"Journal Article": "Text",
        #"Conference Paper": "Text",
        #"Video": "Audiovisual",
        #"Audio": "Audiovisual",
        #"Map": "Map",
        #"Software": "Software"
    }
    return type_mapping.get(dspace_type, "Text") # Default to "Text" if no mapping is found