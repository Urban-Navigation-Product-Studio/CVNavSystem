import requests
import time
import os
from typing import List, Tuple, Dict, Optional
from math import sin, atan2, cos, sqrt, radians, degrees
import pandas as pd
import motion
import location

class GPS_Navigator:
    """
    A class that provides GPS navigation functionalities, including fetching directions, 
    calculating distances, and providing turn-by-turn instructions using the Google Directions API.
    Meant to be used on phone using the Pythonista app: https://www.omz-software.com/pythonista/#:~:text=Pythonista%20is%20a%20complete%20development%20environment
    """

    def __init__(self, directions_api_key: str, destination: str, eps: int = 3, update_time: int = 10):
        """
        Initializes the GPS_Navigator with the required API key and configuration options.

        Args:
            directions_api_key (str): API key for the Google Directions API.
            destination (str): The address of the user's destination.
            eps (int): Tolerance for reaching a step in meters. Defaults to 3.
            update_time (int): Time interval in seconds for updating location and heading. Defaults to 10.
        """
        self.directions_api_key = directions_api_key
        self.eps = eps
        self.update_time = update_time
        self.destination = destination

        self.cardinal_directions = {
            "north": 0,
            "northeast": 45,
            "east": 90,
            "southeast": 135,
            "south": 180,
            "southwest": 225,
            "west": 270,
            "northwest": 315,
        }

    def get_directions(self, origin: Tuple[float, float], destination: str) -> Optional[List[Dict]]:
        """
        Fetches walking directions from the Google Directions API.

        Args:
            origin Tuple[float, float]: The starting point's coordinates with (latitude, longitude)
            destination (str): The destination address as a string.

        Returns:
            Optional[List[Dict]]: A list of steps in the directions or None if an error occurs.
        """
        base_url = "https://maps.googleapis.com/maps/api/directions/json"

        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": destination,
            "mode": "walking",
            "key": self.directions_api_key,
        }

        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK":
                route = data["routes"][0]
                steps = self.convert_to_turn_directions(route["legs"][0]["steps"])

                for index in range(len(steps)):
                    steps[index]["start_location"] = (steps[index]["start_location"]["lat"], 
                                                      steps[index]["start_location"]["lng"])
                    
                    steps[index]["end_location"] = (steps[index]["end_location"]["lat"],
                                                     steps[index]["end_location"]["lng"])
            else:
                print(f"Error: {data['status']}")
                return None
        else:
            print(f"Error: HTTP {response.status_code}")
            return None

    def get_current_heading(self) -> float:
        """
        Retrieves the device's current heading using the device's motion sensors.

        Returns:
            float: The heading in degrees (0 to 360).
        """
        motion.start_updates()
        time.sleep(1)
        attitude = motion.get_attitude()
        yaw = attitude[2]
        heading_degrees = (degrees(yaw) + 360) % 360
        motion.stop_updates()

        return heading_degrees

    def get_turn_direction(self, current_heading: float, target_cardinal_direction: str) -> str:
        """
        Determines whether the user should turn left or right to align with a target cardinal direction.

        Args:
            current_heading (float): The user's current heading in degrees.
            target_cardinal_direction (str): The target cardinal direction (e.g., "north", "east").

        Returns:
            str: 'left' if the user should turn left, 'right' if the user should turn right.
        """
        target_heading = self.cardinal_directions[target_cardinal_direction]
        angle_diff = (target_heading - current_heading + 360) % 360

        if angle_diff < 180:
            return "right"
        else:
            return "left"

    def convert_to_turn_directions(self, steps: List[Dict]) -> List[Dict]:
        """
        Converts cardinal direction instructions into 'left' or 'right' turn instructions.

        Args:
            steps (List[Dict]): A list of steps in the route.

        Returns:
            List[Dict]: The list of steps with updated turn instructions.
        """
        current_heading = self.get_current_heading()

        for index in range(len(steps)):
            for cardinal_dir in ["northeast", "northwest", "southeast", "southwest", "east", "west", "north", "south"]:
                if cardinal_dir in steps[index]["html_instructions"]:
                    steps[index]["html_instructions"] = steps[index]["html_instructions"].replace(
                        cardinal_dir, self.get_turn_direction(current_heading, cardinal_dir))

        return steps

    def get_current_location(self) -> Tuple[float, float]:
        """
        Retrieves the current geographic location using the device's location service.

        Returns:
            Tuple[float, float]: The current location as a tuple with latitude and longitude.
        """
        location.start_updates()
        current_loc = location.get_location()
        location.stop_updates()
        current_loc = (current_loc["latitude"], current_loc["longitude"])
        return current_loc

    def geodesic_distance(self, coord_1: Tuple[float, float], coord_2: Tuple[float, float]) -> float:
        """
        Calculates the geodesic distance between two coordinates using the Haversine formula.

        Args:
            coord_1 (Tuple[float, float]): The first coordinate as (latitude, longitude).
            coord_2 (Tuple[float, float]): The second coordinate as (latitude, longitude).

        Returns:
            float: The distance between the two coordinates in meters.
        """
        R = 6373.0 * 1e3  # Radius of Earth in meters
        coord_1 = (radians(coord_1[0]), radians(coord_1[1]))
        coord_2 = (radians(coord_2[0]), radians(coord_2[1]))

        dlon = coord_2[1] - coord_1[1]
        dlat = coord_2[0] - coord_1[0]

        a = sin(dlat / 2)**2 + cos(coord_1[0]) * cos(coord_2[0]) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c
        return distance

    def clear_screen(self) -> None:
        """
        Clears the console screen, depending on the operating system.
        """
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

    def display_steps(self, steps: List[Dict]) -> None:
        """
        Displays the navigation steps in a formatted table using pandas.

        Args:
            steps (List[Dict]): A list of steps in the route.
        """
        self.clear_screen()
        print("\t\t\tRoute Directions\n" + "="*65)

        dataframe = {}

        for col, header_name in zip(["html_instructions", "distance"], ["Instructions", "Distance"]):
            values = []
            for step in steps:
                if col == "distance":
                    values.append(step[col]["text"])
                else:
                    values.append(step[col])
            dataframe[header_name] = values

        df = pd.DataFrame(dataframe)
        pd.set_option('display.colheader_justify', 'center')
        pd.set_option('display.expand_frame_repr', False)

        print(df)

    def __call__(self) -> None:
        """
        The main function that fetches directions, displays steps, and periodically updates
        the user on their current progress. If the user deviates, the directions are recalculated.
        """
        current_location = self.get_current_location()

        steps = self.get_directions(current_location, self.destination)

        if steps is None:
            return

        self.display_steps(steps)

        step_idx = 0
        prev_distance = self.geodesic_distance(current_location, steps[0]["end_location"])

        while step_idx < len(steps):
            current_location = self.get_current_location()
            distance = self.geodesic_distance(current_location, steps[0]["end_location"])

            if distance < self.eps:
                step_idx += 1
                if step_idx < len(steps):
                    print(f"\nCurrent step: {steps[step_idx]['html_instructions']} ({steps[step_idx]['distance']['text']})")
            elif distance > prev_distance:
                print("You are off route! Recalculating directions...")
                steps = self.get_directions(current_location, self.destination)

                if steps is None:
                    return
                
                self.display_steps(steps)
                step_idx = 0

                prev_distance = self.geodesic_distance(current_location, steps[0]["end_location"])

            prev_distance = distance
            time.sleep(self.update_time)


if __name__ == "__main__":
    api_key = "AIzaSyBVHNEeznNak430vKjbJZuTJv5rIDsZtic"
    destination = "11814 Hillside Ave, Richmond Hill, NY 11418"
    navigator = GPS_Navigator(directions_api_key=api_key,
                               eps=3, 
                               update_time=10, 
                               destination=destination)
    navigator()
