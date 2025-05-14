#!/usr/bin/env python3

import argparse
import os
import re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from property_handlers import parse_property_from_md, create_xml_property

def parse_name_and_id(line):
    """Parse the name, ID, and optional class name from a line."""
    # Match pattern: path (id) [class]
    match = re.match(r'(.+?)\s*\(([^)]+)\)(?:\s*\[([^]]+)\])?', line)
    if match:
        path = match.group(1).strip()
        unique_id = match.group(2).strip()
        class_name = match.group(3).strip() if match.group(3) else None
        return path, unique_id, class_name
    return None, None, None

def get_name_from_path(path):
    """Extract the name of the item from the path."""
    # Handle paths with special characters and spaces
    quoted_name_match = re.search(r'\["([^"]+)"\]$', path)
    if quoted_name_match:
        return quoted_name_match.group(1)
    
    # Regular path with dot notation
    parts = path.split('.')
    return parts[-1] if parts else path

def parse_md_file(file_path):
    """Parse a markdown file and extract item data."""
    items = []
    current_item = None
    properties = []
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.rstrip()
            
            # Skip empty lines
            if not line:
                if current_item:
                    # Add the current item and its properties to the list
                    items.append((current_item, properties))
                    current_item = None
                    properties = []
                continue
            
            # Check if this is a new item line
            path, unique_id, class_name = parse_name_and_id(line)
            if path:
                if current_item:
                    # Save the previous item
                    items.append((current_item, properties))
                    properties = []
                
                current_item = {
                    'path': path,
                    'id': unique_id,
                    'class': class_name or 'Part'  # Default to Part if class is not specified
                }
            elif line.startswith('- ') and current_item:
                # This is a property line
                properties.append(line)
    
    # Add the last item if there is one
    if current_item:
        items.append((current_item, properties))
    
    return items

def build_item_hierarchy(items):
    """Build a hierarchy of items based on their paths."""
    hierarchy = {}
    
    for item, properties in items:
        path = item['path']
        parts = re.split(r'\.(?![^"]*")', path)  # Split by dots, but not within quotes
        
        # Extract the name from the last part (handle quoted names)
        name = get_name_from_path(parts[-1])
        
        # Remove any escaped characters
        name = name.replace('\\"', '"')
        
        current_level = hierarchy
        parent_path = ""
        
        # Navigate to the correct level in the hierarchy
        for i, part in enumerate(parts[:-1]):
            parent_path = parent_path + part if i == 0 else parent_path + "." + part
            if part not in current_level:
                # Create a placeholder for this level
                current_level[part] = {'__children__': {}, '__path__': parent_path}
            current_level = current_level[part]['__children__']
        
        # Add this item to the current level
        current_level[parts[-1]] = {
            '__item__': item,
            '__properties__': properties,
            '__children__': {},
            '__name__': name,
            '__path__': path
        }
    
    return hierarchy

def create_xml_tree(hierarchy):
    """Create an XML tree from the item hierarchy."""
    # Create the root element
    root = ET.Element('roblox')
    root.set('xmlns:xmime', 'http://www.w3.org/2005/05/xmlmime')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:noNamespaceSchemaLocation', 'http://www.roblox.com/roblox.xsd')
    root.set('version', '4')
    
    # Dictionary to track all items by ID
    items_by_id = {}
    
    # Process each high-level item
    for _, high_level_data in hierarchy.items():
        process_item_for_xml(high_level_data, root, None, items_by_id)
    
    return root

def process_item_for_xml(item_data, xml_root, parent_xml, items_by_id):
    """Process an item and its children recursively."""
    # Skip placeholder items without actual data
    if '__item__' not in item_data:
        # Process children of placeholder
        for child_name, child_data in item_data.get('__children__', {}).items():
            process_item_for_xml(child_data, xml_root, parent_xml, items_by_id)
        return
    
    # Create an XML element for this item
    item_xml = ET.SubElement(xml_root, 'Item')
    item_xml.set('class', item_data['__item__']['class'])
    
    # Add properties element
    properties_xml = ET.SubElement(item_xml, 'Properties')
    
    # Add Name property
    name_xml = create_xml_property('string', 'Name', item_data['__name__'], properties_xml)
    
    # Add UniqueId property
    id_xml = create_xml_property('UniqueId', 'UniqueId', item_data['__item__']['id'], properties_xml)
    
    # Process other properties
    for prop_line in item_data['__properties__']:
        prop_info = parse_property_from_md(prop_line)
        if prop_info:
            prop_type, prop_name, prop_value = prop_info
            create_xml_property(prop_type, prop_name, prop_value, properties_xml)
    
    # Store this item by ID for referencing
    items_by_id[item_data['__item__']['id']] = item_xml
    
    # If this item has a parent in our structure, add a reference
    if parent_xml is not None:
        item_xml.set('referent', item_data['__item__']['id'])
    
    # Process children
    for child_name, child_data in item_data.get('__children__', {}).items():
        process_item_for_xml(child_data, xml_root, item_xml, items_by_id)

def format_xml(root):
    """Format the XML with proper indentation."""
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
    parser = argparse.ArgumentParser(description='Convert markdown files back to Roblox XML format')
    parser.add_argument('input_dir', help='Path to directory containing markdown files')
    parser.add_argument('--output', '-o', help='Output XML file path')
    parser.add_argument('--include-dirs', '-i', nargs='+', help='Directories to include (default: all)')
    
    args = parser.parse_args()
    
    # Set default output file if not specified
    if not args.output:
        args.output = 'output.rbxlx'
    
    # Get list of markdown files
    md_files = []
    for root, _, files in os.walk(args.input_dir):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    
    if not md_files:
        print(f"No markdown files found in {args.input_dir}")
        return
    
    # Parse all markdown files
    all_items = []
    for md_file in md_files:
        items = parse_md_file(md_file)
        all_items.extend(items)
    
    # Build hierarchy
    hierarchy = build_item_hierarchy(all_items)
    
    # Create XML tree
    xml_root = create_xml_tree(hierarchy)
    
    # Write output XML
    formatted_xml = format_xml(xml_root)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(formatted_xml)
    
    print(f"Successfully wrote {len(all_items)} items to {args.output}")

if __name__ == "__main__":
    main() 