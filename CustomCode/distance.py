from math import sin, cos, sqrt, atan2, radians

def distance(c_lon, c_lat, o_lon, o_lat):
    R = 6373.0   #radius of the Earth

    client_lon = radians(c_lon)  #coordinates

    other_lon = radians(o_lon)
    client_lat = radians(c_lat)
    other_lat = radians(o_lat)

# c_lon = math.radians(52.2296756)  #coordinates

# lon1 = math.radians(21.0122287)
# lat2 = math.radians(52.406374)
# lon2 = math.radians(16.9251681)

    dlon = other_lon - client_lon #change in coordinates

    dlat = other_lat - client_lat

    a = sin(dlat / 2)**2 + cos(client_lat) * cos(other_lat) * sin(dlon / 2)**2 #Haversine formula

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance
    # print(distance)