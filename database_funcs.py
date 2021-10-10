import pymongo


def find_suitable(collection, elements: dict):
    """ Function to retrieve suitable performer from a provided
    Collection using a dictionary containing chosen requirements.
    """
    results = collection.find(elements)
    return [r for r in results]


def pet_places_collection():
    """Function to connect with Petplaces DB and get """
    # Creating the client
    client = pymongo.MongoClient('mongodb+srv://fl4kee:zWTHDG8j8rA6RfB4'
                                 '@cluster0.egogm.mongodb.net/myFirstDa'
                                 'tabase?retryWrites=true&w=majority')
    # Connecting to our database
    db = client['myFirstDatabase']
    # Returning our collection
    return db.petplaces


def get_categories():
    categories = []
    for performer in find_suitable(pet_places_collection(), {}):
        for key, value in performer.items():
            if key == 'category':
                categories.append(value)
    return list(set(categories))


def get_locations():
    locations = []
    for performer in find_suitable(pet_places_collection(), {}):
        for key, value in performer.items():
            if key == 'location':
                locations.append(value)
    return list(set(locations))


def get_location_triplets(locations):
    location_triplets = []
    for i in range(len(locations)//3):
        triplet = [[locations[3*i+pos]] for pos in range(3)]
        location_triplets.append(triplet)
    if len(locations) % 3 != 0:
        last_non_triplet = []
        for i in range((len(locations) % 3)):
            last_non_triplet.append([locations[-(i+1)]])
        location_triplets.append(last_non_triplet)

    return location_triplets


for i in find_suitable(pet_places_collection(), {}):
    print(i)
