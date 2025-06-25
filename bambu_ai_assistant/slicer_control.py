import zipfile
import os
import shutil
import xml.etree.ElementTree as ET
from itertools import combinations
import math

MODELS_DIR = "models"
OUTPUTS_DIR = "outputs"

def handle_command(command):
    command = command.lower()

    if "scale" in command:
        scale_factor = extract_scale(command)
        if not scale_factor:
            return "Couldn't detect scale value."
        model = find_latest_model()
        if not model:
            return "No .3MF model found."
        output = os.path.join(OUTPUTS_DIR, f"scaled_{os.path.basename(model)}")
        scale_model(model, output, scale_factor)
        return f"Model scaled by {scale_factor}x and saved to outputs."

    elif "material" in command or "filament" in command:
        material = extract_material(command)
        if not material:
            return "Specify material like PLA, PETG-CF, etc."
        model = find_latest_model()
        output = os.path.join(OUTPUTS_DIR, f"material_{material}_{os.path.basename(model)}")
        change_material(model, output, material)
        return f"Material changed to {material} and saved."

    elif "printer" in command:
        if "a1" in command:
            printer = "Bambu A1"
        elif "x1" in command:
            printer = "Bambu X1 Carbon"
        elif "p1" in command:
            printer = "Bambu P1P"
        else:
            return "Unknown printer model."
        model = find_latest_model()
        output = os.path.join(OUTPUTS_DIR, f"printer_{printer.replace(' ', '_')}_{os.path.basename(model)}")
        set_printer(model, output, printer)
        return f"Printer set to {printer}."

    elif "check" in command or "problem" in command or "printable" in command:
        model = find_latest_model()
        return check_model_problems(model)

    elif "move" in command or "position" in command or "center" in command:
        model = find_latest_model()
        dx, dy, dz = extract_offset(command)
        output = os.path.join(OUTPUTS_DIR, f"moved_{os.path.basename(model)}")
        reposition_model(model, output, dx, dy, dz)
        return f"Model repositioned (dx={dx}, dy={dy}, dz={dz}) and saved."

    elif "rotate" in command:
        angle = extract_rotation(command)
        if angle is None:
            return "Please specify angle like 90, 180, or 270."
        model = find_latest_model()
        output = os.path.join(OUTPUTS_DIR, f"rotated_{angle}_{os.path.basename(model)}")
        rotate_model(model, output, angle)
        return f"Model rotated {angle}° around Z axis."

    return "Unknown command. Try: scale, rotate, material, check, move, set printer."

def extract_scale(text):
    import re
    match = re.search(r"(\d+)(?:%|x)?", text)
    if match:
        value = int(match.group(1))
        return round(value / 100, 2) if "%" in text else float(value)
    return None

def extract_material(text):
    materials = ["pla", "pla-cf", "petg", "petg-cf", "abs", "asa", "tpu", "paht", "pc", "carbon fiber"]
    for mat in materials:
        if mat in text:
            return mat.upper()
    return None

def extract_rotation(text):
    import re
    match = re.search(r"(\d{2,3})", text)
    if match:
        return int(match.group(1))
    return None

def extract_offset(text):
    # Defaults to center if no offset is mentioned
    if "center" in text:
        return "center", "center", 0
    import re
    dx = dy = dz = 0
    for axis in ['x', 'y', 'z']:
        m = re.search(rf"{axis}(-?\d+)", text)
        if m:
            val = int(m.group(1))
            if axis == 'x': dx = val
            if axis == 'y': dy = val
            if axis == 'z': dz = val
    return dx, dy, dz

def find_latest_model():
    files = [f for f in os.listdir(MODELS_DIR) if f.endswith(".3mf")]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(os.path.join(MODELS_DIR, f)), reverse=True)
    return os.path.join(MODELS_DIR, files[0])

def scale_model(input_path, output_path, factor):
    with zipfile.ZipFile(input_path, 'r') as zin:
        zin.extractall("temp_scale")
    path = "temp_scale/3D/3dmodel.model"
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    for v in root.findall(".//m:vertex", ns):
        for axis in ['x', 'y', 'z']:
            val = float(v.attrib[axis])
            v.attrib[axis] = str(round(val * factor, 5))
    tree.write(path)
    with zipfile.ZipFile(output_path, 'w') as zout:
        for f, _, files in os.walk("temp_scale"):
            for file in files:
                full = os.path.join(f, file)
                arc = os.path.relpath(full, "temp_scale")
                zout.write(full, arc)
    shutil.rmtree("temp_scale")

def change_material(input_path, output_path, material_code):
    with zipfile.ZipFile(input_path, 'r') as zin:
        zin.extractall("temp_mat")
    path = "temp_mat/metadata/print.config"
    if not os.path.exists(path):
        raise Exception("print.config missing.")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if "filament_type" in line:
            new_lines.append(f'filament_type = "{material_code}"\n')
        else:
            new_lines.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    with zipfile.ZipFile(output_path, 'w') as zout:
        for f, _, files in os.walk("temp_mat"):
            for file in files:
                full = os.path.join(f, file)
                arc = os.path.relpath(full, "temp_mat")
                zout.write(full, arc)
    shutil.rmtree("temp_mat")

