
GENERIC_TEST = "\\registry\\user\\software\\surreal"
USER_TEST = "\\registry\\user\\s102-54306-4360-2-63299\\software\\surreal"


def anonymize_key_path(key_path):
	if key_path.startswith("\\registry\\user\\"):
		# Split off the prefix
		working_path = key_path.split("\\registry\\user\\",1)[-1]
		path_after_sid = working_path[working_path.find("\\")+1:]
		return "\\registry\\user\\" + path_after_sid
	return key_path
	
	
print(anonymize_key_path(USER_TEST))