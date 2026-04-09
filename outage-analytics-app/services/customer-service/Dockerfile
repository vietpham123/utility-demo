FROM ruby:3.2-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY Gemfile .
RUN bundle install
COPY . .
EXPOSE 4567
CMD ["ruby", "app.rb"]
