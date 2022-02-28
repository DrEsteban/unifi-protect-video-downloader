FROM python:3 AS build

RUN mkdir /build
WORKDIR /build

RUN pip install -U poetry

COPY . /build/

RUN poetry build -f wheel --no-ansi --no-interaction


FROM python:3.8-slim AS base

RUN mkdir /install

WORKDIR /install

COPY --from=build /build/dist/*.whl /install/

RUN pip install *.whl

ENTRYPOINT [ "protect-archiver" ]
CMD [ "--help" ]

VOLUME [ "/downloads" ]
