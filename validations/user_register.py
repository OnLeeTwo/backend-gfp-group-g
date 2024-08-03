user_register_schema = {
    "email": {
        "type": "string",
        "required": True,
        "regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    },
    "password": {"type": "string", "minlength": 6, "maxlength": 64, "required": True},
    "role": {"type": "string", "required": True, "allowed": ["buyer", "seller"]},
}

user_register_schema = {
    "email": {
        "type": "string",
        "required": True,
        "regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    },
    "password": {"type": "string", "minlength": 6, "maxlength": 64, "required": True},
    "role": {"type": "string", "required": True, "allowed": ["buyer", "seller"]},
}