FROM elixir:1.16-alpine AS build
RUN apk add --no-cache build-base
WORKDIR /app
COPY mix.exs mix.lock ./
ENV MIX_ENV=prod
RUN mix local.hex --force && mix local.rebar --force && mix deps.get && mix deps.compile
COPY lib/ lib/
RUN mix compile && mix release

FROM alpine:3.19
RUN apk add --no-cache libstdc++ openssl ncurses-libs
WORKDIR /app
COPY --from=build /app/_build/prod/rel/work_order_service/ .
EXPOSE 4000
CMD ["bin/work_order_service", "start"]
