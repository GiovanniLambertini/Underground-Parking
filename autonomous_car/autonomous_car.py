import requests

BASE_API = "http://127.0.0.1/"
API_BOOKING = BASE_API + "booking"
API_ENTER = BASE_API + "enter"
API_EXIT = BASE_API + "exit"
LOCATION_ID = 1
USER_ID = 3

if __name__ == '__main__':
    #Booking
    input("Press Enter to book a slot...")
    body = requests.post(API_BOOKING, json={"type": "car", "locationId": str(LOCATION_ID), "userId": str(USER_ID)})

    if body.status_code == 200:
        if (body.json()['successful'] == True):
            print ("You have successfully booked a slot, you have to arrive within 1 hour")
        else:
            print("Full parking, try with another park or try again later")
            exit(1)

    else:
        print("Error " + str(body.status_code))
        exit(1)

    # Entering
    input("Press Enter when you are in front of the barrier ...")
    body = requests.post(API_ENTER, json={"type": "car", "locationId": str(LOCATION_ID), "userId": str(USER_ID)})

    if body.status_code == 200:
        response = body.json()
        if (response['successful'] == True):
            print("Opening barrier...")
            print ("Nearest slot is: ") + str(response['slot'])

        else:
            print("Full parking, try with another park or try again later")
            exit(1)
    elif body.status_code == 401:
        print ("Error, no valid reservation found for this user")
        exit(1)
    else:
        print("Error " + str(body.status_code))
        exit(1)

    # Exit
    input("Press Enter when you are in front of the barrier ...")
    body = requests.post(API_EXIT, json={"type": "car", "locationId": str(LOCATION_ID), "userId": str(USER_ID)})

    if body.status_code == 200:
        response = body.json();
        if (response['successful'] == True):
            print("Opening barrier...")
            print("You have paid: " + str(response['price']) + " euros")

        else:
            print("Error, try again")
            exit(1)
    elif body.status_code == 401:
        print("Error, no valid reservation found for this user")
        exit(1)
    else:
        print("Error " + str(body.status_code))
        exit(1)