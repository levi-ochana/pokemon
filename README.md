בכדי להריץ את קובץ הדיפלוימנט בסביבת AWS יש לוודא ש AWS CLI מותקן ושקובץ הcredentials מעודכן
ניתן להתקין בUbuntu - 
sudo apt update
sudo apt upgrade
sudo apt install python3-pip
pip3 install awscli --upgrade --user
ולעדכן בUbuntu -
gedit  ~/.aws/credentials


בכדי להריץ את האפליקציה לאחר הפריסה -
.לנוות לתיקיה pokemon_app ולהפעיל python3 pocemon




Explanation:
The code implements a simple game where the user can choose to "draw" a random Pokémon from a list retrieved from the PokeAPI. The game also checks if the Pokémon already exists in a locally saved JSON file, and if not, it adds the Pokémon to the file.

Key Functions:
check_response_status: This function receives the HTTP response, checks if the status is 200 (OK), and returns the JSON content if everything is fine. If not, it prints an error message and returns None.

fetch_pokemon_list: This function fetches a list of Pokémon from the API based on the limit and a random starting point (offset). It uses the PokeAPI to return a list of up to 5 Pokémon from the available pool.

fetch_pokemon_details: This function takes the URL of a Pokémon from the list retrieved from the API and fetches that Pokémon's details (name, height, weight). It checks the response before returning the data.

check_pokemon_in_file: This function checks if the Pokémon already exists in a local JSON file called pokemon_data.json. If the file doesn’t exist, it treats this as if no Pokémon have been saved. If the Pokémon exists, it returns the Pokémon’s details.

save_pokemon_to_file: This function saves the Pokémon's details to the local JSON file. If the file already exists, it appends the new Pokémon to the existing list. If not, it creates a new file and saves the first Pokémon.

print_pokemon_details: This function prints the Pokémon's name, height, and weight in a clear format for the user.

main: This is the main function that runs the game. It asks the user if they want to "draw" a new Pokémon. If the user selects "Y", it fetches data from the API, displays the names of the retrieved Pokémon, and randomly picks one for checking. If the Pokémon already exists in the file, it will display the details. If not, it will save the new Pokémon to the file.

Additional Note:
This code uses an external API (PokeAPI) to fetch Pokémon lists and saves data in a local JSON file. The game gives the user the option to add new Pokémon data to the existing file if they haven’t been saved before.


