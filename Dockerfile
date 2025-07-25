# --- Optimised Layer Caching --- #
# Layer 1 (ffmpeg) will never regenerate
# Layer 2 (pip install) will regenerate if pyproject.toml is changed
# Layer 3 (build & install tiddl), rengerates on any code change

FROM python:alpine
WORKDIR /root

# -- Layer 1 - ffmpeg install (it'll stay cached as a layer always) --
RUN apk add --no-cache ffmpeg

# -- Layer 2 - pip install depenencies (remains cached unless pyproject.toml changes) --
# Exports 'depenencies' from pyproject.toml formatted to requirements.txt format, pipelined to pip install
COPY pyproject.toml .
RUN python -c "import tomllib; f=open('pyproject.toml','rb'); print('\n'.join(tomllib.load(f)['project']['dependencies']))" | xargs pip install 

# -- Layer 3 - Uncached layer (regenerates anytime a new build is released) --
COPY . .
RUN pip install --no-deps .
RUN rm -rf *
