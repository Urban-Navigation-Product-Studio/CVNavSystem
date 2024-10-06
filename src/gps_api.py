"""
    A limited version of the gps api meant to work on laptop.
"""
import requests
from geopy.distance import geodesic
import time
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from dotenv import load_dotenv
import os
from typing import List, Tuple, Dict, Optional

console = Console()


def get_directions(
    api_key: str, origin: Dict[str, float], destination: str
) -> Optional[List[Dict]]:
    """
    Fetch directions from the Google Directions API.

    Args:
        api_key (str): The API key for accessing the Google Directions API.
        origin (Dict[str, float]): The origin coordinates as a dictionary with 'lat' and 'lng'.
        destination (str): The destination address as a string.

    Returns:
        List[Dict]: A list of steps in the directions, or None if an error occurs.
    """
    base_url = "https://maps.googleapis.com/maps/api/directions/json"

    params = {
        "origin": f"{origin['lat']},{origin['lng']}",
        "destination": destination,
        "mode": "walking",
        "key": api_key,
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()

        if data["status"] == "OK":
            route = data["routes"][0]
            return route["legs"][0]["steps"]
        else:
            console.print(f"Error: {data['status']}")
            return None
    else:
        console.print(f"Error: HTTP {response.status_code}")
        return None


def get_current_location() -> Dict[str, float]:
    """
    Get the current geographic location using an IP-based geolocation service.

    Returns:
        Dict[str, float]: The current location as a dictionary with 'lat' and 'lng'.
    """
    response = requests.get("https://ipinfo.io")
    data = response.json()
    location = data["loc"]

    latitude, longitude = map(float, location.split(","))

    return {"lat": latitude, "lng": longitude}


def get_closest_step(
    current_location: Dict[str, float], steps: List[Dict]
) -> Tuple[Dict, float]:
    """
    Find the closest step in the route to the user's current location.

    Args:
        current_location (Dict[str, float]): The current location as a dictionary with 'lat' and 'lng'.
        steps (List[Dict]): A list of steps in the route.

    Returns:
        Tuple[Dict, float]: The closest step and the distance to it in meters.
    """
    closest_step = None
    min_distance = float("inf")

    for step in steps:
        step_location = step["end_location"]
        step_coords = (step_location["lat"], step_location["lng"])
        user_coords = (current_location["lat"], current_location["lng"])

        distance = geodesic(step_coords, user_coords).meters
        if distance < min_distance:
            min_distance = distance
            closest_step = step
    return closest_step, min_distance


def display_steps(steps: List[Dict]) -> None:
    """
    Display the route steps in a table format using rich.

    Args:
        steps (List[Dict]): A list of steps in the route.
    """
    table = Table(title="Route Directions")

    table.add_column("Step", justify="right", style="cyan", no_wrap=True)
    table.add_column("Instruction", style="magenta")
    table.add_column("Distance", justify="right", style="green")

    for i, step in enumerate(steps):
        instruction = step["html_instructions"]
        distance = step["distance"]["text"]
        table.add_row(str(i + 1), instruction, distance)

    console.print(table)


def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def main() -> None:
    """
    Main function to fetch directions, display steps, and update the user on their current progress
    while following the route. If the user deviates, directions are recalculated.
    """
    env_path = os.path.join(".env")
    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("GOOGLE_DIRECTIONS_API_KEY")

    if not api_key:
        console.print(
            "[bold red]API key not found! Please check your .env file.[/bold red]"
        )
        return

    origin = get_current_location()
    destination = "11814 Hillside Ave, Richmond Hill, NY 11418"

    steps = get_directions(api_key, origin, destination)

    if steps is None:
        return

    clear_screen()
    console.print("[bold blue]Route directions:[/bold blue]")
    display_steps(steps)

    with Progress() as progress:
        task = progress.add_task("[yellow]Moving along route...", total=len(steps))

        closest_step = steps[0]
        console.print(
            f"\n[bold green]Current step:[/bold green] {closest_step['html_instructions']} ({closest_step['distance']['text']})"
        )

        step_idx = 0
        prev_step = closest_step

        while step_idx <= len(steps):
            current_location = get_current_location()

            closest_step, distance = get_closest_step(current_location, steps)

            if distance < 50:
                if prev_step.get("html_instructions") != closest_step.get(
                    "html_instructions"
                ):
                    prev_step = closest_step
                    console.print(
                        f"\n[bold green]Current step:[/bold green] {closest_step['html_instructions']} ({closest_step['distance']['text']})"
                    )
                    step_idx += 1
                    progress.update(task, advance=1)

            else:
                console.print(
                    "[bold red]You are off route! Recalculating directions...[/bold red]"
                )
                steps = get_directions(api_key, current_location, destination)

                if steps is not None:
                    clear_screen()

                    progress.reset(task, total=len(steps))
                    progress.update(task, completed=0)
                    prev_step = closest_step
                    display_steps(steps)
                    step_idx = 0

            time.sleep(10)


if __name__ == "__main__":
    main()
