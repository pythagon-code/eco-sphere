from ursina import vec3
from globals import *
import math
from ursina import *
from utils import *

app = Ursina()

globe = Entity(model="sphere", color=color.gray, scale=4, collider="sphere")

draw_globe_line(globe=globe, rho=0.5, color=color.cyan, size=0.008, num_markers=50, phi=math.pi/2)
draw_globe_line(globe=globe, rho=0.5, color=color.cyan, size=0.008, num_markers=50, phi=math.pi)
draw_globe_line(globe=globe, rho=0.5, color=color.cyan, size=0.008, num_markers=50, theta=math.pi/2)
left_mouse_pressed = False
mouse_position = Vec3(0, 0)
camera.parent = globe

def input(key: str) -> None:
    global left_mouse_pressed, mouse_position, camera_distance
    if key == "left mouse down":
        mouse_position = mouse.position
        left_mouse_pressed = True
    elif key == "left mouse up":
        left_mouse_pressed = False
    if key == "scroll up":
        camera_distance += camera_zoom_speed
    elif key == "scroll down":
        camera_distance = max(camera_distance - camera_zoom_speed, 0)

camera.position = Vec3(spherical_to_cartesian(camera_distance, camera_phi, camera_theta))
camera.look_at(globe.position)

def update() -> None:
    global mouse_position, camera_phi, camera_theta
    if left_mouse_pressed:
        mouse_delta = mouse.position - mouse_position
        mouse_position = mouse.position
        rotate_speed = camera_rotate_speed * (camera_distance - 0.5)
        camera_phi = camera_phi - mouse_delta.x * rotate_speed
        camera_theta = clamp(camera_theta + mouse_delta.y * rotate_speed, .01, math.pi - .01)
    camera.position = Vec3(spherical_to_cartesian(camera_distance, camera_phi, camera_theta))
    camera.rotation_z = 0
    camera.look_at(globe.position)

    if mouse.hovered_entity:
        print(mouse.hovered_entity.name)

draw_boundaries(globe, radius=0.501, col=color.turquoise)
draw_centroids(globe, radius=0.501, col=color.light_gray, size=0.02)
print(countries)

app.run()