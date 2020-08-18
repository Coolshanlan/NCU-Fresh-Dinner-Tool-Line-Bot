from imgurpython import ImgurClient
client_id = ''
client_secret = ''
access_token = ''
refresh_token = ''


def getauthorize():

    client = ImgurClient(client_id, client_secret)

    authorization_url = client.get_auth_url('pin')

    print("Go to the following URL: {0}".format(authorization_url))

    pin = input("Enter pin code: ")

    credentials = client.authorize(pin, 'pin')
    client.set_user_auth(
        credentials['access_token'], credentials['refresh_token'])

    print("Authentication successful! Here are the details:")
    print("   Access token:  {0}".format(credentials['access_token']))
    print("   Refresh token: {0}".format(credentials['refresh_token']))
    return client


def setauthorize():
    return ImgurClient(client_id, client_secret, access_token, refresh_token)


def upload(client, path, config):
    image = client.upload_from_path(
        path, config=config, anon=False)
    return image


# config = {
#     'name': 'testupload',
#     'title': 'test-title',
#     'description': 'test-description'
# }
# client = setauthorize()
# image_id = upload(client
#     , "dataset/attractive-asian-nurse-smile-260nw-1207959016.jpg",config)
# print(image_id)
