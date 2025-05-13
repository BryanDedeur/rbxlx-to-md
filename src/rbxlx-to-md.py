#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET
import os
import json
import re
from collections import defaultdict

def format_name(name):
    """Format the name with square brackets and quotes if it contains spaces."""
    if ' ' in name:
        return f'["{name}"]'
    return name

def load_settings(settings_file):
    """Load settings from JSON file, or return default settings if file doesn't exist."""
    default_settings = {
        "path_whitelist": [],
        "path_blacklist": [],
        "class_whitelist": [],
        "class_blacklist": [],
        "use_path_whitelist": False,
        "use_path_blacklist": False,
        "use_class_whitelist": False,
        "use_class_blacklist": False,
        "exclude_no_id_items": False
    }
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                user_settings = json.load(f)
                
                # Handle the "Ignore" section format
                if "Ignore" in user_settings:
                    # Map the ClassName array to class_blacklist
                    if "ClassName" in user_settings["Ignore"]:
                        default_settings["class_blacklist"] = user_settings["Ignore"]["ClassName"]
                        default_settings["use_class_blacklist"] = True
                        print(f"Using class blacklist: {default_settings['class_blacklist']}")
                    
                    # Map the Path array to path_blacklist
                    if "Path" in user_settings["Ignore"]:
                        default_settings["path_blacklist"] = user_settings["Ignore"]["Path"]
                        default_settings["use_path_blacklist"] = True
                        print(f"Using path blacklist: {default_settings['path_blacklist']}")
                
                # Handle the direct settings format if present
                for key in default_settings.keys():
                    if key in user_settings:
                        default_settings[key] = user_settings[key]
                
                return default_settings
        except Exception as e:
            print(f"Error loading settings file: {e}. Using default settings.")
    else:
        print(f"Settings file {settings_file} not found. Using default settings.")
    
    return default_settings

def is_path_under(path, ancestor_path):
    """Check if a path is under an ancestor path or exactly matches it."""
    # Handle wildcards in ancestor_path
    if '*' in ancestor_path:
        pattern = '^' + ancestor_path.replace('.', '\\.').replace('*', '.*') + '$'
        if re.match(pattern, path):
            return True
    else:
        # Check if path is exactly ancestor_path or starts with ancestor_path followed by a dot
        return path == ancestor_path or path.startswith(ancestor_path + '.')
    
    return False

def should_include_path(path, settings):
    """Determine if a path should be included based on path whitelist/blacklist settings."""
    # If path whitelist is enabled, path must be under at least one whitelist path
    if settings.get("use_path_whitelist", False) and settings.get("path_whitelist", []):
        for whitelist_path in settings.get("path_whitelist", []):
            # Remove "game." prefix from whitelist_path if it exists
            if whitelist_path.startswith("game."):
                whitelist_path = whitelist_path[5:]  # Remove "game."
            
            if is_path_under(path, whitelist_path):
                break
        else:  # No match found in whitelist
            return False
    
    # If path blacklist is enabled, path must not be under any blacklist path
    if settings.get("use_path_blacklist", False) and settings.get("path_blacklist", []):
        for blacklist_path in settings.get("path_blacklist", []):
            # Remove "game." prefix from blacklist_path if it exists
            if blacklist_path.startswith("game."):
                blacklist_path = blacklist_path[5:]  # Remove "game."
                
            if is_path_under(path, blacklist_path):
                return False
    
    return True

def should_include_class(class_name, settings):
    """Determine if a class should be included based on class whitelist/blacklist settings."""
    # If class whitelist is enabled and not empty, class_name must be in the whitelist
    if settings.get("use_class_whitelist", False) and settings.get("class_whitelist", []):
        if class_name not in settings.get("class_whitelist", []):
            return False
    
    # If class blacklist is enabled, class_name must not be in the blacklist
    if settings.get("use_class_blacklist", False) and settings.get("class_blacklist", []):
        if class_name in settings.get("class_blacklist", []):
            return False
    
    return True

