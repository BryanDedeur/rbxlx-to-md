#!/usr/bin/env python3

import re

def format_property_for_md(prop, indent_level=0):
    """
    Format a property value from XML to Markdown format.
    
    Args:
        prop: An XML Element representing a property
        indent_level: Indentation level for formatting
        
    Returns:
        A formatted string representation of the property
    """
    indent = "  " * indent_level
    result = []
    
    # Get the property name
    prop_name = prop.get("name", "")
    if not prop_name:
        return ""
    
    # Get the property tag (type)
    prop_type = prop.tag
    
    # Handle each property type uniquely
    if prop_type == "string":
        # Handle string properties
        value = prop.text if prop.text else ""
        result.append(f"{indent}- {prop_name}: {value}")
    
    elif prop_type == "bool":
        # Handle boolean properties
        value = prop.text if prop.text else "false"
        result.append(f"{indent}- {prop_name}: {value}")
    
    elif prop_type == "int":
        # Handle integer properties
        value = prop.text if prop.text else "0"
        result.append(f"{indent}- {prop_name}: {value}")
    
    elif prop_type == "int64":
        # Handle 64-bit integer properties
        value = prop.text if prop.text else "0"
        result.append(f"{indent}- {prop_name}: {value}")
    
    elif prop_type == "float" or prop_type == "double":
        # Handle floating-point properties
        value = prop.text if prop.text else "0.0"
        result.append(f"{indent}- {prop_name}: {value}")
    
    elif prop_type == "token":
        # Handle token properties (enumeration values)
        value = prop.text if prop.text else ""
        result.append(f"{indent}- {prop_name}: {value}")
    
    elif prop_type == "Color3uint8":
        # Handle Color3uint8 properties
        r = next((child.text for child in prop if child.tag == "R"), "0")
        g = next((child.text for child in prop if child.tag == "G"), "0")
        b = next((child.text for child in prop if child.tag == "B"), "0")
        result.append(f"{indent}- {prop_name}: RGB({r}, {g}, {b})")
    
    elif prop_type == "Vector3":
        # Handle Vector3 properties
        x = next((child.text for child in prop if child.tag == "X"), "0")
        y = next((child.text for child in prop if child.tag == "Y"), "0")
        z = next((child.text for child in prop if child.tag == "Z"), "0")
        result.append(f"{indent}- {prop_name}: ({x}, {y}, {z})")
    
    elif prop_type == "Vector2":
        # Handle Vector2 properties
        x = next((child.text for child in prop if child.tag == "X"), "0")
        y = next((child.text for child in prop if child.tag == "Y"), "0")
        result.append(f"{indent}- {prop_name}: ({x}, {y})")
    
    elif prop_type == "CFrame" or prop_type == "CoordinateFrame":
        # Handle CFrame/CoordinateFrame properties
        components = []
        for i in range(12):  # CFrame has 12 components
            value = next((child.text for child in prop if child.tag == f"V{i}" or child.tag == f"R{i}"), "0")
            components.append(value)
        result.append(f"{indent}- {prop_name}: CFrame({', '.join(components)})")
    
    elif prop_type == "OptionalCoordinateFrame":
        # Handle OptionalCoordinateFrame properties (may or may not be present)
        if list(prop):  # Check if there are any children elements
            components = []
            for i in range(12):  # CFrame has 12 components
                value = next((child.text for child in prop if child.tag == f"V{i}" or child.tag == f"R{i}"), "0")
                components.append(value)
            result.append(f"{indent}- {prop_name}: CFrame({', '.join(components)})")
        else:
            result.append(f"{indent}- {prop_name}: nil")
    
    elif prop_type == "UDim":
        # Handle UDim properties
        scale = next((child.text for child in prop if child.tag == "S"), "0")
        offset = next((child.text for child in prop if child.tag == "O"), "0")
        result.append(f"{indent}- {prop_name}: Scale: {scale}, Offset: {offset}")
    
    elif prop_type == "UDim2":
        # Handle UDim2 properties
        x_scale = next((child.text for child in prop if child.tag == "XS"), "0")
        x_offset = next((child.text for child in prop if child.tag == "XO"), "0")
        y_scale = next((child.text for child in prop if child.tag == "YS"), "0")
        y_offset = next((child.text for child in prop if child.tag == "YO"), "0")
        result.append(f"{indent}- {prop_name}: X(Scale: {x_scale}, Offset: {x_offset}), Y(Scale: {y_scale}, Offset: {y_offset})")
    
    elif prop_type == "BinaryString" or prop_type == "ProtectedString":
        # Handle binary/protected string properties (often containing scripts or other binary data)
        result.append(f"{indent}- {prop_name}: [Binary Data]")
    
    elif prop_type == "SharedString":
        # Handle SharedString properties (often contain binary data shared between instances)
        value = prop.text if prop.text else ""
        result.append(f"{indent}- {prop_name}: SharedString({value})")
    
    elif prop_type == "Content":
        # Handle Content properties (references to assets)
        value = prop.text if prop.text else ""
        result.append(f"{indent}- {prop_name}: {value}")
    
    elif prop_type == "UniqueId":
        # Handle UniqueId properties
        value = prop.text if prop.text else ""
        result.append(f"{indent}- {prop_name}: {value}")
    
    elif prop_type == "SecurityCapabilities":
        # Handle SecurityCapabilities properties
        value = prop.text if prop.text else "0"
        result.append(f"{indent}- {prop_name}: {value}")
    
    elif prop_type == "Ref" or prop_type == "Reference":
        # Handle references to other objects
        value = prop.text if prop.text else ""
        result.append(f"{indent}- {prop_name}: Ref({value})")
    
    elif prop_type == "Enum":
        # Handle enum properties
        value = prop.text if prop.text else ""
        result.append(f"{indent}- {prop_name}: Enum({value})")
    
    elif prop_type == "NumberSequence":
        # Handle NumberSequence properties
        keypoints = []
        for keypoint in prop.findall(".//Keypoint"):
            time = next((child.text for child in keypoint if child.tag == "Time"), "0")
            value = next((child.text for child in keypoint if child.tag == "Value"), "0")
            envelope = next((child.text for child in keypoint if child.tag == "Envelope"), "0")
            keypoints.append(f"t:{time},v:{value},e:{envelope}")
        result.append(f"{indent}- {prop_name}: NumberSequence({'; '.join(keypoints)})")
    
    elif prop_type == "ColorSequence":
        # Handle ColorSequence properties
        keypoints = []
        for keypoint in prop.findall(".//Keypoint"):
            time = next((child.text for child in keypoint if child.tag == "Time"), "0")
            
            # Get color components
            r = next((child.text for child in keypoint.find("Value") if child.tag == "R"), "0")
            g = next((child.text for child in keypoint.find("Value") if child.tag == "G"), "0")
            b = next((child.text for child in keypoint.find("Value") if child.tag == "B"), "0")
            
            envelope = next((child.text for child in keypoint if child.tag == "Envelope"), "0")
            keypoints.append(f"t:{time},rgb({r},{g},{b}),e:{envelope}")
        result.append(f"{indent}- {prop_name}: ColorSequence({'; '.join(keypoints)})")
    
    elif prop_type == "PhysicalProperties":
        # Handle PhysicalProperties
        density = next((child.text for child in prop if child.tag == "Density"), "0")
        friction = next((child.text for child in prop if child.tag == "Friction"), "0")
        elasticity = next((child.text for child in prop if child.tag == "Elasticity"), "0")
        result.append(f"{indent}- {prop_name}: PhysicalProperties(Density: {density}, Friction: {friction}, Elasticity: {elasticity})")
    
    elif prop_type == "BrickColor":
        # Handle BrickColor properties
        value = prop.text if prop.text else ""
        result.append(f"{indent}- {prop_name}: BrickColor({value})")
    
    elif prop_type == "Color3":
        # Handle Color3 properties (float-based color)
        r = next((child.text for child in prop if child.tag == "R"), "0")
        g = next((child.text for child in prop if child.tag == "G"), "0")
        b = next((child.text for child in prop if child.tag == "B"), "0")
        result.append(f"{indent}- {prop_name}: Color3({r}, {g}, {b})")
    
    elif prop_type == "NumberRange":
        # Handle NumberRange properties
        min_val = next((child.text for child in prop if child.tag == "Min"), "0")
        max_val = next((child.text for child in prop if child.tag == "Max"), "0")
        result.append(f"{indent}- {prop_name}: Range({min_val} to {max_val})")
    
    elif prop_type == "Faces" or prop_type == "Axes":
        # Handle Faces/Axes properties
        faces = []
        for face in ["Top", "Bottom", "Left", "Right", "Front", "Back"]:
            value = next((child.text for child in prop if child.tag == face), "false")
            if value.lower() == "true":
                faces.append(face)
        result.append(f"{indent}- {prop_name}: [{', '.join(faces)}]")
    
    elif prop_type == "Ray":
        # Handle Ray properties
        origin_x = next((child.text for child in prop.find("Origin") if child.tag == "X"), "0")
        origin_y = next((child.text for child in prop.find("Origin") if child.tag == "Y"), "0")
        origin_z = next((child.text for child in prop.find("Origin") if child.tag == "Z"), "0")
        
        direction_x = next((child.text for child in prop.find("Direction") if child.tag == "X"), "0")
        direction_y = next((child.text for child in prop.find("Direction") if child.tag == "Y"), "0")
        direction_z = next((child.text for child in prop.find("Direction") if child.tag == "Z"), "0")
        
        result.append(f"{indent}- {prop_name}: Ray(Origin: ({origin_x}, {origin_y}, {origin_z}), Direction: ({direction_x}, {direction_y}, {direction_z}))")
    
    elif prop_type == "Font":
        # Handle Font properties
        family = next((child.text for child in prop if child.tag == "Family"), "")
        weight = next((child.text for child in prop if child.tag == "Weight"), "")
        style = next((child.text for child in prop if child.tag == "Style"), "")
        result.append(f"{indent}- {prop_name}: Font({family}, {weight}, {style})")
    
    elif prop_type == "Rect2D":
        # Handle Rect2D properties
        min_x = next((child.text for child in prop if child.tag == "min_x"), "0")
        min_y = next((child.text for child in prop if child.tag == "min_y"), "0")
        max_x = next((child.text for child in prop if child.tag == "max_x"), "0")
        max_y = next((child.text for child in prop if child.tag == "max_y"), "0")
        result.append(f"{indent}- {prop_name}: Rect({min_x}, {min_y}, {max_x}, {max_y})")
    
    else:
        # For unsupported property types, print a warning and use generic formatting
        print(f"WARNING: Unsupported property type '{prop_type}' for property '{prop_name}'. Please add support for this type.")
        
        # Generic fallback handling for unknown types
        if not list(prop) and prop.text:  # If there are no child elements and there is text
            result.append(f"{indent}- {prop_name}: {prop.text} [UNSUPPORTED TYPE: {prop_type}]")
        else:
            # For properties with children or nested structure
            result.append(f"{indent}- {prop_name} [UNSUPPORTED TYPE: {prop_type}]")
            for child in prop:
                # If the child has a tag but no name attribute, it's likely a component of a structured property
                if child.get("name") is None:
                    # For component elements like X, Y, Z in Vector3
                    result.append(f"{indent}  - {child.tag}: {child.text if child.text else ''}")
                else:
                    # For named child properties, recursively format them
                    child_value = format_property_for_md(child, indent_level + 1)
                    if child_value:  # Only add non-empty child values
                        result.extend(child_value.split('\n'))
    
    # Skip empty properties
    if not result:
        return ""
    
    return '\n'.join(result)