def set_printer(input_path, output_path, printer_name):
    with zipfile.ZipFile(input_path, 'r') as zin:
        zin.extractall("temp_printer")
    path = "temp_printer/metadata/print.config"
    if not os.path.exists(path):
        raise Exception("print.config missing.")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if "printer_type" in line:
            new_lines.append(f'printer_type = "{printer_name}"\n')
        else:
            new_lines.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    with zipfile.ZipFile(output_path, 'w') as zout:
        for f, _, files in os.walk("temp_printer"):
            for file in files:
                full = os.path.join(f, file)
                arc = os.path.relpath(full, "temp_printer")
                zout.write(full, arc)
    shutil.rmtree("temp_printer")

def check_model_problems(model_path):
    with zipfile.ZipFile(model_path, 'r') as zin:
        zin.extractall("temp_check")
    model_file = "temp_check/3D/3dmodel.model"
    if not os.path.exists(model_file):
        shutil.rmtree("temp_check")
        return "Model file missing."
    tree = ET.parse(model_file)
    root = tree.getroot()
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    problems = []
    objects = []
    for obj in root.findall(".//m:object", ns):
        verts = [(float(v.attrib['x']), float(v.attrib['y']), float(v.attrib['z']))
                 for v in obj.findall(".//m:vertex", ns)]
        if verts:
            objects.append(verts)
    if not objects:
        return "Empty model."
    bed = (256, 256, 256)
    for i, verts in enumerate(objects):
        min_z = min(z for _, _, z in verts)
        max_x = max(x for x, _, _ in verts)
        max_y = max(y for _, y, _ in verts)
        max_z = max(z for _, _, z in verts)
        if min_z > 1:
            problems.append(f"Object {i+1} is floating above bed.")
        if max_x > bed[0] or max_y > bed[1] or max_z > bed[2]:
            problems.append(f"Object {i+1} exceeds bed volume.")
    for i, j in combinations(range(len(objects)), 2):
        a = objects[i]
        b = objects[j]
        a_bounds = get_bounds(a)
        b_bounds = get_bounds(b)
        if boxes_overlap(a_bounds, b_bounds):
            problems.append(f"Objects {i+1} and {j+1} are overlapping.")
    shutil.rmtree("temp_check")
    return "✅ Model looks good!" if not problems else "⚠️ Issues:\n- " + "\n- ".join(problems)

def get_bounds(verts):
    return (
        min(x for x, _, _ in verts), max(x for x, _, _ in verts),
        min(y for _, y, _ in verts), max(y for _, y, _ in verts),
        min(z for _, _, z in verts), max(z for _, _, z in verts)
    )

def boxes_overlap(a, b):
    return (a[1] > b[0] and b[1] > a[0]) and \
           (a[3] > b[2] and b[3] > a[2]) and \
           (a[5] > b[4] and b[5] > a[4])

def reposition_model(input_path, output_path, dx, dy, dz):
    with zipfile.ZipFile(input_path, 'r') as zin:
        zin.extractall("temp_move")
    path = "temp_move/3D/3dmodel.model"
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    verts = root.findall(".//m:vertex", ns)
    if dx == "center":
        min_x = min(float(v.attrib["x"]) for v in verts)
        min_y = min(float(v.attrib["y"]) for v in verts)
        max_x = max(float(v.attrib["x"]) for v in verts)
        max_y = max(float(v.attrib["y"]) for v in verts)
        dx = 128 - ((min_x + max_x) / 2)
        dy = 128 - ((min_y + max_y) / 2)
    for v in verts:
        v.attrib["x"] = str(round(float(v.attrib["x"]) + dx, 3))
        v.attrib["y"] = str(round(float(v.attrib["y"]) + dy, 3))
        v.attrib["z"] = str(round(float(v.attrib["z"]) + dz, 3))
    tree.write(path)
    with zipfile.ZipFile(output_path, 'w') as zout:
        for f, _, files in os.walk("temp_move"):
            for file in files:
                full = os.path.join(f, file)
                arc = os.path.relpath(full, "temp_move")
                zout.write(full, arc)
    shutil.rmtree("temp_move")

def rotate_model(input_path, output_path, angle_deg):
    angle = math.radians(angle_deg)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    with zipfile.ZipFile(input_path, 'r') as zin:
        zin.extractall("temp_rot")
    path = "temp_rot/3D/3dmodel.model"
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    verts = root.findall(".//m:vertex", ns)
    for v in verts:
        x = float(v.attrib["x"])
        y = float(v.attrib["y"])
        new_x = x * cos_a - y * sin_a
        new_y = x * sin_a + y * cos_a
        v.attrib["x"] = str(round(new_x, 3))
        v.attrib["y"] = str(round(new_y, 3))
    tree.write(path)
    with zipfile.ZipFile(output_path, 'w') as zout:
        for f, _, files in os.walk("temp_rot"):
            for file in files:
                full = os.path.join(f, file)
                arc = os.path.relpath(full, "temp_rot")
                zout.write(full, arc)
    shutil.rmtree("temp_rot")
