FROM gradle:8.5-jdk17-alpine AS build
WORKDIR /app
COPY build.gradle.kts settings.gradle.kts ./
COPY src/ src/
RUN gradle shadowJar --no-daemon

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/build/libs/*-all.jar app.jar
EXPOSE 8090
CMD ["java", "-Xmx256m", "-Xms128m", "-jar", "app.jar"]