def extract_properties(item):
    """
    Extract all properties from an item and return them as a formatted string.
    
    Args:
        item: An XML Element representing an item
        
    Returns:
        A formatted string with all the properties
    """
    properties_elem = item.find("Properties")
    if properties_elem is None:
        return ""
    
    # Properties to skip (already handled elsewhere)
    skip_properties = {"Name"}  # Skip Name property since it's already in the path
    
    result = []
    for prop in sorted(properties_elem, key=lambda x: x.get("name", "")):
        prop_name = prop.get("name", "")
        
        # Skip properties we don't want to include
        if prop_name in skip_properties:
            continue
        
        # Skip empty properties for certain types that are not useful
        if prop_name in ["AttributesSerialize", "Tags"] and (not prop.text or not prop.text.strip()):
            continue
            
        prop_value = format_property_for_md(prop)
        if prop_value:  # Only add non-empty property values
            result.append(prop_value)
    
    return "\n".join(result)

def create_xml_property(element_type, prop_name, prop_value, parent=None):
    """
    Create an XML property element from property details.
    
    Args:
        element_type: The type of the property (string, int, etc.)
        prop_name: The name of the property
        prop_value: The value of the property
        parent: Optional parent Element to append to
        
    Returns:
        An ElementTree Element representing the property
    """
    import xml.etree.ElementTree as ET
    
    # Create the property element
    prop = ET.Element(element_type)
    prop.set("name", prop_name)
    
    # Handle different property types
    if element_type in ["string", "bool", "int", "int64", "float", "double", "token", 
                         "Content", "UniqueId", "SecurityCapabilities", "Enum", "BrickColor"]:
        # Simple types with direct text content
        prop.text = str(prop_value)
    
    elif element_type == "Color3uint8":
        # Color3uint8 with R, G, B components
        if isinstance(prop_value, tuple) and len(prop_value) == 3:
            r, g, b = prop_value
            r_elem = ET.SubElement(prop, "R")
            r_elem.text = str(r)
            g_elem = ET.SubElement(prop, "G")
            g_elem.text = str(g)
            b_elem = ET.SubElement(prop, "B")
            b_elem.text = str(b)
    
    elif element_type == "Vector3":
        # Vector3 with X, Y, Z components
        if isinstance(prop_value, tuple) and len(prop_value) == 3:
            x, y, z = prop_value
            x_elem = ET.SubElement(prop, "X")
            x_elem.text = str(x)
            y_elem = ET.SubElement(prop, "Y")
            y_elem.text = str(y)
            z_elem = ET.SubElement(prop, "Z")
            z_elem.text = str(z)
    
    elif element_type == "Vector2":
        # Vector2 with X, Y components
        if isinstance(prop_value, tuple) and len(prop_value) == 2:
            x, y = prop_value
            x_elem = ET.SubElement(prop, "X")
            x_elem.text = str(x)
            y_elem = ET.SubElement(prop, "Y")
            y_elem.text = str(y)
    
    elif element_type in ["CFrame", "CoordinateFrame"]:
        # CFrame with 12 components
        if isinstance(prop_value, tuple) and len(prop_value) == 12:
            for i, val in enumerate(prop_value):
                v_elem = ET.SubElement(prop, f"R{i}")
                v_elem.text = str(val)
    
    elif element_type == "UDim":
        # UDim with Scale and Offset
        if isinstance(prop_value, tuple) and len(prop_value) == 2:
            scale, offset = prop_value
            s_elem = ET.SubElement(prop, "S")
            s_elem.text = str(scale)
            o_elem = ET.SubElement(prop, "O")
            o_elem.text = str(offset)
    
    elif element_type == "UDim2":
        # UDim2 with X and Y scales and offsets
        if isinstance(prop_value, tuple) and len(prop_value) == 4:
            xs, xo, ys, yo = prop_value
            xs_elem = ET.SubElement(prop, "XS")
            xs_elem.text = str(xs)
            xo_elem = ET.SubElement(prop, "XO")
            xo_elem.text = str(xo)
            ys_elem = ET.SubElement(prop, "YS")
            ys_elem.text = str(ys)
            yo_elem = ET.SubElement(prop, "YO")
            yo_elem.text = str(yo)
    
    elif element_type in ["BinaryString", "ProtectedString", "SharedString"]:
        # Binary data
        prop.text = str(prop_value)
    
    elif element_type == "Ref" or element_type == "Reference":
        # Reference to other objects
        prop.text = str(prop_value)
    
    elif element_type == "Color3":
        # Color3 with R, G, B components (float)
        if isinstance(prop_value, tuple) and len(prop_value) == 3:
            r, g, b = prop_value
            r_elem = ET.SubElement(prop, "R")
            r_elem.text = str(r)
            g_elem = ET.SubElement(prop, "G")
            g_elem.text = str(g)
            b_elem = ET.SubElement(prop, "B")
            b_elem.text = str(b)
    
    elif element_type == "NumberRange":
        # NumberRange with Min and Max
        if isinstance(prop_value, tuple) and len(prop_value) == 2:
            min_val, max_val = prop_value
            min_elem = ET.SubElement(prop, "Min")
            min_elem.text = str(min_val)
            max_elem = ET.SubElement(prop, "Max")
            max_elem.text = str(max_val)
    
    elif element_type in ["Faces", "Axes"]:
        # Faces/Axes with boolean values
        if isinstance(prop_value, list):
            all_faces = ["Top", "Bottom", "Left", "Right", "Front", "Back"]
            for face in all_faces:
                face_elem = ET.SubElement(prop, face)
                face_elem.text = "true" if face in prop_value else "false"
    
    elif element_type == "Ray":
        # Ray with Origin and Direction
        if isinstance(prop_value, tuple) and len(prop_value) == 6:
            ox, oy, oz, dx, dy, dz = prop_value
            origin = ET.SubElement(prop, "Origin")
            origin_x = ET.SubElement(origin, "X")
            origin_x.text = str(ox)
            origin_y = ET.SubElement(origin, "Y")
            origin_y.text = str(oy)
            origin_z = ET.SubElement(origin, "Z")
            origin_z.text = str(oz)
            
            direction = ET.SubElement(prop, "Direction")
            direction_x = ET.SubElement(direction, "X")
            direction_x.text = str(dx)
            direction_y = ET.SubElement(direction, "Y")
            direction_y.text = str(dy)
            direction_z = ET.SubElement(direction, "Z")
            direction_z.text = str(dz)
    
    elif element_type == "Font":
        # Font with Family, Weight, Style
        if isinstance(prop_value, tuple) and len(prop_value) == 3:
            family, weight, style = prop_value
            family_elem = ET.SubElement(prop, "Family")
            family_elem.text = str(family)
            weight_elem = ET.SubElement(prop, "Weight")
            weight_elem.text = str(weight)
            style_elem = ET.SubElement(prop, "Style")
            style_elem.text = str(style)
    
    elif element_type == "Rect2D":
        # Rect2D with min_x, min_y, max_x, max_y
        if isinstance(prop_value, tuple) and len(prop_value) == 4:
            min_x, min_y, max_x, max_y = prop_value
            min_x_elem = ET.SubElement(prop, "min_x")
            min_x_elem.text = str(min_x)
            min_y_elem = ET.SubElement(prop, "min_y")
            min_y_elem.text = str(min_y)
            max_x_elem = ET.SubElement(prop, "max_x")
            max_x_elem.text = str(max_x)
            max_y_elem = ET.SubElement(prop, "max_y")
            max_y_elem.text = str(max_y)
    
    # Append to parent if provided
    if parent is not None:
        parent.append(prop)
        
    return prop

