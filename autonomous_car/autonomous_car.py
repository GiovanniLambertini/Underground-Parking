import requests

BASE_API = "http://127.0.0.1/"
API_BOOKING = BASE_API + "booking"
API_ENTER = BASE_API + "enter"
API_EXIT = BASE_API + "exit"
LOCATION_ID = 1
USER_ID = 1

if __name__ == '__main__':
    #Booking
    input("Press Enter to book a slot...")
    body = requests.post(API_BOOKING, json={"type": "car", "locationId": str(LOCATION_ID), "userId": str(USER_ID)})

    if body.status_code == 200:
        if (body.json()['successful'] == True):
            print ("You have successfully booked a slot, you have to arrive within 1 hour")
        else:
            print("Full parking, try with another park or try again later")

    else:
        print("Error " + str(body.status_code))

    # Entering
    input("Press Enter when you are in front of the barrier ...")
    body = requests.post(API_ENTER, json={"type": "car", "locationId": str(LOCATION_ID), "userId": str(USER_ID)})

    if body.status_code == 200:
        if (body.json()['successful'] == True):
            print("Opening barrier...")

        else:
            print("Full parking, try with another park or try again later")
    elif body.status_code == 401:
        print ("Error, no valid reservation found for this user")
    else:
        print("Error " + str(body.status_code))

    # Exit
    input("Press Enter when you are in front of the barrier ...")
    body = requests.post(API_EXIT, json={"type": "car", "locationId": str(LOCATION_ID), "userId": str(USER_ID)})

    if body.status_code == 200:
        response = body.json();
        if (response['successful'] == True):
            print("Opening barrier...")
            print("You have paid: " + str(response['total_price']) + " euros")

        else:
            print("Error, try again")
    elif body.status_code == 401:
        print("Error, no valid reservation found for this user")
    else:
        print("Error " + str(body.status_code))