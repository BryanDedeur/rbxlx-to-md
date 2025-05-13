#!/usr/bin/env python3

import argparse
import os
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import uuid
from collections import defaultdict

def create_basic_rbxlx_structure():
    """Create a basic RBXLX file structure."""
    # Create the root element
    root = ET.Element("roblox", {
        "xmlns:xmime": "http://www.w3.org/2005/05/xmlmime",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "http://www.roblox.com/roblox.xsd",
        "version": "4"
    })
    
    # Add External tag
    external = ET.SubElement(root, "External")
    external.text = "null"
    
    # Add External tag for import
    external_cframe = ET.SubElement(root, "External")
    external_cframe.text = "nil"
    
    # Add meta tags
    meta = ET.SubElement(root, "Meta", {"name": "ExplicitAutoJoints"})
    meta.text = "true"
    
    return root

def parse_property_line(line):
    """Parse a property line from the MD file."""
    # Basic property pattern: - PropertyName: PropertyValue
    match = re.match(r'^\s*-\s+(\w+):\s*(.*)$', line)
    if match:
        name = match.group(1)
        value = match.group(2).strip()
        return name, value, None
    
    # If it's just a property name without a value
    match = re.match(r'^\s*-\s+(\w+)$', line)
    if match:
        return match.group(1), None, "complex"
    
    return None, None, None

def create_property_element(parent, prop_type, name, value):
    """Create a property element with the given type, name, and value."""
    elem = ET.SubElement(parent, prop_type, {"name": name})
    if value is not None:
        elem.text = value
    return elem

def determine_property_type(value):
    """Determine the property type based on its value."""
    if value is None:
        return "nil"
    
    # Check for boolean values
    if value.lower() in ["true", "false"]:
        return "bool"
    
    # Check for numbers
    try:
        float(value)
        if "." in value:
            return "float"
        else:
            return "int"
    except ValueError:
        pass
    
    # Default to string
    return "string"

def parse_item_line(line):
    """Parse an item line to extract path, uniqueId, and class."""
    # Pattern: path (uniqueId) [className]
    pattern = r'^(.*?)\s+\(([\w-]+)\)(?:\s+\[(.*?)\])?$'
    match = re.match(pattern, line)
    
    if match:
        path = match.group(1).strip()
        unique_id = match.group(2).strip()
        class_name = match.group(3).strip() if match.group(3) else None
        return path, unique_id, class_name
    
    return None, None, None

def build_item_hierarchy(items):
    """Build a hierarchy of items from flat list."""
    hierarchy = {}
    
    for path, unique_id, class_name, properties in items:
        path_parts = parse_path_components(path)
        
        # Insert into hierarchy
        current = hierarchy
        parent_path = ""
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1:
                # Last part, add the item with its properties
                current[part] = {
                    "unique_id": unique_id,
                    "class_name": class_name,
                    "properties": properties,
                    "children": {}
                }
            else:
                # Intermediate part, create if not exists
                if part not in current:
                    current[part] = {
                        "unique_id": str(uuid.uuid4()),  # Generate a unique ID for missing parents
                        "class_name": "Folder",  # Default class for missing parents
                        "properties": {},
                        "children": {}
                    }
                current = current[part]["children"]
            
            # Build parent path for next iteration
            if parent_path:
                parent_path += "." + part
            else:
                parent_path = part
    
    return hierarchy

def parse_path_components(path):
    """Parse path into components, handling quoted parts."""
    components = []
    i = 0
    
    while i < len(path):
        if path[i:i+2] == '["':
            # Find the closing bracket
            end = path.find('"]', i)
            if end != -1:
                components.append(path[i+2:end])
                i = end + 2
                # Skip the next dot if present
                if i < len(path) and path[i] == '.':
                    i += 1
            else:
                # No closing bracket found, treat as normal text
                components.append(path[i])
                i += 1
        elif path[i] == '.':
            # Skip dots
            i += 1
        else:
            # Find the next dot
            end = path.find('.', i)
            if end != -1:
                components.append(path[i:end])
                i = end + 1
            else:
                # No more dots, add the rest
                components.append(path[i:])
                i = len(path)
    
    return components

def create_item_element(class_name, properties):
    """Create an Item element with the given class and properties."""
    item = ET.Element("Item", {"class": class_name})
    
    # Create properties element
    props_elem = ET.SubElement(item, "Properties")
    
    # Add properties to the properties element
    for name, (value, prop_type) in properties.items():
        if prop_type == "complex":
            # Handle complex properties with nested structure
            complex_prop = ET.SubElement(props_elem, name, {"name": name})
            # Process any sub-properties if needed
            for sub_name, (sub_value, sub_type) in value.items():
                if sub_type != "complex":
                    sub_prop = ET.SubElement(complex_prop, sub_type, {"name": sub_name})
                    sub_prop.text = sub_value
        else:
            # Simple property
            prop_elem = ET.SubElement(props_elem, prop_type, {"name": name})
            prop_elem.text = value
    
    return item

