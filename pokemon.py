import requests
import json
import random


def get_pokemon_list(limit=5):
    url = f"https://pokeapi.co/api/v2/pokemon?limit={limit}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        print(f"Error getting data: {response.status_code}")
        return None


def get_pokemon_details(pokemon_list, file_path="pokemon_data.json"):
    full_data = []

    for pokemon in pokemon_list:
        pokemon_url = pokemon['url']
        pokemon_response = requests.get(pokemon_url)

        if pokemon_response.status_code == 200:
            pokemon_data = pokemon_response.json()
            selected_data = {
                "name": pokemon_data['name'],
                "height": pokemon_data['height'],
                "weight": pokemon_data['weight']
            }
            full_data.append(selected_data)
        else:
            print(f"Error getting data: {pokemon['name']}")

    # Save the data to a JSON file
    with open(file_path, 'w') as json_file:
        json.dump(full_data, json_file, indent=2)

    return full_data


def get_random_pokemon_name():
    pokemon_id = random.randint(1, 1010)
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    response = requests.get(url)

    if response.status_code == 200:
        pokemon_data = response.json()
        return {
            "name": pokemon_data['name'],
            "height": pokemon_data['height'],
            "weight": pokemon_data['weight']
        }
    else:
        print(f"Error getting data: {response.status_code}")
        return None


def check_pokemon_in_file(pokemon_name, file_path="pokemon_data.json"):
    try:
        with open(file_path, 'r') as file:
            pokemon_data = json.load(file)
            for pokemon in pokemon_data:
                if pokemon['name'] == pokemon_name:
                    return True, pokemon
            return False, None
    except FileNotFoundError:
        print(f"File not found, please run the game first to create it.")
        return False, None


def save_pokemon_to_file(pokemon_details, file_path="pokemon_data.json"):
    try:
        with open(file_path, 'r+') as file:
            pokemon_data = json.load(file)
            pokemon_data.append(pokemon_details)
            file.seek(0)
            json.dump(pokemon_data, file, indent=2)
    except FileNotFoundError:
        with open(file_path, 'w') as file:
            json.dump([pokemon_details], file, indent=2)


def main():
    print("Welcome to the Pokémon game!")
    while True:
        user_input = input("Do you want to draw a Pokémon? Y/N: ").strip().upper()
        if user_input == "Y":
            print("Game start!")
            pokemon_list = get_pokemon_list(limit=5)
            if pokemon_list is not None:
                pokemon_details = get_pokemon_details(pokemon_list)
                for pokemon in pokemon_details:
                    save_pokemon_to_file(pokemon)

                random_pokemon = get_random_pokemon_name()
                if random_pokemon:
                    pokemon_name = random_pokemon['name']
                    exists, _ = check_pokemon_in_file(pokemon_name)
                    if exists:
                        print(f"{pokemon_name} already exists in the file.")
                    else:
                        save_pokemon_to_file(random_pokemon)

            continue
        elif user_input == "N":
            print("Goodbye!")
            break
        else:
            print("Invalid answer, please enter Y/N.")


if __name__ == "__main__":
    main()
