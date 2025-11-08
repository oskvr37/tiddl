from tiddl.core.api import TidalAPI, TidalClient

# we will utilize some functions from tiddl cli
# and use `APP_PATH` that is located at our /home_directory/.tiddl
from tiddl.cli.utils.auth import load_auth_data
from tiddl.cli.const import APP_PATH

# !! remember to be logged in, use `tiddl auth login`
# it will save auth token in /home_directory/.tiddl/auth.json

# in case your token expired, then use `tiddl auth refresh`

# load our token, country code and user id from file
auth_data = load_auth_data()

# we make sure auth_data is not empty = we are logged in

assert auth_data.token
assert auth_data.country_code
assert auth_data.user_id

# we create Client for our API.
# this is custom client that can cache requests
# to make the API more efficient

client = TidalClient(
    token=auth_data.token,
    cache_name=APP_PATH / "api_cache",  # path to cache api requests
    debug_path=APP_PATH / "api_debug",  # optional, used for debugging api
)

# this is our Tidal API that will call the endpoints

api = TidalAPI(
    client,
    country_code=auth_data.country_code,
    user_id=auth_data.user_id,
)

if __name__ == "__main__":
    # make the API call
    session = api.get_session()

    # every data from the api is `pydantic` model
    print(f"session id: {session.sessionId}")

    # see every available endpoint at `tiddl.core.api`
