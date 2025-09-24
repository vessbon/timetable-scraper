def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def closest_color_id(hex_code, google_colors):
    target_rgb = hex_to_rgb(hex_code)
    min_distance = float("inf")
    closest_id = None

    for color_id, data in google_colors.items():
        rgb = hex_to_rgb(data['background'])
        distance = sum((a - b) ** 2 for a, b in zip(target_rgb, rgb)) ** 0.5
        if distance < min_distance:
            min_distance = distance
            closest_id = color_id

    return closest_id