def format_property_value(prop, indent_level=0):
    """Format a property value in a generic way that can handle any structure."""
    indent = "  " * indent_level
    result = []
    
    # Get the property name
    prop_name = prop.get("name", "")
    if not prop_name:
        return ""
    
    # Skip empty properties for certain types
    # This is a minimal list of properties that are often empty and not useful
    if prop_name in ["AttributesSerialize", "Tags"] and (not prop.text or not prop.text.strip()):
        return ""
    
    # Get the property value
    value = prop.text if prop.text else ""
    
    # Generic approach: output property as NAME: VALUE for simple cases
    if not list(prop) and value:  # If there are no child elements and there is text
        result.append(f"{indent}- {prop_name}: {value}")
    else:
        # For properties with children or nested structure
        result.append(f"{indent}- {prop_name}")
        for child in prop:
            # If the child has a tag but no name attribute, it's likely a component of a structured property
            if child.get("name") is None:
                # For component elements like X, Y, Z in Vector3
                result.append(f"{indent}  - {child.tag}: {child.text if child.text else ''}")
            else:
                # For named child properties, recursively format them
                child_value = format_property_value(child, indent_level + 1)
                if child_value:  # Only add non-empty child values
                    result.extend(child_value.split('\n'))
    
    # If no value was added, return empty string
    if not result:
        return ""
    
    return '\n'.join(result)

def extract_properties(item):
    """Extract all properties from an item and return them as a formatted string."""
    properties_elem = item.find("Properties")
    if properties_elem is None:
        return ""
    
    result = []
    for prop in sorted(properties_elem, key=lambda x: x.get("name", "")):
        if prop.get("name") == "Name":
            continue  # Skip Name property since it's already in the path
            
        prop_value = format_property_value(prop)
        if prop_value:  # Only add non-empty property values
            result.append(prop_value)
    
    return "\n".join(result)

def process_xml(root, settings):
    """Process the XML file and return all item paths with unique IDs, organized by high-level path."""
    all_paths = []
    processed_ids = set()
    
    for item in root.findall(".//Item"):
        paths = get_item_path(item, "", processed_ids, settings)
        all_paths.extend(paths)
    
    # Group paths by high-level path (first component)
    grouped_paths = defaultdict(list)
    for path, unique_id, class_name, properties in all_paths:
        # Extract high-level path (e.g., "Workspace" from "Workspace.Part")
        parts = path.split('.')
        if len(parts) > 0:
            high_level = parts[0]
        else:
            high_level = "Root"
        
        grouped_paths[high_level].append((path, unique_id, class_name, properties))
    
    return grouped_paths

def get_item_path(item, parent_path="", processed_ids=None, settings=None):
    """Recursively get the full path of an item and its children using the Name property and UniqueId."""
    if processed_ids is None:
        processed_ids = set()
    if settings is None:
        settings = {}
    
    paths = []
    
    # Get the class name
    class_name = item.get("class", "Unknown")
    
    # Skip if class name is filtered
    if not should_include_class(class_name, settings):
        # Still process children even if this item is excluded by class
        for child in item:
            if child.tag == "Item":
                paths.extend(get_item_path(child, parent_path, processed_ids, settings))
        return paths
    
    # Find the Name property
    name = "Unnamed"
    for prop in item.findall(".//Properties/string[@name='Name']"):
        name = prop.text
        break
    
    # Find the UniqueId
    unique_id = "NoId"
    for prop in item.findall(".//Properties/UniqueId[@name='UniqueId']"):
        unique_id = prop.text
        break
    
    # Skip if we've already processed this item (by unique ID)
    if unique_id in processed_ids:
        return paths
        
    # Skip items with no ID if that setting is enabled
    if settings.get("exclude_no_id_items", False) and unique_id == "NoId":
        return paths
    
    # Extract properties
    properties = extract_properties(item)
    
    # Mark this item as processed
    processed_ids.add(unique_id)
    
    # Format the name based on whether it contains spaces
    formatted_name = format_name(name)
    
    # Build path with proper formatting
    if parent_path:
        if ' ' in name:
            current_path = f"{parent_path}{formatted_name}"
        else:
            current_path = f"{parent_path}.{formatted_name}"
    else:
        if ' ' in name:
            current_path = formatted_name
        else:
            current_path = formatted_name
    
    # Check if this path should be included based on path whitelist/blacklist
    include_current = should_include_path(current_path, settings)
    if include_current:
        paths.append((current_path, unique_id, class_name, properties))
    
    # Always process children, regardless of whether this path is included,
    # since a child could be under a whitelisted path even if its parent is not
    for child in item:
        if child.tag == "Item":
            paths.extend(get_item_path(child, current_path, processed_ids, settings))
    
    return paths