def add_hierarchy_to_xml(parent_elem, hierarchy):
    """Recursively add items from hierarchy to XML."""
    for name, data in hierarchy.items():
        # Create item element
        item = ET.SubElement(parent_elem, "Item", {"class": data["class_name"]})
        
        # Add properties
        props_elem = ET.SubElement(item, "Properties")
        
        # Add Name property
        name_prop = ET.SubElement(props_elem, "string", {"name": "Name"})
        name_prop.text = name
        
        # Add UniqueId property
        uid_prop = ET.SubElement(props_elem, "UniqueId", {"name": "UniqueId"})
        uid_prop.text = data["unique_id"]
        
        # Add other properties
        for prop_name, (prop_value, prop_type) in data["properties"].items():
            if prop_type != "complex":
                prop_elem = ET.SubElement(props_elem, prop_type, {"name": prop_name})
                if prop_value is not None:
                    prop_elem.text = prop_value
            else:
                # Handle complex properties (with nested structure)
                complex_prop = ET.SubElement(props_elem, prop_name, {"name": prop_name})
                if isinstance(prop_value, dict):
                    for sub_name, (sub_value, sub_type) in prop_value.items():
                        sub_prop = ET.SubElement(complex_prop, sub_type, {"name": sub_name})
                        if sub_value is not None:
                            sub_prop.text = sub_value
        
        # Add children recursively
        add_hierarchy_to_xml(item, data["children"])

def parse_markdown_files(input_paths):
    """Parse MD files to extract items and their properties."""
    all_items = []
    
    for input_path in input_paths:
        current_item = None
        current_properties = {}
        prop_indent_level = 0
        complex_prop_stack = []
        
        with open(input_path, 'r') as f:
            for line in f:
                line = line.rstrip()
                
                # Skip empty lines
                if not line.strip():
                    if current_item:
                        # End of an item
                        path, unique_id, class_name = current_item
                        all_items.append((path, unique_id, class_name, current_properties.copy()))
                        current_item = None
                        current_properties = {}
                        complex_prop_stack = []
                    continue
                
                # If not currently parsing an item, check for a new item line
                if not current_item:
                    path, unique_id, class_name = parse_item_line(line)
                    if path:
                        current_item = (path, unique_id, class_name)
                        continue
                
                # If we're parsing an item, look for property lines
                if current_item:
                    # Calculate indentation level
                    indent = len(line) - len(line.lstrip())
                    prop_name, prop_value, is_complex = parse_property_line(line)
                    
                    if prop_name:
                        # Determine property type
                        prop_type = determine_property_type(prop_value)
                        
                        if is_complex == "complex":
                            # Start of a complex property
                            complex_prop_stack.append((prop_name, indent))
                            current_properties[prop_name] = ({}, "complex")
                        elif complex_prop_stack:
                            # We're inside a complex property
                            curr_complex_name, curr_indent = complex_prop_stack[-1]
                            
                            if indent > curr_indent:
                                # This is a sub-property of the current complex property
                                complex_dict = current_properties[curr_complex_name][0]
                                complex_dict[prop_name] = (prop_value, prop_type)
                            else:
                                # Same level as parent or higher, pop back
                                while complex_prop_stack and indent <= complex_prop_stack[-1][1]:
                                    complex_prop_stack.pop()
                                
                                if complex_prop_stack:
                                    # Add to the new current complex property
                                    curr_complex_name, _ = complex_prop_stack[-1]
                                    complex_dict = current_properties[curr_complex_name][0]
                                    complex_dict[prop_name] = (prop_value, prop_type)
                                else:
                                    # No more complex properties, add to main properties
                                    current_properties[prop_name] = (prop_value, prop_type)
                        else:
                            # Add to main properties
                            current_properties[prop_name] = (prop_value, prop_type)
        
        # Don't forget the last item
        if current_item:
            path, unique_id, class_name = current_item
            all_items.append((path, unique_id, class_name, current_properties.copy()))
    
    return all_items

def convert_to_rbxlx(items):
    """Convert parsed items to RBXLX XML."""
    # Create base structure
    root = create_basic_rbxlx_structure()
    
    # Build item hierarchy
    hierarchy = build_item_hierarchy(items)
    
    # Add items to XML
    add_hierarchy_to_xml(root, hierarchy)
    
    return root

def format_xml(root):
    """Format XML with proper indentation."""
    # Convert to string
    rough_string = ET.tostring(root, 'utf-8')
    
    # Parse with minidom and pretty print
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
    parser = argparse.ArgumentParser(description='Convert MD files to Roblox XML (RBXLX) format')
    parser.add_argument('input', nargs='+', help='Input MD file(s) or directory')
    parser.add_argument('--output', '-o', help='Output RBXLX file path (default: output.rbxlx)')
    
    args = parser.parse_args()
    
    # Set default output file if not specified
    if not args.output:
        args.output = "output.rbxlx"
    
    # Collect input files
    input_files = []
    for input_path in args.input:
        if os.path.isdir(input_path):
            # If a directory, collect all .md files
            for file in os.listdir(input_path):
                if file.endswith('.md'):
                    input_files.append(os.path.join(input_path, file))
        elif os.path.isfile(input_path) and input_path.endswith('.md'):
            input_files.append(input_path)
    
    if not input_files:
        print("No valid input files found. Please provide .md files or a directory containing .md files.")
        return
    
    try:
        # Parse MD files
        items = parse_markdown_files(input_files)
        
        # Convert to RBXLX
        root = convert_to_rbxlx(items)
        
        # Format and save XML
        xml_string = format_xml(root)
        with open(args.output, 'w') as f:
            f.write(xml_string)
        
        print(f"Successfully converted {len(input_files)} MD file(s) to {args.output}")
        print(f"Converted {len(items)} items")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 