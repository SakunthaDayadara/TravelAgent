from flask import Flask, render_template, request
import pandas as pd
import requests

app = Flask(__name__)

# Define your OpenAI API key
OPENAI_API_KEY = 'Define your OpenAI API key'

# Define your OpenAI endpoint
OPENAI_ENDPOINT = 'https://api.openai.com/v1/completions'


GOOGLE_PLACES_API_KEY = 'Define your API key'

# Load the dataset
data = pd.read_csv("DataSheet1.csv", skipinitialspace=True)

# Define function to calculate similarity
def calculate_similarity(last_visited, living_city, interests):
    # Filter cities based on district
    district_cities = data[data['District'] != living_city['District']]

    # Calculate similarity based on travel interests
    district_cities['Similarity'] = abs(district_cities['Historical'] - last_visited['Historical']) + \
                                    abs(district_cities['Adventure'] - last_visited['Adventure']) + \
                                    abs(district_cities['Nature'] - last_visited['Nature']) + \
                                    abs(district_cities['Joyful'] - last_visited['Joyful']) + \
                                    abs(district_cities['Beach'] - last_visited['Beach'])

    # Sort by similarity and return top 3 cities
    recommendations = district_cities.sort_values(by='Similarity').iloc[2:3]

    return recommendations[['City']]



def get_tourism_plan(city):
    prompt = f"Give me a 2 or 3 day travel plan in {city}?"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + OPENAI_API_KEY,
    }
    data = {
        'model': 'gpt-3.5-turbo-instruct',
        'prompt': prompt,
        'temperature': 0.5,
        'max_tokens': 1000,  # Adjust as needed
    }
    response = requests.post(OPENAI_ENDPOINT, headers=headers, json=data)
    #print("Response JSON:", response.json())
    choices = response.json()['choices']
    if choices:
        plan = choices[0]['text'].strip().split('\n')
        return plan
    else:
        print("Unexpected error:", response.text)
        return []


def get_hotels(city):
    places_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=hotels+in+{city}&key={GOOGLE_PLACES_API_KEY}"
    response = requests.get(places_url)
    data = response.json()
    return data['results']



@app.route('/', methods=['GET', 'POST'])
def index():
    recommended_cities_with_plan = {}
    if request.method == 'POST':
        # Get user input
        currently_living_district = request.form['currently_living_district']
        currently_living_city = request.form['currently_living_city']
        last_visited_district = request.form['last_visited_district']
        last_visited_city = request.form['last_visited_city']
        last_visited = data[data['City'] == last_visited_city].iloc[0]
        living_city = data[data['City'] == currently_living_city].iloc[0] 
        interests = [request.form.get(interest) for interest in ['Historical', 'Adventure', 'Nature', 'Joyful', 'Beach']]

        # Calculate recommendations
        recommendations = calculate_similarity(last_visited, living_city, interests)
        print(recommendations)

        #return render_template('result.html', recommendations=recommendations)
        for index, row in recommendations.iterrows():
            city = row['City']
            if city:
                plan = get_tourism_plan(city)
                hotels = get_hotels(city)
                recommended_cities_with_plan[city] = {'plan': plan, 'hotels': hotels}

        print(recommended_cities_with_plan)
        return render_template('recommendations.html', recommendations=recommended_cities_with_plan)
    else:
        districts = data['District'].unique()
        cities_by_district = data.groupby('District')['City'].apply(list).to_dict()
        return render_template('index.html', districts=districts, districts_to_cities=cities_by_district)

if __name__ == '__main__':
    app.run(debug=True)
