from dotenv import dotenv_values

backend_config = {**dotenv_values(".env.shared")}
