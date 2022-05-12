import requests


def getUUIDFromUsername(username):
	try: return requests.get(f'https://api.mojang.com/users/profiles/minecraft/{username}').json()['id']
	except: return ""

def getUsernameFromUUID(uuid):
	res = requests.get(f'https://api.mojang.com/user/profiles/{uuid}/names').json()
	return res[len(res)-1]['name']