def parse_property_from_md(prop_line):
    """
    Parse a property from a markdown line into a tuple of (type, name, value).
    
    Args:
        prop_line: A string representing a property line from markdown
        
    Returns:
        A tuple of (type, name, value) where type is inferred from the value format
    """
    # Check if the line looks like a property line
    if not prop_line.strip().startswith('-'):
        return None
    
    # Extract property name and value
    # Format: "- PropertyName: PropertyValue"
    parts = prop_line.strip()[2:].split(':', 1)
    if len(parts) != 2:
        return None
    
    prop_name = parts[0].strip()
    prop_value = parts[1].strip()
    
    # Infer type from value format
    prop_type = None
    actual_value = None
    
    # Boolean
    if prop_value.lower() in ['true', 'false']:
        prop_type = 'bool'
        actual_value = prop_value.lower()
    
    # Integer
    elif prop_value.isdigit() or (prop_value.startswith('-') and prop_value[1:].isdigit()):
        # Check if large number (int64)
        if abs(int(prop_value)) > 2147483647:
            prop_type = 'int64'
        else:
            prop_type = 'int'
        actual_value = prop_value
    
    # Float
    elif re.match(r'^-?\d+\.\d+$', prop_value):
        prop_type = 'float'
        actual_value = prop_value
    
    # RGB Color3uint8
    elif re.match(r'^RGB\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$', prop_value):
        prop_type = 'Color3uint8'
        rgb_match = re.search(r'RGB\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', prop_value)
        if rgb_match:
            r, g, b = rgb_match.groups()
            actual_value = (r, g, b)
    
    # Vector3
    elif re.match(r'^\(\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*\)$', prop_value):
        prop_type = 'Vector3'
        vector_match = re.search(r'\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)', prop_value)
        if vector_match:
            x, y, z = vector_match.groups()
            actual_value = (x, y, z)
    
    # Vector2
    elif re.match(r'^\(\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*\)$', prop_value):
        prop_type = 'Vector2'
        vector_match = re.search(r'\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)', prop_value)
        if vector_match:
            x, y = vector_match.groups()
            actual_value = (x, y)
    
    # CFrame
    elif prop_value.startswith('CFrame('):
        prop_type = 'CFrame'
        cframe_match = re.search(r'CFrame\((.*)\)', prop_value)
        if cframe_match:
            components = cframe_match.group(1).split(',')
            components = [c.strip() for c in components]
            if len(components) == 12:
                actual_value = tuple(components)
    
    # UDim
    elif 'Scale:' in prop_value and 'Offset:' in prop_value:
        prop_type = 'UDim'
        scale_match = re.search(r'Scale:\s*(-?\d+(?:\.\d+)?)', prop_value)
        offset_match = re.search(r'Offset:\s*(-?\d+(?:\.\d+)?)', prop_value)
        if scale_match and offset_match:
            scale = scale_match.group(1)
            offset = offset_match.group(1)
            actual_value = (scale, offset)
    
    # Special handling for other types
    elif '[Binary Data]' in prop_value:
        prop_type = 'BinaryString'
        actual_value = ""
    
    elif prop_value.startswith('SharedString('):
        prop_type = 'SharedString'
        shared_match = re.search(r'SharedString\((.*)\)', prop_value)
        if shared_match:
            actual_value = shared_match.group(1)
    
    elif prop_value.startswith('Ref('):
        prop_type = 'Ref'
        ref_match = re.search(r'Ref\((.*)\)', prop_value)
        if ref_match:
            actual_value = ref_match.group(1)
    
    elif prop_value.startswith('Enum('):
        prop_type = 'Enum'
        enum_match = re.search(r'Enum\((.*)\)', prop_value)
        if enum_match:
            actual_value = enum_match.group(1)
    
    elif prop_value.startswith('BrickColor('):
        prop_type = 'BrickColor'
        brick_match = re.search(r'BrickColor\((.*)\)', prop_value)
        if brick_match:
            actual_value = brick_match.group(1)
    
    elif prop_value.startswith('Color3('):
        prop_type = 'Color3'
        color_match = re.search(r'Color3\((.*)\)', prop_value)
        if color_match:
            components = color_match.group(1).split(',')
            components = [c.strip() for c in components]
            if len(components) == 3:
                actual_value = tuple(components)
    
    # Default to string for everything else
    else:
        prop_type = 'string'
        actual_value = prop_value
    
    return (prop_type, prop_name, actual_value) 