def format_properties(properties):
    """Format properties as a string with each property on a new indented line."""
    if not properties:
        return ""
    return "\n" + properties

def main():
    parser = argparse.ArgumentParser(description='Convert Roblox XML file to readable item paths')
    parser.add_argument('input_file', help='Path to the Roblox XML file')
    parser.add_argument('--output', '-o', help='Output directory path (default: input_file_name_paths)')
    parser.add_argument('--settings', '-s', default='settings.json', help='Path to settings JSON file (default: settings.json)')
    parser.add_argument('--show-class', '-c', action='store_true', help='Include class names in the output')
    parser.add_argument('--single-file', '-f', action='store_true', help='Output to a single file instead of separate files per path')
    parser.add_argument('--show-properties', '-p', action='store_true', help='Include properties in the output (default: True)', default=True)
    
    args = parser.parse_args()
    
    # Set default output directory if not specified
    if not args.output:
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        args.output = f"{base_name}"
    
    try:
        # Count lines in input XML file
        with open(args.input_file, 'r') as f:
            input_line_count = sum(1 for _ in f)
        
        # Load settings
        settings = load_settings(args.settings)
        
        # Parse the XML file
        tree = ET.parse(args.input_file)
        root = tree.getroot()
        
        # Get all item paths with unique IDs, grouped by high-level path
        grouped_paths = process_xml(root, settings)
        
        total_paths = sum(len(paths) for paths in grouped_paths.values())
        total_output_lines = 0
        
        if args.single_file:
            # Write all paths to a single file (backward compatibility)
            all_paths = []
            for paths in grouped_paths.values():
                all_paths.extend(paths)
            
            os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
            with open(args.output, 'w') as f:
                for path, unique_id, class_name, properties in sorted(all_paths):
                    if args.show_class:
                        f.write(f"{path} ({unique_id}) [{class_name}]")
                    else:
                        f.write(f"{path} ({unique_id})")
                    
                    if args.show_properties:
                        f.write(format_properties(properties))
                    else:
                        f.write("\n")
                    
                    # Add a blank line between items
                    f.write("\n\n")
            
            # Count lines in output file
            with open(args.output, 'r') as f:
                total_output_lines = sum(1 for _ in f)
                
            print(f"Successfully wrote {total_paths} item paths to {args.output}")
        else:
            # Write each high-level path to its own file in a directory
            os.makedirs(args.output, exist_ok=True)
            
            file_count = 0
            output_files = []
            for high_level, paths in grouped_paths.items():
                if paths:  # Only create files for non-empty path groups
                    file_count += 1
                    output_file = os.path.join(args.output, f"{high_level}.md")
                    output_files.append(output_file)
                    with open(output_file, 'w') as f:
                        for path, unique_id, class_name, properties in sorted(paths):
                            if args.show_class:
                                f.write(f"{path} ({unique_id}) [{class_name}]")
                            else:
                                f.write(f"{path} ({unique_id})")
                            
                            if args.show_properties:
                                f.write(format_properties(properties))
                            else:
                                f.write("\n")
                            
                            # Add a blank line between items
                            f.write("\n\n")
            
            # Count lines in all output files
            for output_file in output_files:
                with open(output_file, 'r') as f:
                    total_output_lines += sum(1 for _ in f)
            
            print(f"Successfully wrote {total_paths} item paths across {file_count} files in the {args.output} directory")
        
        # Report line count reduction
        line_reduction = input_line_count - total_output_lines
        reduction_percentage = (line_reduction / input_line_count) * 100
        print(f"Input XML: {input_line_count} lines, Output: {total_output_lines} lines")
        print(f"Reduced by {line_reduction} lines ({reduction_percentage:.2f}%)")
            
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
