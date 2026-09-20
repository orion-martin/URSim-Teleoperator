import math

FIXED_ORIENT = [0.0, 3.14159, 0.0]  # tool pointing down (axis-angle, rad) — verify for your tool

# this comes in after filter
def wrist_map_to_robot(d):
    rx = d[0]
    ry = d[1]
    rz = d[2]

    return [-rz, rx, -ry, *FIXED_ORIENT]