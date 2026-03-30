from globals import *
import math
from ursina import *
from utils import *
app = Ursina()

window.color = add_hsv(color.white, (0, -.1, -.4))
globe = Entity(model="sphere", color=add_hsv(color.dark_gray, (0, 0, -.12)), scale=4, name="globe")
gui = None
hovered_country = None
hovered_country_name = None
hovered_country_info_text = None
similarity_scores = {}
similarity_signature = None
selected_countries = []
selected_country = None
unselected_country = None

draw_globe_line(globe=globe, rho=0.5, color=color.white, alpha=.6, size=0.004, num_markers=100, theta=math.pi/2)
Entity(model="sphere", color=color.white, scale=0.008, position=Vec3(0, 0.5, 0), parent=globe)
Entity(model="sphere", color=color.white, scale=0.008, position=Vec3(0, -0.5, 0), parent=globe)
left_mouse_pressed = False
mouse_position = Vec3(0, 0)
camera.parent = globe

def unselect_all() -> None:
    global selected_countries, selected_country, unselected_country
    for country in selected_countries:
        country.alpha = .6
        country.scale = .02
    selected_countries.clear()
    selected_country = None
    unselected_country = None

unselect_all_button_base_color = add_hsv(color.dark_gray, (0, 0, -.8))
unselect_all_button_hover_color = color.dark_gray
log_scale_button_base_color = add_hsv(color.dark_gray, (0, 0, -.8))
log_scale_button_hover_color = color.dark_gray
use_log_scale = True

unselect_all_button = Button(
    text="Unselect All",
    scale=Vec2(.2, .07),
    position=Vec2(-.7, -0.35),
    color=unselect_all_button_base_color,
    highlight_color=unselect_all_button_hover_color,
    text_color=color.white,
    alpha=.5,
    on_click=unselect_all,
)

def toggle_log_scale() -> None:
    global use_log_scale
    use_log_scale = not use_log_scale
    if use_log_scale:
        log_scale_button.text = "Log Scale: On"
    else:
        log_scale_button.text = "Log Scale: Off"
    apply_year_colors(int(year_slider.value) - year_base, log_scale=use_log_scale)

log_scale_button = Button(
    text="Log Scale: On",
    scale=Vec2(.2, .07),
    position=Vec2(-.7, -0.45),
    color=log_scale_button_base_color,
    highlight_color=log_scale_button_hover_color,
    text_color=color.white,
    alpha=.5,
    on_click=toggle_log_scale,
)

year_slider = Slider(
    parent=camera.ui,
    min=1960,
    max=2025,
    default=2000,
    step=1,
    origin=Vec2(.5, .5),
    text_color=color.white,
    position=(-.25, -.45),
)
year_slider_label = Text(
    parent=camera.ui,
    text="Year",
    color=color.white,
    scale=1.5,
    origin=Vec2(.5, .5),
    position=Vec2(.05, -.37),
)

legend_panel = Entity(
    parent = camera.ui,
    model = "quad",
    color = color.black,
    alpha = .45,
    scale = Vec2(.40, .40),
    position = Vec2(.62, -.22),
)
legend_title = Text(
    parent = legend_panel,
    text = "GDP Legend",
    color = color.white,
    scale = 4,
    origin = Vec2(0, 0),
    position = Vec2(.0, .4),
)
legend_points = []
legend_values = []
legend_num_steps = 7
for i in range(legend_num_steps):
    y_pos = .2 - i * .09
    step = i / (legend_num_steps - 1)
    point = Entity(
        parent = legend_panel,
        model = "circle",
        color = add_hsv(color.red, (step * 360, 0, 0)),
        scale = (.07, .07),
        origin = Vec2(.0, .0),
        position = Vec2(-.12, y_pos),
    )
    value = Text(
        parent = legend_panel,
        text = "0",
        color = color.white,
        scale = 2.2,
        origin = Vec2(.0, .0),
        position = Vec2(.1, y_pos),
    )
    legend_points.append(point)
    legend_values.append(value)

year_base = 1960
current_year_index = None

def format_gdp_value(gdp_value: float) -> str:
    if gdp_value >= 1000000000000:
        return f"{gdp_value / 1000000000000:.1f}T"
    if gdp_value >= 1000000000:
        return f"{gdp_value / 1000000000:.1f}B"
    if gdp_value >= 1000000:
        return f"{gdp_value / 1000000:.1f}M"
    return f"{gdp_value:.0f}"

def get_country_gdp_info_text(country_name: str) -> str:
    if country_name not in gdps:
        return f"{country_name}\nGDP: N/A"
    if current_year_index is None:
        return f"{country_name}\nGDP: N/A"
    country_gdp_values = gdps[country_name]
    if current_year_index < 0 or current_year_index >= len(country_gdp_values):
        return f"{country_name}\nGDP: N/A"
    gdp_value = country_gdp_values[current_year_index]
    info_text = f"{country_name}\nGDP: {format_gdp_value(gdp_value)}"
    if similarity_scores:
        similarity_value = similarity_scores.get(country_name)
        if similarity_value is not None:
            info_text += f"\nSimilarity: {similarity_value:.3f}"
    return info_text

