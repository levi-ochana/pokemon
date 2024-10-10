import requests
import json
import random

# Function to check the status of the response
def check_response_status(response):
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting data: {response.status_code}")
        return None

# Function to fetch a list of Pokémon
def fetch_pokemon_list(limit=5):
    offset = random.randint(0, 1010 - limit)  # Random starting point
    url = f"https://pokeapi.co/api/v2/pokemon?limit={limit}&offset={offset}"
    response = requests.get(url)
    data = check_response_status(response)
    return data.get('results', []) if data else None

# Function to fetch Pokémon details by URL
def fetch_pokemon_details(pokemon_url):
    response = requests.get(pokemon_url)
    data = check_response_status(response)
    if data:
        return {
            "name": data['name'],
            "height": data['height'],
            "weight": data['weight']
        }
    return None

# Function to check if a Pokémon exists in the JSON file
def check_pokemon_in_file(pokemon_name, file_path="pokemon_data.json"):
    try:
        with open(file_path, 'r') as file:
            pokemon_data = json.load(file)
            for pokemon in pokemon_data:
                if pokemon['name'] == pokemon_name:
                    return True, pokemon  # Pokémon found
            return False, None  # Pokémon not found
    except FileNotFoundError:
        return False, None  # File not found, treat as if no Pokémon exist

# Function to save Pokémon details to a JSON file
def save_pokemon_to_file(pokemon_details, file_path="pokemon_data.json"):
    try:
        with open(file_path, 'r+') as file:
            pokemon_data = json.load(file)
            pokemon_data.append(pokemon_details)  # Append new Pokémon details
            file.seek(0)  # Move cursor back to the start of the file
            json.dump(pokemon_data, file, indent=2)
    except FileNotFoundError:
        with open(file_path, 'w') as file:
            json.dump([pokemon_details], file, indent=2)  # Create a new file

# Function to print Pokémon details
def print_pokemon_details(pokemon):
    print(f"Name: {pokemon['name']}, Height: {pokemon['height']}, Weight: {pokemon['weight']}")

# Main function to run the game
def main():
    print("Welcome to the Pokémon game!")
    while True:
        user_input = input("\nDo you want to draw a Pokémon? Y/N: ").strip().upper()
        if user_input == "Y":
            print("Game start!")
            pokemon_list = fetch_pokemon_list(limit=5)  # Fetch a list of Pokémon
            if pokemon_list:
                # Fetch details for each Pokémon
                pokemon_details_list = [fetch_pokemon_details(pokemon['url']) for pokemon in pokemon_list if fetch_pokemon_details(pokemon['url'])]

                # Display fetched Pokémon names
                print("Pokémon names retrieved:")
                for pokemon in pokemon_details_list:
                    print(pokemon['name'])  # Display names

                # Choose a random Pokémon
                random_pokemon = random.choice(pokemon_details_list)  
                pokemon_name = random_pokemon['name']

                # Check if the random Pokémon already exists in the file
                exists, existing_pokemon = check_pokemon_in_file(pokemon_name)
                if exists:
                    print(f"\n{pokemon_name} already exists in the file.")
                    # Display existing Pokémon details
                    print_pokemon_details(existing_pokemon)
                else:
                    save_pokemon_to_file(random_pokemon)  # Save new Pokémon to the file
                    print(f"\nRandom Pokémon added:")
                    print_pokemon_details(random_pokemon)
            continue
        elif user_input == "N":
            print("Goodbye!")
            break
        else:
            print("Invalid answer, please enter Y/N.")

if __name__ == "__main__":
    main()