def apply_legend_values(year_index: int, log_scale: bool = True) -> None:
    print(f"applying legend values for year {year_index}")
    gdp_values = sorted(gdp[year_index] for gdp in gdps.values())
    if not gdp_values:
        return
    gdp_max = gdp_values[-1]
    gdp_scale_max = math.log1p(gdp_max) if log_scale else gdp_max
    for i in range(legend_num_steps):
        step = i / (legend_num_steps - 1)
        legend_points[i].color = add_hsv(color.red, (step * 340, 0, 0))
        scaled_value = step * gdp_scale_max
        gdp_value = math.expm1(scaled_value) if log_scale else scaled_value
        legend_values[i].text = format_gdp_value(gdp_value)

def apply_year_colors(year_index: int, log_scale: bool = True) -> None:
    global current_year_index
    if "United States" not in gdps:
        return
    max_index = len(gdps["United States"]) - 1
    if max_index < 0:
        return
    if year_index < 0:
        year_index = 0
    if year_index > max_index:
        year_index = max_index
    current_year_index = year_index
    gdp_max = max(gdp[year_index] for gdp in gdps.values())
    if log_scale:
        gdp_max = math.log1p(gdp_max)
    for name, country in countries.items():
        gdp = gdps[name][year_index]
        if log_scale:
            gdp = math.log1p(gdp)
        ratio = (gdp / gdp_max) if gdp_max else 0
        col = add_hsv(color.red, (ratio * 340, 0, 0))
        country.color = col
    apply_legend_values(year_index, log_scale=log_scale)

def input(key: str) -> None:
    global left_mouse_pressed, mouse_position, camera_distance, selected_country, unselected_country
    if key == "left mouse down":
        mouse_position = mouse.position
        left_mouse_pressed = True
        mouse_hovered_entity = mouse.hovered_entity
        if mouse_hovered_entity and mouse_hovered_entity.name in countries:
            if mouse_hovered_entity in selected_countries:
                unselected_country = mouse_hovered_entity
                selected_countries.remove(unselected_country)
            else:
                selected_country = mouse_hovered_entity
                selected_countries.append(selected_country)

    elif key == "left mouse up":
        left_mouse_pressed = False
    if key == "scroll up":
        camera_distance = max(camera_distance - camera_zoom_speed, 0)
    elif key == "scroll down":
        camera_distance += camera_zoom_speed

camera.position = Vec3(spherical_to_cartesian(camera_distance, camera_phi, camera_theta))
camera.look_at(globe.position)

def update() -> None:
    global mouse_position, camera_phi, camera_theta, gui, hovered_country, hovered_country_name, hovered_country_info_text, similarity_scores, similarity_signature, selected_country, unselected_country
    if left_mouse_pressed:
        mouse_delta = mouse.position - mouse_position
        mouse_position = mouse.position
        rotate_speed = camera_rotate_speed * (camera_distance - 0.5)
        camera_phi = camera_phi - mouse_delta.x * rotate_speed
        camera_theta = clamp(camera_theta + mouse_delta.y * rotate_speed, .01, math.pi - .01)
    camera.position = Vec3(spherical_to_cartesian(camera_distance, camera_phi, camera_theta))
    camera.animate("rotation_z", 0, duration=.2, curve=curve.in_sine)
    camera.look_at(globe.position)

    if hovered_country and hovered_country.name in countries and hovered_country not in selected_countries:
        hovered_country.alpha = .6
        hovered_country.scale = .02
    hovered_country = mouse.hovered_entity
    if hovered_country and hovered_country not in selected_countries and hovered_country.name in countries:
        info_text = get_country_gdp_info_text(hovered_country.name)
        if hovered_country_name != hovered_country.name:
            gui = display_country_info(gui, hovered_country.name, info_text)
            hovered_country_name = hovered_country.name
            hovered_country_info_text = info_text
        elif gui is None:
            gui = display_country_info(gui, hovered_country.name, info_text)
            hovered_country_info_text = info_text
        elif hovered_country_info_text != info_text:
            gui = display_country_info(gui, hovered_country.name, info_text)
            hovered_country_info_text = info_text
        hovered_country.alpha = .8
        hovered_country.scale = .025
    if not hovered_country or hovered_country.name not in countries:
        if gui is not None:
            gui.disable()
        hovered_country_name = None
        hovered_country_info_text = None
    if selected_country:
        selected_country.alpha = 1.
        selected_country.scale = .03
        selected_country = None
    elif unselected_country:
        unselected_country.alpha = .6
        unselected_country.scale = .02
        unselected_country = None

    selected_names = sorted(country.name for country in selected_countries)
    next_signature = tuple(selected_names)
    if next_signature != similarity_signature:
        similarity_signature = next_signature
        if selected_names:
            similarity_scores = compute_group_similarity(selected_names)
        else:
            similarity_scores = {}
        hovered_country_info_text = None

    if not selected_countries:
        unselect_all_button.disable()
    else:
        unselect_all_button.enable()

    if unselect_all_button.hovered:
        unselect_all_button.color = unselect_all_button_hover_color
    else:
        unselect_all_button.color = unselect_all_button_base_color
    if log_scale_button.hovered:
        log_scale_button.color = log_scale_button_hover_color
    else:
        log_scale_button.color = log_scale_button_base_color

    year_index = int(year_slider.value) - year_base
    if year_index != current_year_index:
        apply_year_colors(year_index, log_scale=use_log_scale)

draw_boundaries(globe, radius=0.501, col=add_hsv(color.green, (0, -.8, 0)))
draw_centroids(globe, radius=0.501, col=add_hsv(color.red, (0, 0, -.1)), alpha=.4, size=.02)
get_gdp_data()
apply_year_colors(int(year_slider.value) - year_base, log_scale=use_log_scale)
for _, country in countries.items():
    country.alpha = .6

app.run()